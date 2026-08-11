#!/usr/bin/env python3
"""Parse and audit Figma-filled data declarations in Flutter contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from contract_core import ContractError, doc_sections


SCHEMA = "fr-mvvm-contract.figma-fill-data-report.v1"
ENTRY = re.compile(r"^-\s*\[([a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)+)\]\s*\|\s*(.+)$")
FIELD = re.compile(r"^([A-Za-z][A-Za-z ]*):\s*(.+)$")
NODE_ID = re.compile(r"^[A-Za-z0-9_-]+:[A-Za-z0-9_-]+$")
RENDER = re.compile(r"^([A-Z][A-Za-z0-9_]*Model)\.([a-z][A-Za-z0-9_]*)$")
TODO = re.compile(r"\bTODO\s*\(\s*figma-data\s*\)", re.IGNORECASE)
KINDS = {"remote", "local", "derived", "static-copy"}
BINDINGS = {"bound", "pending", "static"}


@dataclass(frozen=True)
class FigmaFillData:
    """One non-copy Figma value and its runtime ownership."""

    id: str
    node: str
    kind: str
    binding: str
    render: str | None
    source: str | None
    fixture: str | None


def _fields(raw: str, *, entry_id: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for fragment in raw.split("|"):
        match = FIELD.match(fragment.strip())
        if match is None:
            raise ContractError(
                f"Figma Data `{entry_id}` fields must use `Name: value`"
            )
        name, value = match.group(1).strip(), match.group(2).strip()
        if name in fields:
            raise ContractError(f"Figma Data `{entry_id}` repeats `{name}`")
        fields[name] = value
    return fields


def parse_figma_fill_data(sections: dict[str, list[str]]) -> tuple[FigmaFillData, ...]:
    """Return the structured `Figma Data` declarations from one contract."""

    lines = sections.get("Figma Data")
    if lines is None:
        return ()
    if lines == ["- none"]:
        return ()
    if len(lines) == 1 and ENTRY.match(lines[0]) is None and TODO.search(lines[0]):
        return ()
    if not lines:
        raise ContractError("Figma Data must declare entries or `- none`")

    entries: list[FigmaFillData] = []
    seen: set[str] = set()
    for line in lines:
        match = ENTRY.match(line)
        if match is None:
            raise ContractError(
                "Figma Data entries must use `- [stable.id] | Node: ... | "
                "Kind: ... | Binding: ...`"
            )
        entry_id, raw_fields = match.groups()
        if entry_id in seen:
            raise ContractError(f"Figma Data repeats `{entry_id}`")
        seen.add(entry_id)
        fields = _fields(raw_fields, entry_id=entry_id)
        unknown = set(fields).difference(
            {"Node", "Kind", "Binding", "Render", "Source", "Fixture"}
        )
        if unknown:
            raise ContractError(
                f"Figma Data `{entry_id}` has unsupported fields: "
                + ", ".join(sorted(unknown))
            )
        for required in ("Node", "Kind", "Binding"):
            if required not in fields:
                raise ContractError(f"Figma Data `{entry_id}` requires `{required}`")
        if not NODE_ID.fullmatch(fields["Node"]):
            raise ContractError(
                f"Figma Data `{entry_id}` Node must be one Figma node id"
            )
        if fields["Kind"] not in KINDS:
            raise ContractError(
                f"Figma Data `{entry_id}` Kind must be one of: "
                + ", ".join(sorted(KINDS))
            )
        if fields["Binding"] not in BINDINGS:
            raise ContractError(
                f"Figma Data `{entry_id}` Binding must be one of: "
                + ", ".join(sorted(BINDINGS))
            )

        binding = fields["Binding"]
        render = fields.get("Render")
        source = fields.get("Source")
        fixture = fields.get("Fixture")
        if binding in {"bound", "pending"}:
            for required, value in (
                ("Render", render),
                ("Source", source),
                ("Fixture", fixture),
            ):
                if not value:
                    raise ContractError(
                        f"Figma Data `{entry_id}` with Binding `{binding}` "
                        f"requires `{required}`"
                    )
            if render is None or RENDER.fullmatch(render) is None:
                raise ContractError(
                    f"Figma Data `{entry_id}` Render must be `XxxModel.field`"
                )
        if binding == "bound" and source is not None and TODO.search(source):
            raise ContractError(
                f"Figma Data `{entry_id}` is bound but its Source is still TODO"
            )
        if binding == "pending" and (source is None or TODO.search(source) is None):
            raise ContractError(
                f"Figma Data `{entry_id}` pending Source must contain "
                "`TODO(figma-data)`"
            )
        if binding == "static" and fields["Kind"] != "static-copy":
            raise ContractError(
                f"Figma Data `{entry_id}` Binding `static` requires "
                "Kind `static-copy`"
            )
        entries.append(
            FigmaFillData(
                id=entry_id,
                node=fields["Node"],
                kind=fields["Kind"],
                binding=binding,
                render=render,
                source=source,
                fixture=fixture,
            )
        )
    return tuple(entries)


def audit_figma_fill_data(project_root: Path) -> dict[str, Any]:
    """Report every Figma-bound contract's declared fill-data state."""

    root = project_root.resolve()
    contracts: list[dict[str, Any]] = []
    summary = {
        "bound": 0,
        "pending": 0,
        "static": 0,
        "legacy_unreviewed": 0,
        "invalid": 0,
    }
    for path in sorted((root / "lib").rglob("*.c.dart")):
        sections = doc_sections(path.read_text(encoding="utf-8"))
        if "Figma" not in sections:
            continue
        relative = path.relative_to(root).as_posix()
        if "Figma Data" not in sections:
            contracts.append(
                {"contract": relative, "status": "legacy_unreviewed", "entries": []}
            )
            summary["legacy_unreviewed"] += 1
            continue
        try:
            entries = parse_figma_fill_data(sections)
        except ContractError as error:
            contracts.append(
                {
                    "contract": relative,
                    "status": "invalid",
                    "error": str(error),
                    "entries": [],
                }
            )
            summary["invalid"] += 1
            continue
        contracts.append(
            {
                "contract": relative,
                "status": "declared",
                "entries": [asdict(entry) for entry in entries],
            }
        )
        for entry in entries:
            summary[entry.binding] += 1
    return {
        "schema": SCHEMA,
        "project_root": str(root),
        "summary": summary,
        "contracts": contracts,
    }


def markdown_report(report: dict[str, Any]) -> str:
    """Render a compact human review of the audit result."""

    summary = report["summary"]
    lines = [
        "# Figma Fill Data Audit",
        "",
        "| Bound | Pending | Static copy | Legacy unreviewed | Invalid |",
        "| ---: | ---: | ---: | ---: | ---: |",
        "| {bound} | {pending} | {static} | {legacy_unreviewed} | {invalid} |".format(
            **summary
        ),
        "",
        "| Contract | ID | Binding | Render | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for contract in report["contracts"]:
        entries = contract["entries"]
        if contract["status"] != "declared":
            lines.append(
                f"| {contract['contract']} | — | {contract['status']} | — | "
                f"{contract.get('error', 'add Figma Data')} |"
            )
            continue
        if not entries:
            lines.append(f"| {contract['contract']} | — | none | — | — |")
            continue
        for entry in entries:
            lines.append(
                "| {contract} | {id} | {binding} | {render} | {source} |".format(
                    contract=contract["contract"],
                    id=entry["id"],
                    binding=entry["binding"],
                    render=entry["render"] or "—",
                    source=entry["source"] or "—",
                )
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    try:
        report = audit_figma_fill_data(args.project_root)
    except ContractError as error:
        print(f"figma fill data error: {error}", file=sys.stderr)
        return 2
    print(
        markdown_report(report)
        if args.format == "markdown"
        else json.dumps(report, ensure_ascii=False, indent=2)
    )
    if args.strict and any(
        report["summary"][key] for key in ("pending", "legacy_unreviewed", "invalid")
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

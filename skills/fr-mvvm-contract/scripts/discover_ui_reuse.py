#!/usr/bin/env python3
"""Discover cross-route public UI entries by their declared capabilities."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Literal

from contract_core import bracket_refs, doc_sections


Kind = Literal["component", "widget"]


def relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def public_symbols(module_files: list[Path]) -> set[str]:
    """Return public class names declared by one Dart library/module."""

    pattern = re.compile(r"\bclass\s+([A-Za-z][A-Za-z0-9_]*)\b")
    return {
        name
        for path in module_files
        for name in pattern.findall(path.read_text(encoding="utf-8"))
        if not name.startswith("_")
    }


def component_library_files(entry: Path) -> list[Path]:
    """Return the public component library and its declared parts only."""

    source = entry.read_text(encoding="utf-8")
    part_names = re.findall(r"\bpart\s+['\"]([^'\"]+)['\"]\s*;", source)
    return [entry, *(entry.parent / part for part in part_names if (entry.parent / part).is_file())]


def section_values(source: str, section: str) -> list[str]:
    return [line.removeprefix("-").strip() for line in doc_sections(source).get(section, [])]


def normalize_capabilities(values: list[str]) -> str:
    return " ".join(values).casefold()


def matches(values: list[str], query: str) -> bool:
    normalized = normalize_capabilities(values)
    return all(word in normalized for word in query.casefold().split())


def inspect_module(
    *,
    kind: Kind,
    root: Path,
    entry: Path,
    metadata: Path,
    files: list[Path],
    query: str,
) -> dict[str, object] | None:
    source = metadata.read_text(encoding="utf-8")
    capabilities = section_values(source, "Capabilities")
    public_section = "Public Views" if kind == "component" else "Public Widgets"
    public = bracket_refs(doc_sections(source).get(public_section, []))
    if not capabilities or not matches(capabilities, query):
        return None

    symbols = public_symbols(files)
    missing = [name for name in public if name not in symbols]
    return {
        "kind": kind,
        "module": entry.stem,
        "entry": relative(entry, root),
        "metadata": relative(metadata, root),
        "capabilities": capabilities,
        "publicViews" if kind == "component" else "publicWidgets": public,
        "valid": bool(public) and not missing,
        "errors": (
            ([] if public else [f"missing `{public_section}:`"])
            + [f"public entry `{name}` is not declared by the module" for name in missing]
        ),
    }


def discover_components(root: Path, query: str) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    components_root = root / "lib/components"
    if not components_root.is_dir():
        return result
    for entry in sorted(components_root.glob("*/*.dart")):
        if entry.name != f"{entry.parent.name}.dart":
            continue
        metadata = entry.with_name(f"{entry.stem}.c.dart")
        if not metadata.is_file():
            continue
        candidate = inspect_module(
            kind="component",
            root=root,
            entry=entry,
            metadata=metadata,
            files=component_library_files(entry),
            query=query,
        )
        if candidate:
            result.append(candidate)
    return result


def discover_widgets(root: Path, query: str) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    widgets_root = root / "lib/widgets"
    if not widgets_root.is_dir():
        return result
    for entry in sorted(widgets_root.rglob("*.dart")):
        source = entry.read_text(encoding="utf-8")
        if "Capabilities:" not in source or "Public Widgets:" not in source:
            continue
        candidate = inspect_module(
            kind="widget",
            root=root,
            entry=entry,
            metadata=entry,
            files=[entry],
            query=query,
        )
        if candidate:
            result.append(candidate)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--capability", required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = args.project_root.resolve()
    if not (root / "lib").is_dir():
        parser.error("--project-root must contain lib/")
    components = discover_components(root, args.capability)
    widgets = discover_widgets(root, args.capability)
    result = {
        "capability": args.capability,
        "components": components,
        "widgets": widgets,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.strict and any(not item["valid"] for item in [*components, *widgets]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

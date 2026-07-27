#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Audit Figma fidelity from Dart contracts and exact asset lock files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from contract_core import ContractError, doc_sections
from figma_contract import parse_figma_contract_nodes

ASSET_LOCK_SCHEMA = "fr-mvvm-contract.figma-assets-lock.v1"
EXCLUDED_DISPOSITION = re.compile(r"^excluded\s*\|\s*(.+)$")
VIEWPORT_ENTRY = re.compile(r"^-\s*Viewport:\s*([1-9][0-9]*)\s*x\s*([1-9][0-9]*)$")
ASSET_LOCK_ENTRY = re.compile(r"^-\s*Asset Lock:\s*(\S+)$")
REGRESSION_TEST_ENTRY = re.compile(r"^-\s*Regression Test:\s*(.+)$")


class AuditConfigError(ValueError):
    """Raised when a fidelity contract or asset lock is invalid or unsafe."""


@dataclass(frozen=True)
class Check:
    """One stable audit result."""

    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class FidelityContract:
    """Audited facts owned by one Dart component contract."""

    contract_path: Path
    width: int
    height: int
    asset_lock_path: Path | None
    regression_test: str


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AuditConfigError(f"{field} must be an object")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise AuditConfigError(f"{field} must be an array")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise AuditConfigError(f"{field} must be a non-empty string")
    return value


def _relative(value: Any, field: str) -> str:
    raw = _string(value, field)
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or "\\" in raw:
        raise AuditConfigError(f"{field} must be a safe repository-relative path")
    return raw


def _contained_path(root: Path, candidate: Path, field: str) -> Path:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise AuditConfigError(f"{field} escapes the project root") from exc
    return candidate


def _project_path(root: Path, value: Any, field: str) -> Path:
    relative = _relative(value, field)
    return _contained_path(root, (root / relative).resolve(), field)


def _read_text(paths: tuple[Path, ...]) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8") for path in paths if path.is_file()
    )


def _asset_is_rendered(path: str, dart_source: str) -> bool:
    if path not in dart_source:
        return False
    if path.lower().endswith(".svg"):
        return "SvgPicture.asset" in dart_source
    return "Image.asset" in dart_source or "AssetImage" in dart_source


def _load_asset_lock(root: Path, lock_path: Path) -> list[dict[str, str]]:
    try:
        lock = _mapping(json.loads(lock_path.read_text(encoding="utf-8")), "lock")
    except (json.JSONDecodeError, OSError) as exc:
        raise AuditConfigError(f"invalid asset lock {lock_path}: {exc}") from exc
    unknown = set(lock) - {"schema", "assets"}
    if unknown:
        raise AuditConfigError(
            "asset lock has unsupported fields: " + ", ".join(sorted(unknown))
        )
    if lock.get("schema") != ASSET_LOCK_SCHEMA:
        raise AuditConfigError(f"lock.schema must be {ASSET_LOCK_SCHEMA}")

    assets: list[dict[str, str]] = []
    names: set[str] = set()
    paths: set[str] = set()
    for index, raw_asset in enumerate(_list(lock.get("assets"), "lock.assets")):
        field = f"lock.assets[{index}]"
        asset = _mapping(raw_asset, field)
        unknown_asset = set(asset) - {"name", "path", "source_export", "sha256"}
        if unknown_asset:
            raise AuditConfigError(
                f"{field} has unsupported fields: "
                + ", ".join(sorted(unknown_asset))
            )
        name = _string(asset.get("name"), f"{field}.name")
        relative_path = _relative(asset.get("path"), f"{field}.path")
        source_export = _string(
            asset.get("source_export"), f"{field}.source_export"
        )
        sha256 = _string(asset.get("sha256"), f"{field}.sha256")
        if len(sha256) != 64 or any(
            char not in "0123456789abcdef" for char in sha256
        ):
            raise AuditConfigError(f"{field}.sha256 must be lowercase SHA-256")
        if name in names:
            raise AuditConfigError(f"duplicate asset name: {name}")
        if relative_path in paths:
            raise AuditConfigError(f"duplicate asset path: {relative_path}")
        names.add(name)
        paths.add(relative_path)
        _project_path(root, relative_path, f"{field}.path")
        assets.append(
            {
                "name": name,
                "path": relative_path,
                "source_export": source_export,
                "sha256": sha256,
            }
        )
    return assets


def audit_asset_lock(root: Path, lock_path: Path) -> list[Check]:
    """Validate one pure Figma asset lock without page semantics."""

    project_root = root.resolve()
    resolved_lock = _contained_path(
        project_root, lock_path.resolve(), "asset_lock"
    )
    assets = _load_asset_lock(project_root, resolved_lock)
    hash_errors: list[str] = []
    for asset in assets:
        path = _project_path(project_root, asset["path"], "asset.path")
        if not path.is_file():
            hash_errors.append(f"missing:{asset['path']}")
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != asset["sha256"]:
            hash_errors.append(f"hash:{asset['path']}")
    return [
        Check(
            name="exact_figma_assets",
            passed=not hash_errors,
            detail=(
                "all locked asset hashes match"
                if not hash_errors
                else ", ".join(hash_errors)
            ),
        )
    ]


def _parse_fidelity_contract(
    root: Path,
    contract_path: Path,
    lines: list[str],
) -> FidelityContract:
    relative_contract = contract_path.relative_to(root).as_posix()
    if len(lines) != 3:
        raise AuditConfigError(
            f"{relative_contract}.Figma Fidelity must declare Viewport, "
            "Asset Lock, and Regression Test"
        )
    viewport_match = VIEWPORT_ENTRY.fullmatch(lines[0])
    asset_lock_match = ASSET_LOCK_ENTRY.fullmatch(lines[1])
    test_match = REGRESSION_TEST_ENTRY.fullmatch(lines[2])
    if not viewport_match or not asset_lock_match or not test_match:
        raise AuditConfigError(
            f"{relative_contract}.Figma Fidelity must use `- Viewport: W x H`, "
            "`- Asset Lock: <path|none>`, then `- Regression Test: <name>`"
        )
    asset_lock_value = asset_lock_match.group(1)
    asset_lock_path = (
        None
        if asset_lock_value == "none"
        else _project_path(
            root,
            asset_lock_value,
            f"{relative_contract}.Figma Fidelity.Asset Lock",
        )
    )
    if asset_lock_path is not None and not asset_lock_path.is_file():
        raise AuditConfigError(
            f"{relative_contract} asset lock does not exist: {asset_lock_value}"
        )
    return FidelityContract(
        contract_path=contract_path,
        width=int(viewport_match.group(1)),
        height=int(viewport_match.group(2)),
        asset_lock_path=asset_lock_path,
        regression_test=test_match.group(1).strip(),
    )


def _audit_contract(
    root: Path,
    fidelity: FidelityContract,
    *,
    dart_paths: tuple[Path, ...],
    test_paths: tuple[Path, ...],
) -> list[Check]:
    contract_relative = fidelity.contract_path.relative_to(root).as_posix()
    prefix = contract_relative.removesuffix(".c.dart").replace("/", "_")
    contract_source = fidelity.contract_path.read_text(encoding="utf-8")
    results: list[Check] = []

    asset_paths: tuple[str, ...] = ()
    if fidelity.asset_lock_path is not None:
        assets = _load_asset_lock(root, fidelity.asset_lock_path)
        asset_paths = tuple(asset["path"] for asset in assets)
        for check in audit_asset_lock(root, fidelity.asset_lock_path):
            results.append(
                Check(f"{prefix}:{check.name}", check.passed, check.detail)
            )

    dart_sources = {
        path: path.read_text(encoding="utf-8")
        for path in dart_paths
        if path.is_file()
    }
    unrendered_assets = [
        path
        for path in asset_paths
        if not any(
            _asset_is_rendered(path, source)
            for source in dart_sources.values()
        )
    ]
    results.append(
        Check(
            name=f"{prefix}:locked_assets_rendered",
            passed=not unrendered_assets,
            detail=(
                "every locked asset is rendered by Dart source"
                if not unrendered_assets
                else "unrendered:" + ",".join(unrendered_assets)
            ),
        )
    )

    test_source = _read_text(test_paths)
    missing_test_parts = [
        value
        for value in (
            fidelity.regression_test,
            f"Size({fidelity.width}, {fidelity.height})",
        )
        if value not in test_source
    ]
    results.append(
        Check(
            name=f"{prefix}:regression_test",
            passed=not missing_test_parts,
            detail=(
                "declared regression test covers the contract viewport"
                if not missing_test_parts
                else "missing:" + ",".join(missing_test_parts)
            ),
        )
    )
    results.append(
        Check(
            name=f"{prefix}:contract_is_final",
            passed="TODO" not in contract_source,
            detail=(
                "contract contains no TODO"
                if "TODO" not in contract_source
                else "contract contains TODO"
            ),
        )
    )
    return results


def audit_discovered(
    root: Path, *, contracts_glob: str = "lib/**/*.c.dart"
) -> list[Check]:
    """Discover all Figma fidelity authority from component contracts."""

    project_root = root.resolve()
    safe_glob = _relative(contracts_glob, "contracts_glob")
    contract_paths = tuple(
        sorted(
            _contained_path(project_root, path.resolve(), "contracts_glob")
            for path in project_root.glob(safe_glob)
            if path.is_file()
        )
    )
    dart_paths = tuple(sorted(project_root.glob("lib/**/*.dart")))
    test_paths = tuple(sorted(project_root.glob("test/**/*.dart")))
    errors: list[str] = []
    exclusions: list[str] = []
    audited: list[FidelityContract] = []
    used_locks: dict[Path, str] = {}
    used_bindings: dict[tuple[str, str], str] = {}
    primary_count = 0

    for contract_path in contract_paths:
        relative_contract = contract_path.relative_to(project_root).as_posix()
        sections = doc_sections(contract_path.read_text(encoding="utf-8"))
        if "Figma" not in sections:
            continue
        primary_count += 1
        try:
            nodes = parse_figma_contract_nodes(sections)
        except ContractError as exc:
            errors.append(f"invalid-contract:{relative_contract}:{exc}")
            continue

        lines = sections.get("Figma Fidelity", [])
        if len(lines) == 1:
            excluded = EXCLUDED_DISPOSITION.fullmatch(lines[0])
            if excluded:
                exclusions.append(f"{relative_contract}:{excluded.group(1).strip()}")
                continue
        try:
            fidelity = _parse_fidelity_contract(
                project_root, contract_path, lines
            )
        except AuditConfigError as exc:
            errors.append(f"invalid-disposition:{exc}")
            continue

        binding = (nodes.primary.file_key, nodes.primary.node_id)
        previous_binding_owner = used_bindings.get(binding)
        if previous_binding_owner:
            errors.append(
                f"duplicate-primary-binding:{nodes.primary.file_key}/"
                f"{nodes.primary.node_id}:{previous_binding_owner},"
                f"{relative_contract}"
            )
            continue
        used_bindings[binding] = relative_contract

        if fidelity.asset_lock_path is not None:
            previous_lock_owner = used_locks.get(fidelity.asset_lock_path)
            if previous_lock_owner:
                lock_relative = fidelity.asset_lock_path.relative_to(
                    project_root
                ).as_posix()
                errors.append(
                    f"reused-asset-lock:{lock_relative}:"
                    f"{previous_lock_owner},{relative_contract}"
                )
                continue
            used_locks[fidelity.asset_lock_path] = relative_contract
        audited.append(fidelity)

    if primary_count == 0:
        errors.append(f"no-primary-contracts:{safe_glob}")

    checks = [
        Check(
            name="figma_fidelity_coverage",
            passed=not errors,
            detail=(
                f"{primary_count} primary contracts accounted for"
                if not errors
                else ", ".join(errors)
            ),
        ),
        Check(
            name="figma_fidelity_exclusions",
            passed=True,
            detail=(
                "no explicit exclusions"
                if not exclusions
                else "; ".join(exclusions)
            ),
        ),
    ]
    for fidelity in audited:
        checks.extend(
            _audit_contract(
                project_root,
                fidelity,
                dart_paths=dart_paths,
                test_paths=test_paths,
            )
        )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--asset-lock", type=Path)
    mode.add_argument("--discover", action="store_true")
    parser.add_argument("--contracts-glob", default="lib/**/*.c.dart")
    parser.add_argument("--allow-fail", action="store_true")
    args = parser.parse_args()

    try:
        checks = (
            audit_discovered(
                args.project_root, contracts_glob=args.contracts_glob
            )
            if args.discover
            else audit_asset_lock(args.project_root.resolve(), args.asset_lock)
        )
    except (AuditConfigError, json.JSONDecodeError, OSError) as exc:
        parser.error(str(exc))
    failed = [check.name for check in checks if not check.passed]
    result = {
        "status": "pass" if not failed else "fail",
        "passed": len(checks) - len(failed),
        "failed": failed,
        "checks": [asdict(check) for check in checks],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failed or args.allow_fail else 1


if __name__ == "__main__":
    sys.exit(main())

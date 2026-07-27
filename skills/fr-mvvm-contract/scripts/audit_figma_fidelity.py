#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Audit project-configured Figma fidelity invariants."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

PROFILE_SCHEMA = "fr-mvvm-contract.figma-fidelity.v1"


class AuditConfigError(ValueError):
    """Raised when a fidelity profile is invalid or unsafe."""


@dataclass(frozen=True)
class Check:
    """One stable audit result."""

    name: str
    passed: bool
    detail: str


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AuditConfigError(f"{field} must be an object")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise AuditConfigError(f"{field} must be an array")
    return value


def _nonempty_list(value: Any, field: str) -> list[Any]:
    items = _list(value, field)
    if not items:
        raise AuditConfigError(f"{field} must not be empty")
    return items


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise AuditConfigError(f"{field} must be a non-empty string")
    return value


def _strings(value: Any, field: str) -> tuple[str, ...]:
    return tuple(
        _string(item, f"{field}[{index}]")
        for index, item in enumerate(_list(value, field))
    )


def _relative(value: Any, field: str) -> str:
    raw = _string(value, field)
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or "\\" in raw:
        raise AuditConfigError(f"{field} must be a safe repository-relative path")
    return raw


def _project_path(root: Path, value: Any, field: str) -> Path:
    relative = _relative(value, field)
    candidate = (root / relative).resolve()
    return _contained_path(root, candidate, field)


def _contained_path(root: Path, candidate: Path, field: str) -> Path:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise AuditConfigError(f"{field} escapes the project root") from exc
    return candidate


def _read_files(paths: tuple[Path, ...]) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8") for path in paths if path.is_file()
    )


def _matched_paths(root: Path, rule: dict[str, Any], field: str) -> tuple[Path, ...]:
    has_path = "path" in rule
    has_glob = "glob" in rule
    if has_path == has_glob:
        raise AuditConfigError(f"{field} must declare exactly one of path or glob")
    if has_path:
        return (_project_path(root, rule["path"], f"{field}.path"),)
    pattern = _relative(rule["glob"], f"{field}.glob")
    return tuple(
        sorted(
            {
                _contained_path(root, path.resolve(), f"{field}.glob")
                for path in root.glob(pattern)
            }
        )
    )


def _source_rule_errors(root: Path, rules: list[Any], field: str) -> list[str]:
    errors: list[str] = []
    for index, raw_rule in enumerate(rules):
        rule_field = f"{field}[{index}]"
        rule = _mapping(raw_rule, rule_field)
        unknown = set(rule) - {"path", "glob", "contains", "excludes"}
        if unknown:
            raise AuditConfigError(
                f"{rule_field} has unsupported fields: {', '.join(sorted(unknown))}"
            )
        paths = _matched_paths(root, rule, rule_field)
        if not paths or any(not path.is_file() for path in paths):
            errors.append(f"missing:{rule.get('path') or rule.get('glob')}")
            continue
        text = _read_files(paths)
        contains = _strings(rule.get("contains", []), f"{rule_field}.contains")
        excludes = _strings(rule.get("excludes", []), f"{rule_field}.excludes")
        errors.extend(
            f"missing-text:{value}" for value in contains if value not in text
        )
        errors.extend(f"forbidden-text:{value}" for value in excludes if value in text)
    return errors


def _check_assets(root: Path, assets: list[Any]) -> Check:
    errors: list[str] = []
    for index, raw_asset in enumerate(assets):
        field = f"assets[{index}]"
        asset = _mapping(raw_asset, field)
        unknown = set(asset) - {"name", "path", "source_export", "sha256"}
        if unknown:
            raise AuditConfigError(
                f"{field} has unsupported fields: {', '.join(sorted(unknown))}"
            )
        _string(asset.get("name"), f"{field}.name")
        _string(asset.get("source_export"), f"{field}.source_export")
        expected = _string(asset.get("sha256"), f"{field}.sha256")
        if len(expected) != 64 or any(
            char not in "0123456789abcdef" for char in expected
        ):
            raise AuditConfigError(f"{field}.sha256 must be lowercase SHA-256")
        path = _project_path(root, asset.get("path"), f"{field}.path")
        relative = _relative(asset.get("path"), f"{field}.path")
        if not path.is_file():
            errors.append(f"missing:{relative}")
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f"hash:{relative}")
    return Check(
        name="exact_figma_assets",
        passed=not errors,
        detail="all manifest hashes match" if not errors else ", ".join(errors),
    )


def _check_source_rules(root: Path, check: dict[str, Any], field: str) -> Check:
    unknown = set(check) - {"name", "kind", "detail", "rules"}
    if unknown:
        raise AuditConfigError(
            f"{field} has unsupported fields: {', '.join(sorted(unknown))}"
        )
    name = _string(check.get("name"), f"{field}.name")
    detail = _string(check.get("detail"), f"{field}.detail")
    errors = _source_rule_errors(
        root, _nonempty_list(check.get("rules"), f"{field}.rules"), f"{field}.rules"
    )
    return Check(
        name, not errors, detail if not errors else f"{detail}: {', '.join(errors)}"
    )


def _check_unique_text(root: Path, check: dict[str, Any], field: str) -> Check:
    unknown = set(check) - {"name", "kind", "detail", "globs", "values", "expected"}
    if unknown:
        raise AuditConfigError(
            f"{field} has unsupported fields: {', '.join(sorted(unknown))}"
        )
    name = _string(check.get("name"), f"{field}.name")
    detail = _string(check.get("detail"), f"{field}.detail")
    patterns = _strings(
        _nonempty_list(check.get("globs"), f"{field}.globs"), f"{field}.globs"
    )
    paths: set[Path] = set()
    for index, pattern in enumerate(patterns):
        safe_pattern = _relative(pattern, f"{field}.globs[{index}]")
        paths.update(
            _contained_path(root, path.resolve(), f"{field}.globs[{index}]")
            for path in root.glob(safe_pattern)
            if path.is_file()
        )
    expected = check.get("expected")
    if not isinstance(expected, int) or isinstance(expected, bool) or expected < 0:
        raise AuditConfigError(f"{field}.expected must be a non-negative integer")
    text = _read_files(tuple(sorted(paths)))
    errors = [
        f"count:{value}={text.count(value)}"
        for value in _strings(
            _nonempty_list(check.get("values"), f"{field}.values"),
            f"{field}.values",
        )
        if text.count(value) != expected
    ]
    return Check(
        name, not errors, detail if not errors else f"{detail}: {', '.join(errors)}"
    )


def _check_paths_absent(root: Path, check: dict[str, Any], field: str) -> Check:
    unknown = set(check) - {"name", "kind", "detail", "paths"}
    if unknown:
        raise AuditConfigError(
            f"{field} has unsupported fields: {', '.join(sorted(unknown))}"
        )
    name = _string(check.get("name"), f"{field}.name")
    detail = _string(check.get("detail"), f"{field}.detail")
    present = []
    for index, raw_path in enumerate(
        _nonempty_list(check.get("paths"), f"{field}.paths")
    ):
        path_field = f"{field}.paths[{index}]"
        path = _project_path(root, raw_path, path_field)
        if path.exists():
            present.append(_relative(raw_path, path_field))
    return Check(
        name,
        not present,
        detail if not present else f"{detail}: present:{', '.join(present)}",
    )


def audit(root: Path, profile_path: Path) -> list[Check]:
    """Run the profile's stable fidelity checks against a project root."""

    project_root = root.resolve()
    profile = _mapping(json.loads(profile_path.read_text(encoding="utf-8")), "profile")
    unknown = set(profile) - {
        "schema",
        "id",
        "figma_file_key",
        "primary_node",
        "viewport",
        "assets",
        "checks",
    }
    if unknown:
        raise AuditConfigError(
            f"profile has unsupported fields: {', '.join(sorted(unknown))}"
        )
    if profile.get("schema") != PROFILE_SCHEMA:
        raise AuditConfigError(f"profile.schema must be {PROFILE_SCHEMA}")
    _string(profile.get("id"), "profile.id")
    _string(profile.get("figma_file_key"), "profile.figma_file_key")
    _string(profile.get("primary_node"), "profile.primary_node")
    viewport = _mapping(profile.get("viewport"), "profile.viewport")
    if set(viewport) != {"width", "height"}:
        raise AuditConfigError("profile.viewport must contain width and height")
    for axis in ("width", "height"):
        value = viewport[axis]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise AuditConfigError(
                f"profile.viewport.{axis} must be a positive integer"
            )

    checks = [
        _check_assets(project_root, _list(profile.get("assets"), "profile.assets"))
    ]
    names = {"exact_figma_assets"}
    for index, raw_check in enumerate(_list(profile.get("checks"), "profile.checks")):
        field = f"profile.checks[{index}]"
        check = _mapping(raw_check, field)
        kind = _string(check.get("kind"), f"{field}.kind")
        if kind == "source_rules":
            result = _check_source_rules(project_root, check, field)
        elif kind == "unique_text":
            result = _check_unique_text(project_root, check, field)
        elif kind == "paths_absent":
            result = _check_paths_absent(project_root, check, field)
        else:
            raise AuditConfigError(f"{field}.kind is unsupported: {kind}")
        if result.name in names:
            raise AuditConfigError(f"duplicate check name: {result.name}")
        names.add(result.name)
        checks.append(result)
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--allow-fail", action="store_true")
    args = parser.parse_args()

    try:
        checks = audit(args.project_root, args.profile.resolve())
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

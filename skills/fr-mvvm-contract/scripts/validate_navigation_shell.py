#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate project-configured persistent navigation shell ownership."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any


PROFILE_SCHEMA = "fr-mvvm-contract.navigation-shell.v1"


class NavigationShellConfigError(ValueError):
    """Raised when a navigation-shell profile is invalid or unsafe."""


@dataclass(frozen=True)
class Check:
    """One stable navigation-shell validation result."""

    name: str
    passed: bool
    detail: str


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise NavigationShellConfigError(f"{field} must be an object")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise NavigationShellConfigError(f"{field} must be an array")
    return value


def _nonempty_list(value: Any, field: str) -> list[Any]:
    items = _list(value, field)
    if not items:
        raise NavigationShellConfigError(f"{field} must not be empty")
    return items


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise NavigationShellConfigError(f"{field} must be a non-empty string")
    return value


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise NavigationShellConfigError(f"{field} must be a boolean")
    return value


def _relative(value: Any, field: str) -> str:
    raw = _string(value, field)
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or "\\" in raw:
        raise NavigationShellConfigError(
            f"{field} must be a safe repository-relative path"
        )
    return raw


def _project_path(root: Path, value: Any, field: str) -> Path:
    relative = _relative(value, field)
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise NavigationShellConfigError(f"{field} escapes the project root") from exc
    return candidate


def _read_file(root: Path, value: Any, field: str) -> tuple[Path, str]:
    path = _project_path(root, value, field)
    if not path.is_file():
        return path, ""
    return path, path.read_text(encoding="utf-8")


def _missing_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [f"missing-text:{token}" for token in tokens if token not in text]


def _forbidden_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [f"forbidden-text:{token}" for token in tokens if token in text]


def _strings(value: Any, field: str) -> tuple[str, ...]:
    return tuple(
        _string(item, f"{field}[{index}]")
        for index, item in enumerate(_list(value, field))
    )


def _check_shell(root: Path, shell: dict[str, Any], index: int) -> list[Check]:
    field = f"profile.shells[{index}]"
    allowed = {
        "id",
        "strategy",
        "branch_switch_transition",
        "preserve_branch_state",
        "router_path",
        "shell_path",
        "shell_widget",
        "navigation_path",
        "navigation_widget",
        "selection_callback",
        "top_region_widget",
        "branches",
        "tests",
    }
    unknown = set(shell) - allowed
    if unknown:
        raise NavigationShellConfigError(
            f"{field} has unsupported fields: {', '.join(sorted(unknown))}"
        )

    shell_id = _string(shell.get("id"), f"{field}.id")
    if shell.get("strategy") != "stateful-indexed-stack":
        raise NavigationShellConfigError(
            f"{field}.strategy must be stateful-indexed-stack"
        )
    if shell.get("branch_switch_transition") != "none":
        raise NavigationShellConfigError(
            f"{field}.branch_switch_transition must be none"
        )
    if not _bool(
        shell.get("preserve_branch_state"), f"{field}.preserve_branch_state"
    ):
        raise NavigationShellConfigError(
            f"{field}.preserve_branch_state must be true"
        )

    router_path, router_text = _read_file(
        root, shell.get("router_path"), f"{field}.router_path"
    )
    shell_path, shell_text = _read_file(
        root, shell.get("shell_path"), f"{field}.shell_path"
    )
    navigation_path, navigation_text = _read_file(
        root, shell.get("navigation_path"), f"{field}.navigation_path"
    )
    shell_widget = _string(shell.get("shell_widget"), f"{field}.shell_widget")
    navigation_widget = _string(
        shell.get("navigation_widget"), f"{field}.navigation_widget"
    )
    selection_callback = _string(
        shell.get("selection_callback"), f"{field}.selection_callback"
    )
    top_region_widget = _string(
        shell.get("top_region_widget"), f"{field}.top_region_widget"
    )

    router_errors = (
        ([] if router_text else [f"missing:{router_path.relative_to(root)}"])
        + _missing_tokens(
            router_text,
            (
                "StatefulShellRoute.indexedStack",
                shell_widget,
            ),
        )
    )
    checks = [
        Check(
            f"{shell_id}.router_strategy",
            not router_errors,
            "stateful indexed-stack router configured"
            if not router_errors
            else ", ".join(router_errors),
        )
    ]

    shell_errors = (
        ([] if shell_text else [f"missing:{shell_path.relative_to(root)}"])
        + _missing_tokens(
            shell_text,
            (
                f"class {shell_widget}",
                "StatefulNavigationShell",
                "Scaffold(",
                "bottomNavigationBar:",
                f"{navigation_widget}(",
                top_region_widget,
                ".goBranch(",
            ),
        )
    )
    checks.append(
        Check(
            f"{shell_id}.single_shell_owner",
            not shell_errors,
            "shell owns persistent Scaffold, top region, and bottom navigation"
            if not shell_errors
            else ", ".join(shell_errors),
        )
    )

    branches_raw = _nonempty_list(shell.get("branches"), f"{field}.branches")
    if len(branches_raw) < 2:
        raise NavigationShellConfigError(f"{field}.branches must contain at least two")

    branch_ids: set[str] = set()
    page_names: list[str] = []
    branch_errors: list[str] = []
    for branch_index, raw_branch in enumerate(branches_raw):
        branch_field = f"{field}.branches[{branch_index}]"
        branch = _mapping(raw_branch, branch_field)
        unknown_branch = set(branch) - {
            "id",
            "route",
            "page",
            "route_path",
            "view_path",
        }
        if unknown_branch:
            raise NavigationShellConfigError(
                f"{branch_field} has unsupported fields: "
                f"{', '.join(sorted(unknown_branch))}"
            )
        branch_id = _string(branch.get("id"), f"{branch_field}.id")
        if branch_id in branch_ids:
            raise NavigationShellConfigError(f"duplicate branch id: {branch_id}")
        branch_ids.add(branch_id)
        route = _string(branch.get("route"), f"{branch_field}.route")
        page = _string(branch.get("page"), f"{branch_field}.page")
        page_names.append(page)
        route_path, route_text = _read_file(
            root, branch.get("route_path"), f"{branch_field}.route_path"
        )
        view_path, view_text = _read_file(
            root, branch.get("view_path"), f"{branch_field}.view_path"
        )
        if not route_text:
            branch_errors.append(f"{branch_id}:missing:{route_path.relative_to(root)}")
        else:
            branch_errors.extend(
                f"{branch_id}:{error}"
                for error in _missing_tokens(route_text, (page, route))
            )
        if not view_text:
            branch_errors.append(f"{branch_id}:missing:{view_path.relative_to(root)}")
        else:
            branch_errors.extend(
                f"{branch_id}:{error}"
                for error in _forbidden_tokens(
                    view_text,
                    (
                        "Scaffold(",
                        "bottomNavigationBar:",
                        f"{navigation_widget}(",
                        f"{top_region_widget}(",
                    ),
                )
            )
    checks.append(
        Check(
            f"{shell_id}.branch_content_only",
            not branch_errors,
            "branch Views contain content only"
            if not branch_errors
            else ", ".join(branch_errors),
        )
    )

    navigation_errors = (
        ([] if navigation_text else [f"missing:{navigation_path.relative_to(root)}"])
        + _missing_tokens(
            navigation_text,
            (
                f"class {navigation_widget}",
                "currentIndex",
                selection_callback,
            ),
        )
        + _forbidden_tokens(
            navigation_text,
            (
                "Scaffold(",
                ".go(context)",
                ".push(context)",
                ".replace(context)",
                *page_names,
            ),
        )
    )
    checks.append(
        Check(
            f"{shell_id}.passive_navigation",
            not navigation_errors,
            "bottom navigation is presentation-only"
            if not navigation_errors
            else ", ".join(navigation_errors),
        )
    )

    owner_paths = []
    for path in root.glob("lib/**/*.dart"):
        if path.name.endswith((".g.dart", ".freezed.dart")) or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "bottomNavigationBar:" in text and f"{navigation_widget}(" in text:
            owner_paths.append(path.resolve())
    expected_owner = shell_path.resolve()
    owner_errors = []
    if owner_paths != [expected_owner]:
        rendered = ", ".join(
            str(path.relative_to(root)) for path in sorted(owner_paths)
        ) or "none"
        owner_errors.append(f"owners:{rendered}")
    checks.append(
        Check(
            f"{shell_id}.single_bottom_navigation_slot",
            not owner_errors,
            "exactly one shell bottom-navigation slot"
            if not owner_errors
            else ", ".join(owner_errors),
        )
    )

    tests = _mapping(shell.get("tests"), f"{field}.tests")
    unknown_tests = set(tests) - {"globs", "contains"}
    if unknown_tests:
        raise NavigationShellConfigError(
            f"{field}.tests has unsupported fields: "
            f"{', '.join(sorted(unknown_tests))}"
        )
    test_paths: set[Path] = set()
    for glob_index, raw_glob in enumerate(
        _nonempty_list(tests.get("globs"), f"{field}.tests.globs")
    ):
        pattern = _relative(raw_glob, f"{field}.tests.globs[{glob_index}]")
        test_paths.update(path for path in root.glob(pattern) if path.is_file())
    test_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(test_paths)
    )
    test_errors = (
        ([] if test_paths else ["missing:test-files"])
        + _missing_tokens(
            test_text,
            _strings(
                _nonempty_list(
                    tests.get("contains"), f"{field}.tests.contains"
                ),
                f"{field}.tests.contains",
            ),
        )
    )
    checks.append(
        Check(
            f"{shell_id}.runtime_regression",
            not test_errors,
            "runtime shell regression coverage declared"
            if not test_errors
            else ", ".join(test_errors),
        )
    )
    return checks


def validate(root: Path, profile_path: Path) -> list[Check]:
    """Validate every persistent shell declared by the project profile."""

    project_root = root.resolve()
    profile = _mapping(json.loads(profile_path.read_text(encoding="utf-8")), "profile")
    unknown = set(profile) - {"schema", "shells"}
    if unknown:
        raise NavigationShellConfigError(
            f"profile has unsupported fields: {', '.join(sorted(unknown))}"
        )
    if profile.get("schema") != PROFILE_SCHEMA:
        raise NavigationShellConfigError(f"profile.schema must be {PROFILE_SCHEMA}")

    checks: list[Check] = []
    shell_ids: set[str] = set()
    for index, raw_shell in enumerate(
        _nonempty_list(profile.get("shells"), "profile.shells")
    ):
        shell = _mapping(raw_shell, f"profile.shells[{index}]")
        shell_id = _string(shell.get("id"), f"profile.shells[{index}].id")
        if shell_id in shell_ids:
            raise NavigationShellConfigError(f"duplicate shell id: {shell_id}")
        shell_ids.add(shell_id)
        checks.extend(_check_shell(project_root, shell, index))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--allow-fail", action="store_true")
    args = parser.parse_args()

    try:
        checks = validate(args.project_root, args.profile.resolve())
    except (NavigationShellConfigError, json.JSONDecodeError, OSError) as exc:
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

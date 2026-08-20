#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Ensure that a project resolves a compatible fr_acdd dependency."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from contract_core import has_direct_dependency


MINIMUM_FR_ACDD_VERSION = "0.7.0"


class FrAcddVersionError(ValueError):
    """Raised when fr_acdd cannot be resolved or upgraded compatibly."""


@dataclass(frozen=True)
class ResolvedPackage:
    """One package record reported by Dart Pub."""

    version: str
    source: str


def version_tuple(
    value: str,
) -> tuple[int, int, int, tuple[tuple[int, int | str], ...]]:
    """Parse the SemVer subset emitted by Pub for precedence checks."""

    match = re.fullmatch(
        r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
        r"(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?",
        value.strip(),
    )
    if match is None:
        raise FrAcddVersionError(f"invalid fr_acdd version reported by Pub: {value!r}")
    prerelease: tuple[tuple[int, int | str], ...]
    if match.group(4) is None:
        prerelease = ((2, ""),)
    else:
        identifiers: list[tuple[int, int | str]] = []
        for identifier in match.group(4).split("."):
            identifiers.append(
                (0, int(identifier)) if identifier.isdigit() else (1, identifier)
            )
        prerelease = tuple(identifiers)
    return int(match.group(1)), int(match.group(2)), int(match.group(3)), prerelease


def is_compatible(version: str, minimum: str) -> bool:
    """Return whether a resolved version meets the compatible minimum."""

    return version_tuple(version) >= version_tuple(minimum)


def fvm_executable() -> str:
    """Return the configured FVM executable or fail with actionable guidance."""

    executable = os.environ.get("FR_MVVM_FVM", "fvm")
    if not shutil.which(executable):
        raise FrAcddVersionError(
            f"`{executable}` is not executable; install/configure FVM before "
            "checking fr_acdd"
        )
    return executable


def run_command(command: list[str], package_root: Path) -> subprocess.CompletedProcess[str]:
    """Run one Pub command without mutating the caller's process state."""

    return subprocess.run(
        command,
        cwd=package_root,
        capture_output=True,
        text=True,
        check=False,
    )


def resolved_package(package_root: Path, fvm: str) -> ResolvedPackage | None:
    """Read the resolved fr_acdd package from `dart pub deps --json`."""

    result = run_command([fvm, "dart", "pub", "deps", "--json"], package_root)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise FrAcddVersionError(f"failed to inspect resolved fr_acdd version: {detail}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise FrAcddVersionError(
            "failed to inspect resolved fr_acdd version: Pub returned invalid JSON"
        ) from error
    for package in payload.get("packages", []):
        if package.get("name") == "fr_acdd":
            return ResolvedPackage(
                version=str(package.get("version", "")),
                source=str(package.get("source", "unknown")),
            )
    return None


def is_flutter_package(pubspec: Path) -> bool:
    """Return whether dependencies declare Flutter's SDK in block or flow YAML."""

    text = pubspec.read_text(encoding="utf-8")
    if re.search(
        r"(?ms)^dependencies:\s*\{.*?\bflutter\s*:\s*\{[^}]*\bsdk\s*:\s*flutter\b",
        text,
    ):
        return True
    lines = text.splitlines()
    in_dependencies = False
    for index, line in enumerate(lines):
        if re.match(r"^dependencies:\s*(?:#.*)?$", line):
            in_dependencies = True
            continue
        if in_dependencies and line and not line.startswith((" ", "\t", "#")):
            break
        if not in_dependencies:
            continue
        flutter = re.match(r"^(\s+)flutter\s*:\s*(.*)$", line)
        if flutter is None:
            continue
        indent = len(flutter.group(1).replace("\t", "    "))
        inline = flutter.group(2).split("#", 1)[0].strip()
        if inline:
            return bool(
                re.fullmatch(r"\{\s*sdk\s*:\s*flutter\s*,?\s*\}", inline)
            )
        for child in lines[index + 1 :]:
            if not child.strip() or child.lstrip().startswith("#"):
                continue
            child_indent = len(child) - len(child.lstrip(" \t"))
            if child_indent <= indent:
                break
            if re.match(r"^\s+sdk\s*:\s*flutter\s*(?:#.*)?$", child):
                return True
        return False
    return False


def dependency_source_hint(pubspec: Path) -> str:
    """Infer whether the direct declaration is hosted, path, or git."""

    lines = pubspec.read_text(encoding="utf-8").splitlines()
    in_dependencies = False
    for index, line in enumerate(lines):
        if re.match(r"^dependencies:\s*(?:#.*)?$", line):
            in_dependencies = True
            continue
        if in_dependencies and line and not line.startswith((" ", "\t", "#")):
            break
        dependency_match = re.match(r"^(\s+)fr_acdd\s*:", line)
        if not in_dependencies or dependency_match is None:
            continue
        dependency_indent = len(dependency_match.group(1).replace("\t", "    "))
        inline = line.split(":", 1)[1].strip()
        if inline and not inline.startswith("#"):
            if re.search(r"(?:^|[{,]\s*)path\s*:", inline):
                return "path"
            if re.search(r"(?:^|[{,]\s*)git\s*:", inline):
                return "git"
            return "hosted"
        nested: list[str] = []
        for child in lines[index + 1 :]:
            if not child.strip() or child.lstrip().startswith("#"):
                continue
            child_indent = len(child) - len(child.lstrip(" \t"))
            if child_indent <= dependency_indent:
                break
            nested.append(child)
        block = "\n".join(nested)
        if re.search(r"(?m)^\s+path\s*:", block):
            return "path"
        if re.search(r"(?m)^\s+git\s*:", block):
            return "git"
        return "hosted"
    return "missing"


def pub_command_prefix(pubspec: Path, fvm: str) -> list[str]:
    """Select Flutter Pub for Flutter apps and Dart Pub otherwise."""

    return (
        [fvm, "flutter", "pub"]
        if is_flutter_package(pubspec)
        else [fvm, "dart", "pub"]
    )


def run_upgrade(
    pubspec: Path,
    *,
    minimum: str,
    source: str,
    fvm: str,
) -> None:
    """Attempt the least-destructive compatible Pub upgrade."""

    prefix = pub_command_prefix(pubspec, fvm)
    if source in {"path", "git", "root"}:
        command = [*prefix, "upgrade", "fr_acdd"]
    else:
        command = [*prefix, "add", f"fr_acdd:^{minimum}"]
    result = run_command(command, pubspec.parent)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise FrAcddVersionError(
            f"automatic fr_acdd upgrade failed (`{' '.join(command)}`): {detail}"
        )


def ensure_fr_acdd(
    pubspec: Path,
    *,
    minimum: str = MINIMUM_FR_ACDD_VERSION,
    allow_upgrade: bool = True,
) -> ResolvedPackage:
    """Check fr_acdd and optionally attempt an automatic compatible upgrade."""

    pubspec = pubspec.resolve()
    if not pubspec.is_file():
        raise FrAcddVersionError(f"pubspec.yaml not found: {pubspec}")
    fvm = fvm_executable()
    declared = has_direct_dependency(pubspec, "fr_acdd", section="dependencies")
    source_hint = dependency_source_hint(pubspec)
    try:
        resolved = resolved_package(pubspec.parent, fvm)
    except FrAcddVersionError:
        if not allow_upgrade:
            raise
        get_result = run_command([*pub_command_prefix(pubspec, fvm), "get"], pubspec.parent)
        if get_result.returncode:
            detail = (get_result.stderr or get_result.stdout).strip()
            raise FrAcddVersionError(
                f"failed to resolve dependencies before checking fr_acdd: {detail}"
            )
        resolved = resolved_package(pubspec.parent, fvm)

    if declared and resolved and is_compatible(resolved.version, minimum):
        return resolved

    current = resolved.version if resolved else "not resolved"
    if not declared:
        source = "missing"
    elif source_hint in {"path", "git"}:
        # Preserve the authored direct source even when dependency_overrides
        # causes Pub to report a different resolved source.
        source = source_hint
    elif resolved and resolved.source in {"path", "git", "root"}:
        # A workspace member or override cannot be advanced by rewriting the
        # hosted-looking direct constraint.
        source = resolved.source
    else:
        source = "hosted"
    if not allow_upgrade:
        if not declared:
            raise FrAcddVersionError(
                f"{pubspec} must directly declare fr_acdd >= {minimum} under dependencies"
            )
        raise FrAcddVersionError(
            f"fr_acdd {current} is incompatible; version >= {minimum} is required"
        )

    run_upgrade(pubspec, minimum=minimum, source=source, fvm=fvm)
    upgraded = resolved_package(pubspec.parent, fvm)
    if not has_direct_dependency(pubspec, "fr_acdd", section="dependencies"):
        raise FrAcddVersionError(
            "automatic Pub upgrade completed without adding a direct fr_acdd dependency"
        )
    if upgraded is None or not is_compatible(upgraded.version, minimum):
        upgraded_version = upgraded.version if upgraded else "not resolved"
        raise FrAcddVersionError(
            f"automatic fr_acdd upgrade did not reach >= {minimum} "
            f"(resolved: {upgraded_version}, source: {source}). Update the "
            "workspace/path/git source revision or dependency constraint manually"
        )
    return upgraded


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Package root containing pubspec.yaml (defaults to cwd).",
    )
    parser.add_argument(
        "--minimum",
        default=MINIMUM_FR_ACDD_VERSION,
        help=f"Minimum compatible version (default: {MINIMUM_FR_ACDD_VERSION}).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check only; do not run Pub add/upgrade/get commands.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        resolved = ensure_fr_acdd(
            args.project_root / "pubspec.yaml",
            minimum=args.minimum,
            allow_upgrade=not args.check,
        )
    except FrAcddVersionError as error:
        print(f"fr_acdd: blocked: {error}")
        return 1
    print(
        f"fr_acdd: ready: {resolved.version} "
        f"(source: {resolved.source}, required: >= {args.minimum})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

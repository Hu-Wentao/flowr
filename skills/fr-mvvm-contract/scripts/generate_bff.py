#!/usr/bin/env python3
"""Generate or check the required JSON5 BFF artifact for one component."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

from contract_core import (
    ContractError,
    find_package_pubspec,
    has_direct_dependency,
    require_file,
)
from contract_parser import ComponentContract, parse_component, parse_page


def is_bff_mode(component: ComponentContract) -> bool:
    """Resolve the contract mode, defaulting to BFF unless API is explicit."""

    contract = require_file(Path(component.contract_file), "component contract")
    if "BFF-API" in component.sections or "FrAcddMode.bff" in contract:
        return True
    return "API" not in component.sections


def extractor_command(input_file: Path, output_file: Path) -> list[str]:
    return [
        os.environ.get("FR_MVVM_FVM", "fvm"),
        "dart",
        "run",
        "fr_acdd:extract_bff",
        "--format",
        "json5",
        "--input",
        str(input_file),
        "--output",
        str(output_file),
    ]


def run_extractor_preflight(package_root: Path) -> None:
    fvm = os.environ.get("FR_MVVM_FVM", "fvm")
    if not shutil.which(fvm):
        raise ContractError(
            f"BFF extractor preflight failed: `{fvm}` is not executable; "
            "install/configure FVM before generating BFF artifacts"
        )
    result = subprocess.run(
        [fvm, "dart", "run", "fr_acdd:extract_bff", "--help"],
        cwd=package_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise ContractError(
            "BFF extractor preflight failed. Verify that fr_acdd is compatible "
            f"with the resolved analyzer version.\n{detail}"
        )


def preflight_bff(component: ComponentContract) -> tuple[Path, Path, Path] | None:
    """Validate BFF ownership and extractor availability without writing files."""

    if not is_bff_mode(component):
        return None
    component_file = Path(component.component_file)
    contract_file = Path(component.contract_file)
    output_file = component_file.with_suffix(".bff.md")
    pubspec = find_package_pubspec(component_file)
    if not has_direct_dependency(pubspec, "fr_acdd", section="dependencies"):
        raise ContractError(
            f"{pubspec} must directly declare fr_acdd under dependencies in BFF-JSON mode"
        )
    run_extractor_preflight(pubspec.parent)
    return contract_file, output_file, pubspec.parent


def render_bff(component: ComponentContract) -> tuple[Path, bytes] | None:
    """Render a BFF artifact to memory without changing the component directory."""

    preflight = preflight_bff(component)
    if preflight is None:
        return None
    contract_file, output_file, package_root = preflight
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_file.stem}.", suffix=".md", dir=output_file.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    temporary.unlink()
    try:
        result = subprocess.run(
            extractor_command(contract_file, temporary),
            cwd=package_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode or not temporary.is_file():
            detail = (result.stderr or result.stdout).strip()
            raise ContractError(
                "BFF extraction failed; no artifact was replaced. Verify fr_acdd/analyzer "
                f"compatibility and the contract annotations.\n{detail}"
            )
        return output_file, temporary.read_bytes()
    finally:
        temporary.unlink(missing_ok=True)


def generate_bff(component: ComponentContract, *, check: bool) -> Path | None:
    """Generate atomically, or compare the current artifact with fresh output."""

    expected = Path(component.component_file).with_suffix(".bff.md")
    if check and is_bff_mode(component) and not expected.is_file():
        raise ContractError(f"required BFF artifact does not exist: {expected}")
    output = render_bff(component)
    if output is None:
        return None
    output_file, content = output
    if check:
        if output_file.read_bytes() != content:
            raise ContractError(
                f"BFF artifact is stale: {output_file}; regenerate it with "
                "generate_bff.py"
            )
        return output_file

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_file.stem}.",
        suffix=output_file.suffix,
        dir=output_file.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_bytes(content)
        mode = (
            stat.S_IMODE(output_file.stat().st_mode) if output_file.exists() else 0o644
        )
        temporary.chmod(mode)
        temporary.replace(output_file)
    finally:
        temporary.unlink(missing_ok=True)
    return output_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--page-file", type=Path)
    group.add_argument("--component-file", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        component = (
            parse_page(args.page_file.resolve()).component
            if args.page_file
            else parse_component(args.component_file.resolve())
        )
        output = generate_bff(component, check=args.check)
    except ContractError as error:
        print(f"contract error: {error}", file=sys.stderr)
        return 2
    if output is None:
        print("BFF artifact: not required in explicit API mode")
    else:
        action = "current" if args.check else "generated"
        print(f"BFF artifact {action}: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

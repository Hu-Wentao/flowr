#!/usr/bin/env python3
"""Prepare derived component parts from an approved source contract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from contract_core import ContractError
from contract_parser import ComponentContract, parse_component, parse_page
from generate_bff import generate_bff


def part_path(component: ComponentContract, suffix: str) -> Path:
    shell = Path(component.component_file)
    return shell.with_name(f"{shell.stem}.{suffix}.dart")


def write_stub(path: Path, shell_name: str, force: bool) -> None:
    if path.exists() and not force:
        return
    path.write_text(
        f"part of '{shell_name}';\n\n"
        "// Implement this derived file from read_contract.py output.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--page-file", type=Path)
    group.add_argument("--component-file", type=Path)
    parser.add_argument("--write-stubs", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        component = (
            parse_page(args.page_file.resolve()).component
            if args.page_file
            else parse_component(args.component_file.resolve())
        )
        shell = Path(component.component_file)
        expected = {f"{shell.stem}.v.dart", f"{shell.stem}.vm.dart"}
        missing = expected.difference(component.parts)
        if missing:
            raise ContractError("component shell is missing required parts: " + ", ".join(sorted(missing)))
        if args.write_stubs:
            for suffix in ("v", "vm"):
                write_stub(part_path(component, suffix), shell.name, args.force)
        bff_file = generate_bff(component, check=False)
        print(f"component_file: {component.component_file}")
        print(f"view_file: {part_path(component, 'v')}")
        print(f"view_model_file: {part_path(component, 'vm')}")
        print(f"bff_file: {bff_file or 'not required (API mode)'}")
        print("source: approved contract reader output")
    except ContractError as error:
        print(f"contract error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

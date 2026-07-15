#!/usr/bin/env python3
"""Validate source-first component contracts and optional page adapters."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from contract_core import ContractError, require_file
from contract_parser import parse_component, parse_page


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--page-file", type=Path)
    group.add_argument("--component-file", type=Path)
    args = parser.parse_args()
    try:
        component = parse_page(args.page_file.resolve()).component if args.page_file else parse_component(args.component_file.resolve())
        contract = require_file(Path(component.contract_file), "component contract")
        if "FrProvider" not in contract:
            raise ContractError("XxxView must create its component FrProvider in .c.dart")
        for suffix in ("v", "vm"):
            path = Path(component.component_file).with_name(f"{Path(component.component_file).stem}.{suffix}.dart")
            if path.exists() and f"part of '{Path(component.component_file).name}';" not in require_file(path, f".{suffix}.dart"):
                raise ContractError(f"{path.name} must declare the component shell as part of")
    except ContractError as error:
        print(f"contract error: {error}", file=sys.stderr)
        return 2
    print("contract validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

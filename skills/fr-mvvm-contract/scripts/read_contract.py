#!/usr/bin/env python3
"""Read the stable core facts of a page or reusable component contract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from contract_core import ContractError
from contract_parser import ComponentContract, PageContract, parse_component, parse_page


def print_component(component: ComponentContract) -> None:
    print(f"component_file: {component.component_file}")
    print(f"contract_file: {component.contract_file}")
    print(f"view: {component.view}")
    print("component_input: ordinary View fields")
    print(f"events: {', '.join(component.events) or 'none'}")
    print(f"view_models: {', '.join(component.view_models) or 'none'}")
    print(f"models: {', '.join(component.models) or 'none'}")
    print(f"api.type: {component.api_type or 'missing'}")
    print(f"bff.service: {component.bff_service or 'not declared'}")
    print(f"theme.mode: {component.theme_mode}")
    print(f"theme.type: {component.theme_type or 'none'}")
    print(f"theme.ownership: {component.theme_ownership or 'none'}")
    if component.theme_warning:
        print(f"contract warning: {component.theme_warning}", file=sys.stderr)
    print(f"parts: {', '.join(component.parts)}")
    print(f"imports: {', '.join(component.imports)}")
    for label, lines in component.sections.items():
        print(f"section.{label}: {' | '.join(lines)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--page-file", type=Path)
    group.add_argument("--component-file", type=Path)
    args = parser.parse_args()
    try:
        if args.page_file:
            page: PageContract = parse_page(args.page_file.resolve())
            print(f"page_file: {page.page_file}")
            print(f"page_class: {page.page_class}")
            print(f"page_args: {page.page_args}")
            print(f"primary_view: {page.primary_view}")
            for label, lines in page.sections.items():
                print(f"page_section.{label}: {' | '.join(lines)}")
            print_component(page.component)
        else:
            print_component(parse_component(args.component_file.resolve()))
    except ContractError as error:
        print(f"contract error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

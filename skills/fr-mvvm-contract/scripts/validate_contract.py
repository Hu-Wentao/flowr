#!/usr/bin/env python3
"""Validate source-first component contracts and optional page adapters."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from contract_core import ContractError, require_file
from contract_parser import parse_component, parse_page


JSON_STATE_ANNOTATION = re.compile(r"@FrState(?:Json)?\b")
GENERATED_JSON_FUNCTION = re.compile(
    r"_\$[A-Za-z_][A-Za-z0-9_]*(?:ToJson|FromJson)\s*\("
)
SOURCE_PART_SUFFIXES = ("c", "v", "vm", "srv")


def find_package_pubspec(component_file: Path) -> Path:
    """Return the nearest package manifest that owns the component library."""

    for directory in (component_file.parent, *component_file.parents):
        candidate = directory / "pubspec.yaml"
        if candidate.is_file():
            return candidate
    raise ContractError(
        f"no pubspec.yaml owns {component_file}; add json_serializable to the "
        "owning package dev_dependencies, then run build_runner"
    )


def has_direct_dev_dependency(pubspec: Path, dependency: str) -> bool:
    """Check one directly declared dependency without resolving transitive packages."""

    in_dev_dependencies = False
    for line in pubspec.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[:1].isspace():
            in_dev_dependencies = bool(
                re.match(r"dev_dependencies\s*:\s*(?:#.*)?$", line)
            )
            continue
        if in_dev_dependencies and re.match(rf"\s+{re.escape(dependency)}\s*:", line):
            return True
    return False


def defines_generated_json_function(source: str) -> str | None:
    """Return a generated JSON function name only when it is a definition."""

    for match in GENERATED_JSON_FUNCTION.finditer(source):
        opening = source.find("(", match.start())
        depth = 0
        for index in range(opening, len(source)):
            char = source[index]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    tail = source[index + 1 :].lstrip()
                    if tail.startswith("=>") or tail.startswith("{"):
                        return match.group(0).split("(", 1)[0].strip()
                    break
    return None


def validate_json_generation(component_file: Path) -> None:
    """Validate JSON parts, generator dependency, and generated-code ownership."""

    stem = component_file.stem
    source_paths = [
        component_file.with_name(f"{stem}.{suffix}.dart")
        for suffix in SOURCE_PART_SUFFIXES
    ]
    sources = [require_file(component_file, "component library")]
    sources.extend(
        path.read_text(encoding="utf-8") for path in source_paths if path.is_file()
    )
    uses_json_state = any(JSON_STATE_ANNOTATION.search(source) for source in sources)
    if uses_json_state:
        shell = require_file(component_file, "component library")
        generated_part = f"{stem}.g.dart"
        if not re.search(rf"\bpart\s+['\"]{re.escape(generated_part)}['\"]\s*;", shell):
            raise ContractError(
                f"@FrState/@FrStateJson requires `part '{generated_part}';`; "
                "declare it and run build_runner, never handwrite JSON generator functions"
            )
        pubspec = find_package_pubspec(component_file)
        if not has_direct_dev_dependency(pubspec, "json_serializable"):
            raise ContractError(
                f"{pubspec} must directly declare json_serializable under "
                "dev_dependencies for @FrState/@FrStateJson; add it and run "
                "build_runner, never handwrite JSON generator functions"
            )

    for path in source_paths:
        if not path.is_file():
            continue
        function = defines_generated_json_function(path.read_text(encoding="utf-8"))
        if function:
            raise ContractError(
                f"{path.name} defines generated JSON function {function}; these functions "
                "must not be handwritten and may exist only in the generated .g.dart. "
                "Check json_serializable and the .g.dart part, then run build_runner"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--page-file", type=Path)
    group.add_argument("--component-file", type=Path)
    args = parser.parse_args()
    try:
        component = (
            parse_page(args.page_file.resolve()).component
            if args.page_file
            else parse_component(args.component_file.resolve())
        )
        contract = require_file(Path(component.contract_file), "component contract")
        if "FrProvider" not in contract:
            raise ContractError(
                "XxxView must create its component FrProvider in .c.dart"
            )
        for suffix in ("v", "vm"):
            path = Path(component.component_file).with_name(
                f"{Path(component.component_file).stem}.{suffix}.dart"
            )
            if (
                path.exists()
                and f"part of '{Path(component.component_file).name}';"
                not in require_file(path, f".{suffix}.dart")
            ):
                raise ContractError(
                    f"{path.name} must declare the component shell as part of"
                )
        validate_json_generation(Path(component.component_file))
    except ContractError as error:
        print(f"contract error: {error}", file=sys.stderr)
        return 2
    print("contract validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Prepare derived component parts from an approved source contract."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from contract_core import ContractError, require_file
from contract_parser import ComponentContract, parse_component, parse_page


def snake(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def package_root(component_file: Path) -> Path:
    for directory in (component_file.parent, *component_file.parents):
        if (directory / "pubspec.yaml").is_file():
            return directory
    raise ContractError(f"no pubspec.yaml owns {component_file}")


def add_directive(source: str, directive: str, *, kind: str) -> str:
    if directive in source:
        return source
    matches = list(re.finditer(rf"^\s*{kind}\s+['\"][^'\"]+['\"]\s*;\s*$", source, re.MULTILINE))
    if matches:
        index = matches[-1].end()
        return source[:index] + "\n" + directive + source[index:]
    return directive + "\n" + source


def write_theme_type(path: Path, theme_type: str, *, as_part: str | None = None) -> None:
    if path.exists():
        return
    prefix = (
        f"part of '{as_part}';\n\n"
        if as_part
        else "import 'package:fr_mvvm_theme/fr_mvvm_theme.dart';\n\n"
    )
    path.write_text(
        prefix
        + f"class {theme_type} extends FrPageTheme<{theme_type}> {{\n"
        + f"  const {theme_type}();\n\n"
        + "  @override\n"
        + "  Map<String, dynamic> toJson() => const {};\n"
        + "}\n",
        encoding="utf-8",
    )


def matching_paren(source: str, opening: int) -> int:
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "(":
            depth += 1
        elif source[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    raise ContractError("unterminated AppThemeModel constructor invocation")


def register_app_shared_theme(
    app_theme: Path, theme_file: Path, theme_type: str
) -> None:
    source = require_file(app_theme, "app theme model")
    field = snake(theme_type.removesuffix("Theme")) or "page_theme"
    import_uri = os.path.relpath(theme_file, app_theme.parent).replace(os.sep, "/")
    source = add_directive(source, f"import '{import_uri}';", kind="import")
    class_match = re.search(r"\bclass\s+AppThemeModel\s+extends\s+FrThemeModel\b", source)
    if not class_match:
        raise ContractError("app-shared theme requires AppThemeModel extends FrThemeModel")
    if not re.search(rf"\bfinal\s+{re.escape(theme_type)}\s+{re.escape(field)}\s*;", source):
        override = source.find("@override", class_match.end())
        if override < 0:
            raise ContractError("AppThemeModel must declare toJson()")
        source = source[:override] + f"final {theme_type} {field};\n\n  " + source[override:]
    constructor = re.search(r"\bAppThemeModel\s*\(\{", source[class_match.end():])
    if not constructor:
        raise ContractError("AppThemeModel must use a named-parameter constructor")
    opening = class_match.end() + constructor.start() + constructor.group(0).find("(")
    closing = matching_paren(source, opening)
    parameters = source[opening + 1 : closing]
    if not re.search(rf"\bthis\.{re.escape(field)}\b", parameters):
        named_closing = source.rfind("}", opening + 1, closing)
        if named_closing < 0:
            raise ContractError("AppThemeModel constructor must use named parameters")
        named_parameters = source[opening + 2 : named_closing]
        if "\n" in named_parameters:
            separator = "" if named_parameters.rstrip().endswith(",") else ","
            insertion = f"{separator}\n    required this.{field},\n  "
        else:
            separator = "" if named_parameters.rstrip().endswith(("{", ",")) else ","
            insertion = f"{separator} required this.{field}"
        source = source[:named_closing] + insertion + source[named_closing:]
    method = re.search(
        r"Map<String,\s*dynamic>\s+toJson\(\)\s*=>\s*(?:const\s*)?\{([^}]*)\};",
        source,
        re.DOTALL,
    )
    if not method:
        raise ContractError("AppThemeModel.toJson() must use a map literal")
    if not re.search(rf"['\"]{re.escape(field)}['\"]\s*:\s*{re.escape(field)}\b", method.group(1)):
        entries = method.group(1).strip()
        replacement = "{\n" + (f"    {entries.rstrip(',')},\n" if entries else "")
        replacement += f"    '{field}': {field},\n  }};"
        source = source[: method.start()] + "Map<String, dynamic> toJson() => " + replacement + source[method.end() :]
    built_in = re.search(r"\bAppThemeModel\s*\(", source[method.end():])
    if not built_in:
        raise ContractError("app theme model must declare a built-in AppThemeModel value")
    call_opening = method.end() + built_in.start() + built_in.group(0).rfind("(")
    call_closing = matching_paren(source, call_opening)
    arguments = source[call_opening + 1 : call_closing]
    if not re.search(rf"\b{re.escape(field)}\s*:", arguments):
        if "\n" in arguments:
            separator = "" if arguments.rstrip().endswith(",") else ","
            insertion = f"{separator}\n  {field}: const {theme_type}(),\n"
        else:
            separator = "" if arguments.rstrip().endswith(("(", ",")) else ","
            insertion = f"{separator} {field}: const {theme_type}()"
        source = source[:call_closing] + insertion + source[call_closing:]
    app_theme.write_text(source, encoding="utf-8")


def generate_theme(component: ComponentContract) -> Path | None:
    if component.theme_mode in {"none", "material"}:
        return None
    if component.theme_mode == "legacy":
        raise ContractError(component.theme_warning or "legacy theme contract")
    if not component.theme_type or component.theme_ownership not in {
        "app-shared",
        "component",
    }:
        raise ContractError(
            "fr-mvvm-theme requires a ThemeType and Theme Ownership of app-shared or component"
        )
    shell = Path(component.component_file)
    shell_source = require_file(shell, "component library")
    if component.theme_ownership == "component":
        theme_file = part_path(component, "thm")
        shell_source = add_directive(
            shell_source,
            "import 'package:fr_mvvm_theme/fr_mvvm_theme.dart';",
            kind="import",
        )
        shell_source = add_directive(
            shell_source, f"part '{theme_file.name}';", kind="part"
        )
        shell.write_text(shell_source, encoding="utf-8")
        write_theme_type(theme_file, component.theme_type, as_part=shell.name)
        return theme_file
    root = package_root(shell)
    core = root / "lib/core"
    core.mkdir(parents=True, exist_ok=True)
    theme_file = core / f"{snake(component.theme_type)}.dart"
    write_theme_type(theme_file, component.theme_type)
    import_uri = os.path.relpath(theme_file, shell.parent).replace(os.sep, "/")
    shell_source = add_directive(
        shell_source,
        "import 'package:fr_mvvm_theme/fr_mvvm_theme.dart';",
        kind="import",
    )
    shell_source = add_directive(
        shell_source, f"import '{import_uri}';", kind="import"
    )
    shell.write_text(shell_source, encoding="utf-8")
    register_app_shared_theme(core / "app_theme.dart", theme_file, component.theme_type)
    return theme_file


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
        theme_file = generate_theme(component)
        print(f"component_file: {component.component_file}")
        print(f"view_file: {part_path(component, 'v')}")
        print(f"view_model_file: {part_path(component, 'vm')}")
        if theme_file:
            print(f"theme_file: {theme_file}")
        print("source: approved contract reader output")
    except ContractError as error:
        print(f"contract error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

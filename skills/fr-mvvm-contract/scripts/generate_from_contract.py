#!/usr/bin/env python3
"""Prepare derived component parts from an approved source contract."""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
import tempfile
from pathlib import Path

from contract_core import ContractError, require_file
from contract_parser import ComponentContract, parse_component, parse_page
from generate_bff import render_bff
from generate_service import plan_service
from validate_contract import DERIVED_STUB_MARKER, validate_contract


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
    matches = list(
        re.finditer(rf"^\s*{kind}\s+['\"][^'\"]+['\"]\s*;\s*$", source, re.MULTILINE)
    )
    if matches:
        index = matches[-1].end()
        return source[:index] + "\n" + directive + source[index:]
    return directive + "\n" + source


def theme_type_source(theme_type: str, *, as_part: str | None = None) -> str:
    prefix = (
        f"part of '{as_part}';\n\n"
        if as_part
        else "import 'package:fr_mvvm_theme/fr_mvvm_theme.dart';\n\n"
    )
    return (
        prefix
        + f"class {theme_type} extends FrPageTheme<{theme_type}> {{\n"
        + f"  const {theme_type}();\n\n"
        + "  @override\n"
        + "  Map<String, dynamic> toJson() => const {};\n"
        + "}\n"
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


def app_shared_theme_source(app_theme: Path, theme_file: Path, theme_type: str) -> str:
    source = require_file(app_theme, "app theme model")
    field = snake(theme_type.removesuffix("Theme")) or "page_theme"
    import_uri = os.path.relpath(theme_file, app_theme.parent).replace(os.sep, "/")
    source = add_directive(source, f"import '{import_uri}';", kind="import")
    class_match = re.search(
        r"\bclass\s+AppThemeModel\s+extends\s+FrThemeModel\b", source
    )
    if not class_match:
        raise ContractError(
            "app-shared theme requires AppThemeModel extends FrThemeModel"
        )
    if not re.search(
        rf"\bfinal\s+{re.escape(theme_type)}\s+{re.escape(field)}\s*;", source
    ):
        override = source.find("@override", class_match.end())
        if override < 0:
            raise ContractError("AppThemeModel must declare toJson()")
        source = (
            source[:override] + f"final {theme_type} {field};\n\n  " + source[override:]
        )
    constructor = re.search(r"\bAppThemeModel\s*\(\{", source[class_match.end() :])
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
    if not re.search(
        rf"['\"]{re.escape(field)}['\"]\s*:\s*{re.escape(field)}\b", method.group(1)
    ):
        entries = method.group(1).strip()
        replacement = "{\n" + (f"    {entries.rstrip(',')},\n" if entries else "")
        replacement += f"    '{field}': {field},\n  }};"
        source = (
            source[: method.start()]
            + "Map<String, dynamic> toJson() => "
            + replacement
            + source[method.end() :]
        )
    built_in = re.search(r"\bAppThemeModel\s*\(", source[method.end() :])
    if not built_in:
        raise ContractError(
            "app theme model must declare a built-in AppThemeModel value"
        )
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
    return source


def plan_theme(component: ComponentContract) -> tuple[dict[Path, bytes], Path | None]:
    """Calculate every Theme write and validate its targets without mutation."""

    if component.theme_mode in {"none", "material"}:
        return {}, None
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
    updates: dict[Path, bytes] = {}
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
        updates[shell] = shell_source.encode("utf-8")
        if not theme_file.exists():
            updates[theme_file] = theme_type_source(
                component.theme_type, as_part=shell.name
            ).encode("utf-8")
        return updates, theme_file
    root = package_root(shell)
    core = root / "lib/core"
    theme_file = core / f"{snake(component.theme_type)}.dart"
    if not theme_file.exists():
        updates[theme_file] = theme_type_source(component.theme_type).encode("utf-8")
    import_uri = os.path.relpath(theme_file, shell.parent).replace(os.sep, "/")
    shell_source = add_directive(
        shell_source,
        "import 'package:fr_mvvm_theme/fr_mvvm_theme.dart';",
        kind="import",
    )
    shell_source = add_directive(shell_source, f"import '{import_uri}';", kind="import")
    updates[shell] = shell_source.encode("utf-8")
    app_theme = core / "app_theme.dart"
    updates[app_theme] = app_shared_theme_source(
        app_theme, theme_file, component.theme_type
    ).encode("utf-8")
    return updates, theme_file


def part_path(component: ComponentContract, suffix: str) -> Path:
    shell = Path(component.component_file)
    return shell.with_name(f"{shell.stem}.{suffix}.dart")


def stub_source(shell_name: str) -> bytes:
    return (f"part of '{shell_name}';\n\n{DERIVED_STUB_MARKER}\n").encode("utf-8")


def plan_stub(
    updates: dict[Path, bytes],
    path: Path,
    shell_name: str,
    *,
    replace: bool,
) -> None:
    if not path.exists():
        updates[path] = stub_source(shell_name)
        return
    existing = path.read_text(encoding="utf-8")
    if not replace:
        return
    if DERIVED_STUB_MARKER not in existing:
        raise ContractError(
            f"refusing to replace implemented derived file {path}; only generated "
            "stubs may be refreshed"
        )
    updates[path] = stub_source(shell_name)


def atomic_write(path: Path, content: bytes) -> None:
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_bytes(content)
        temporary.chmod(mode)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def apply_updates(updates: dict[Path, bytes]) -> None:
    """Commit a prepared file set and restore the original set on failure."""

    originals = {
        path: path.read_bytes() if path.is_file() else None for path in updates
    }
    try:
        for path, content in updates.items():
            atomic_write(path, content)
    except Exception as error:
        try:
            for path, original in reversed(list(originals.items())):
                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(path, original)
        except Exception as rollback_error:
            raise ContractError(
                "derived file commit failed and rollback was incomplete: "
                f"{rollback_error}"
            ) from error
        raise ContractError(
            f"derived file commit failed; original files were restored: {error}"
        ) from error


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--page-file", type=Path)
    group.add_argument("--component-file", type=Path)
    parser.add_argument("--write-stubs", action="store_true")
    parser.add_argument(
        "--replace-derived-stubs",
        action="store_true",
        help="refresh existing generated stubs; implemented files are never replaced",
    )
    parser.add_argument("--force", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        page = parse_page(args.page_file.resolve()) if args.page_file else None
        component = (
            page.component if page else parse_component(args.component_file.resolve())
        )
        validate_contract(page, component, phase="contract")
        shell = Path(component.component_file)
        expected = {f"{shell.stem}.v.dart", f"{shell.stem}.vm.dart"}
        missing = expected.difference(component.parts)
        if missing:
            raise ContractError(
                "component shell is missing required parts: "
                + ", ".join(sorted(missing))
            )
        if args.force:
            print(
                "warning: --force is deprecated; only generated stubs may be "
                "refreshed. Use --replace-derived-stubs.",
                file=sys.stderr,
            )

        # Everything below is prepared without mutation. Only a fully successful
        # plan is committed, so extractor or Theme failures leave no partial files.
        updates, theme_file = plan_theme(component)
        rendered_bff = render_bff(component)
        bff_file = None
        service_file = None
        if rendered_bff:
            bff_file, bff_content = rendered_bff
            updates[bff_file] = bff_content
            service_updates, service_file = plan_service(
                component,
                bff_content,
                shell_content=updates.get(shell),
            )
            updates.update(service_updates)
        if args.write_stubs:
            replace = args.replace_derived_stubs or args.force
            for suffix in ("vm", "v"):
                plan_stub(
                    updates,
                    part_path(component, suffix),
                    shell.name,
                    replace=replace,
                )
        apply_updates(updates)
        print(f"component_file: {component.component_file}")
        print(f"view_file: {part_path(component, 'v')}")
        print(f"view_model_file: {part_path(component, 'vm')}")
        print(f"bff_file: {bff_file or 'not required (API mode)'}")
        print(f"service_file: {service_file or 'not required'}")
        if theme_file:
            print(f"theme_file: {theme_file}")
        print("source: approved contract reader output")
    except ContractError as error:
        print(f"contract error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

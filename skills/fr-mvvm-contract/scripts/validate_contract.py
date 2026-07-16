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
PAGE_ARGS_REFERENCE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*PageArgs\b")
STATIC_COLOR_TABLE = re.compile(r"\b(?!Colors\b|CupertinoColors\b)[A-Za-z_][A-Za-z0-9_]*Colors\s*\.")


def find_package_pubspec(component_file: Path) -> Path:
    """Return the nearest package manifest that owns the component library."""

    for directory in (component_file.parent, *component_file.parents):
        candidate = directory / "pubspec.yaml"
        if candidate.is_file():
            return candidate
    raise ContractError(
        f"no pubspec.yaml owns {component_file}; add json_annotation to the "
        "owning package dependencies and json_serializable to dev_dependencies, "
        "then run build_runner"
    )


def has_direct_dependency(pubspec: Path, dependency: str, *, section: str) -> bool:
    """Check one directly declared dependency in the required manifest section."""

    in_section = False
    for line in pubspec.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[:1].isspace():
            in_section = bool(re.match(rf"{section}\s*:\s*(?:#.*)?$", line))
            continue
        if in_section and re.match(rf"\s+{re.escape(dependency)}\s*:", line):
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
        if not has_direct_dependency(
            pubspec, "json_annotation", section="dependencies"
        ):
            raise ContractError(
                f"{pubspec} must directly declare json_annotation under "
                "dependencies for @FrState/@FrStateJson; it is a runtime "
                "dependency and must not be added with --dev"
            )
        if not has_direct_dependency(
            pubspec, "json_serializable", section="dev_dependencies"
        ):
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


def validate_component_input_ownership(component_file: Path) -> None:
    """Keep route-owned PageArgs out of every component-library source file."""

    stem = component_file.stem
    paths = [component_file]
    paths.extend(
        component_file.with_name(f"{stem}.{suffix}.dart")
        for suffix in SOURCE_PART_SUFFIXES
    )
    for path in paths:
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8")
        if ".page.dart" in source:
            raise ContractError(
                f"{path.name} must not import or reference the route adapter .page.dart"
            )
        match = PAGE_ARGS_REFERENCE.search(source)
        if match:
            raise ContractError(
                f"{path.name} references route-owned {match.group(0)}; component "
                "sources may depend only on XxxArgs, XxxConfig, or ordinary inputs"
            )


def validate_page_argument_conversion(
    page_file: Path, page_args: str, view: str
) -> None:
    """Reject passing the route argument object straight through to the View."""

    source = require_file(page_file, "page support")
    field_match = re.search(
        rf"\bfinal\s+{re.escape(page_args)}\s+([A-Za-z_][A-Za-z0-9_]*)\s*;",
        source,
    )
    if not field_match:
        raise ContractError(
            f"page support must own a final {page_args} field before converting it"
        )
    route_value = field_match.group(1)
    call_start = re.search(rf"\b{re.escape(view)}\s*\(", source)
    if not call_start:
        raise ContractError(f"page support must construct its primary view `{view}`")
    opening = source.find("(", call_start.start())
    depth = 0
    closing = None
    for index in range(opening, len(source)):
        if source[index] == "(":
            depth += 1
        elif source[index] == ")":
            depth -= 1
            if depth == 0:
                closing = index
                break
    if closing is None:
        raise ContractError(f"page support has an unterminated `{view}` constructor")
    arguments = source[opening + 1 : closing]
    direct_named = re.search(rf"\bargs\s*:\s*{re.escape(route_value)}\b", arguments)
    direct_positional = re.fullmatch(rf"\s*{re.escape(route_value)}\s*,?\s*", arguments)
    if direct_named or direct_positional:
        raise ContractError(
            f"page support must convert route-owned {page_args} to ordinary View "
            "parameters or component-owned XxxArgs/XxxConfig; do not pass it through"
        )


def dart_sources(package_root: Path) -> list[Path]:
    lib = package_root / "lib"
    return list(lib.rglob("*.dart")) if lib.is_dir() else []


def validate_theme(component_file: Path, component: object) -> None:
    """Validate structured theme schema, generation, registration, and use."""

    mode = component.theme_mode
    ownership = component.theme_ownership
    if mode == "legacy":
        raise ContractError(component.theme_warning or "legacy Theme declaration")
    if mode in {"none", "material"}:
        if ownership:
            raise ContractError(f"Theme Ownership is not valid for Theme: {mode}")
        if mode == "material":
            view = component_file.with_name(f"{component_file.stem}.v.dart")
            view_source = require_file(view, "component view")
            if not re.search(
                r"Theme\.of\s*\(\s*context\s*\)\.colorScheme\b", view_source
            ):
                raise ContractError(
                    "Theme: material must read Theme.of(context).colorScheme in .v.dart"
                )
        return
    theme_type = component.theme_type
    if not theme_type or ownership not in {"app-shared", "component"}:
        raise ContractError(
            "fr-mvvm-theme requires [ThemeType] and Theme Ownership: app-shared|component"
        )
    pubspec = find_package_pubspec(component_file)
    if not has_direct_dependency(pubspec, "fr_mvvm_theme", section="dependencies"):
        raise ContractError(
            f"{pubspec} must directly declare fr_mvvm_theme for Theme: fr-mvvm-theme"
        )
    root = pubspec.parent
    sources = dart_sources(root)
    definition = re.compile(
        rf"\bclass\s+{re.escape(theme_type)}\s+extends\s+FrPageTheme\s*<\s*{re.escape(theme_type)}\s*>"
    )
    if not any(definition.search(path.read_text(encoding="utf-8")) for path in sources):
        raise ContractError(
            f"theme type {theme_type} must extend FrPageTheme<{theme_type}>"
        )
    view = component_file.with_name(f"{component_file.stem}.v.dart")
    view_source = require_file(view, "component view")
    if STATIC_COLOR_TABLE.search(view_source):
        raise ContractError(
            ".v.dart must not statically reference an XxxColors table for a "
            "fr-mvvm-theme contract"
        )
    if not re.search(
        rf"context\.ofThm\s*<\s*{re.escape(theme_type)}\s*>\s*\(\s*\)",
        view_source,
    ):
        raise ContractError(
            f".v.dart must read the active theme with context.ofThm<{theme_type}>()"
        )
    if ownership == "component":
        part_name = f"{component_file.stem}.thm.dart"
        shell = require_file(component_file, "component library")
        if not re.search(rf"\bpart\s+['\"]{re.escape(part_name)}['\"]\s*;", shell):
            raise ContractError(
                f"component theme must be generated as `{part_name}` and added to the shell"
            )
    else:
        app_theme = root / "lib/core/app_theme.dart"
        app_source = require_file(app_theme, "app theme model")
        field_match = re.search(
            rf"\bfinal\s+{re.escape(theme_type)}\s+([A-Za-z_][A-Za-z0-9_]*)\s*;",
            app_source,
        )
        if not field_match:
            raise ContractError(
                f"app-shared {theme_type} must be registered as an AppThemeModel field"
            )
        field = field_match.group(1)
        method = re.search(
            r"Map<String,\s*dynamic>\s+toJson\(\)\s*=>\s*(?:const\s*)?\{([^}]*)\};",
            app_source[field_match.end() :],
            re.DOTALL,
        )
        if not method or not re.search(
            rf"['\"][^'\"]+['\"]\s*:\s*{re.escape(field)}\b", method.group(1)
        ):
            raise ContractError(
                f"AppThemeModel.toJson() must preserve {field} as a FrPageTheme object"
            )
        if not any(
            re.search(
                r"ThemeData\s*\([\s\S]*?extensions\s*:\s*[^,)]*\.extensions\b",
                path.read_text(encoding="utf-8"),
            )
            for path in sources
        ):
            raise ContractError(
                "root ThemeData must inject extensions: theme.data.extensions"
            )
def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--page-file", type=Path)
    group.add_argument("--component-file", type=Path)
    args = parser.parse_args()
    try:
        page = parse_page(args.page_file.resolve()) if args.page_file else None
        component = (
            page.component if page else parse_component(args.component_file.resolve())
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
        component_file = Path(component.component_file)
        validate_component_input_ownership(component_file)
        if page:
            validate_page_argument_conversion(
                Path(page.page_file), page.page_args, page.primary_view
            )
        validate_theme(component_file, component)
        validate_json_generation(component_file)
    except ContractError as error:
        print(f"contract error: {error}", file=sys.stderr)
        return 2
    print("contract validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate source-first component contracts and optional page adapters."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from contract_core import (
    ContractError,
    bracket_refs,
    class_names,
    find_package_pubspec,
    has_direct_dependency,
    require_file,
)
from contract_parser import parse_component, parse_page
from generate_bff import generate_bff, is_bff_mode


JSON_STATE_ANNOTATION = re.compile(r"@FrState(?:Json)?\b")
GENERATED_JSON_FUNCTION = re.compile(
    r"_\$[A-Za-z_][A-Za-z0-9_]*(?:ToJson|FromJson)\s*\("
)
SOURCE_PART_SUFFIXES = ("c", "v", "vm", "srv")
DERIVED_STUB_MARKER = "// Implement this derived file from read_contract.py output."
APPROVAL_PLACEHOLDER = re.compile(r"\b(?:pendingRequestField|pendingResponseField)\b")
PAGE_ARGS_REFERENCE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*PageArgs\b")
COMPONENT_INPUT_WRAPPER = re.compile(
    r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*(?:Args|Config))\b"
)
STATIC_COLOR_TABLE = re.compile(
    r"\b(?!Colors\b|CupertinoColors\b)[A-Za-z_][A-Za-z0-9_]*Colors\s*\."
)
WIDGET_TREE_MAX_KEY_WIDGETS = 12
WIDGET_TREE_FORBIDDEN_WRAPPERS = {
    "Builder",
    "FrConsumer",
    "FrProvider",
}
WIDGET_TREE_FORBIDDEN_GLUE = {
    "Align",
    "DecoratedBox",
    "Divider",
    "Expanded",
    "Flexible",
    "Padding",
    "SafeArea",
    "SizedBox",
    "Spacer",
}
PRIVATE_VIEW_BODY = re.compile(r"^_[A-Za-z_][A-Za-z0-9_]*ViewBody$")


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


def validate_json_generation(
    component_file: Path, *, require_generated_files: bool = False
) -> None:
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
        if require_generated_files:
            for suffix in ("freezed", "g"):
                generated = component_file.with_name(f"{stem}.{suffix}.dart")
                if not generated.is_file():
                    raise ContractError(
                        f"final validation requires generated file {generated.name}; "
                        "run build_runner after handwritten sources are complete"
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
    """Keep route types and structured input wrappers out of component sources."""

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
                "sources must expose ordinary View constructor fields"
            )
        wrapper = COMPONENT_INPUT_WRAPPER.search(source)
        if wrapper:
            raise ContractError(
                f"{path.name} declares component input wrapper {wrapper.group(1)}; "
                "declare ordinary fields directly on XxxView and pass needed values "
                "to XxxViewModel"
            )


def validate_widget_tree(component: object) -> None:
    """Reject deterministic Widget Tree omissions and implementation noise."""

    lines = component.sections.get("Widget Tree")
    if not lines:
        raise ContractError("component contract must declare `Widget Tree:`")
    text = "\n".join(lines).strip()
    if re.search(r"\bTODO\b", text, re.IGNORECASE):
        raise ContractError("Widget Tree must replace TODO before contract approval")
    refs = bracket_refs(lines)
    if not refs or refs[0] != component.view:
        raise ContractError(
            f"Widget Tree root must be the public component view [{component.view}]"
        )
    key_widgets = refs[1:]
    if not key_widgets:
        raise ContractError(
            "Widget Tree must reference key Widgets after its root; do not use only "
            "the root or a natural-language summary"
        )
    view_bodies = sorted(
        {name for name in key_widgets if PRIVATE_VIEW_BODY.fullmatch(name)}
    )
    if view_bodies:
        raise ContractError(
            "Widget Tree must not include formulaic _XxxViewBody wrappers: "
            + ", ".join(view_bodies)
        )
    wrappers = sorted(set(key_widgets).intersection(WIDGET_TREE_FORBIDDEN_WRAPPERS))
    if wrappers:
        raise ContractError(
            "Widget Tree must omit state and implementation wrappers: "
            + ", ".join(wrappers)
        )
    glue = sorted(set(key_widgets).intersection(WIDGET_TREE_FORBIDDEN_GLUE))
    if glue:
        raise ContractError(
            "Widget Tree must omit layout glue and decorative Widgets: "
            + ", ".join(glue)
        )
    if len(key_widgets) > WIDGET_TREE_MAX_KEY_WIDGETS:
        raise ContractError(
            "Widget Tree contains "
            f"{len(key_widgets)} key Widget references; fold it to at most "
            f"{WIDGET_TREE_MAX_KEY_WIDGETS} business-level entries"
        )


def validate_model_names(component: object) -> None:
    """Require component state references to use the XxxModel suffix."""

    if not component.models:
        raise ContractError("component contract must reference at least one state Model")
    invalid = sorted(name for name in component.models if not name.endswith("Model"))
    if invalid:
        raise ContractError(
            "component state classes must use the XxxModel suffix: "
            + ", ".join(invalid)
        )


def annotated_classes(source: str) -> dict[str, str]:
    """Return annotation blocks keyed by the class they immediately annotate."""

    pattern = re.compile(
        r"((?:\s*@(?:[A-Za-z_][A-Za-z0-9_]*)(?:\([^;]*?\))?\s*)+)"
        r"class\s+([A-Za-z_][A-Za-z0-9_]*)\b",
        re.DOTALL,
    )
    return {match.group(2): match.group(1) for match in pattern.finditer(source)}


def validate_bff_contract(
    component, contract: str, *, check_artifact: bool = True
) -> None:
    """Require a complete, reproducible BFF-JSON delivery contract."""

    if not is_bff_mode(component):
        return
    component_file = Path(component.component_file)
    shell = require_file(component_file, "component library")
    if "package:fr_acdd/fr_acdd.dart" not in shell:
        raise ContractError(
            "BFF-JSON component shell must import package:fr_acdd/fr_acdd.dart"
        )
    page_annotations = re.findall(r"@FrAcddPage\s*\((.*?)\)", contract, re.DOTALL)
    if len(page_annotations) != 1 or not re.search(
        r"mode\s*:\s*FrAcddMode\.bff\b", page_annotations[0]
    ):
        raise ContractError(
            "BFF-JSON component must contain exactly one @FrAcddPage(mode: FrAcddMode.bff)"
        )
    annotations = annotated_classes(contract)
    dto_classes = {
        name: block for name, block in annotations.items() if "@FrAcddDto" in block
    }
    roots = [
        name
        for name, block in dto_classes.items()
        if re.search(r"kind\s*:\s*FrAcddDtoKind\.root\b", block)
    ]
    if not roots:
        raise ContractError(
            "BFF-JSON component must define at least one root @FrAcddDto"
        )
    for name, block in dto_classes.items():
        if "@FrAcddFreezedJSON" not in block:
            raise ContractError(f"BFF DTO {name} must use @FrAcddFreezedJSON")
        if not re.search(rf"factory\s+{re.escape(name)}\.fromJson\s*\(", contract):
            raise ContractError(f"BFF DTO {name} must declare factory {name}.fromJson")
    api_lines = component.sections.get("BFF-API", [])
    api_text = "\n".join(api_lines)
    refs = bracket_refs(api_lines)
    if (
        not re.search(r"\b(?:GET|POST|PUT|PATCH|DELETE)\s+\S+", api_text)
        or len(refs) < 2
    ):
        raise ContractError(
            "BFF-API must describe an HTTP method, path, request DTO, and response DTO"
        )
    if len(refs) % 2 != 0:
        raise ContractError(
            "BFF-API must declare request/response DTO references in pairs"
        )
    invalid_requests = sorted(
        {name for name in refs[0::2] if not name.endswith("BffReq")}
    )
    invalid_responses = sorted(
        {name for name in refs[1::2] if not name.endswith("BffRsp")}
    )
    if invalid_requests:
        raise ContractError(
            "BFF request boundary classes must use the XxxBffReq suffix: "
            + ", ".join(invalid_requests)
        )
    if invalid_responses:
        raise ContractError(
            "BFF response boundary classes must use the XxxBffRsp suffix: "
            + ", ".join(invalid_responses)
        )
    names = set(class_names(contract))
    missing_classes = sorted(set(refs).difference(names))
    if missing_classes:
        raise ContractError(
            "BFF-API references undefined DTOs: " + ", ".join(missing_classes)
        )
    missing = sorted(set(refs).difference(dto_classes))
    if missing:
        raise ContractError(
            "BFF-API references classes that are not @FrAcddDto values: "
            + ", ".join(missing)
        )
    internal_dtos = sorted(set(dto_classes).difference(refs))
    invalid_internal = [name for name in internal_dtos if not name.endswith("Dto")]
    if invalid_internal:
        raise ContractError(
            "internal BFF DTO classes must use the XxxDto suffix: "
            + ", ".join(invalid_internal)
        )
    pubspec = find_package_pubspec(component_file)
    if not has_direct_dependency(pubspec, "fr_acdd", section="dependencies"):
        raise ContractError(
            f"{pubspec} must directly declare fr_acdd under dependencies in BFF-JSON mode"
        )
    if check_artifact:
        generate_bff(component, check=True)


def validate_page_argument_conversion(
    page_file: Path,
    page_args: str,
    view: str,
    *,
    require_all_fields: bool = False,
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
            "constructor fields; do not pass it through"
        )
    if not require_all_fields:
        return
    class_match = re.search(rf"\bclass\s+{re.escape(page_args)}\b", source)
    if not class_match:
        raise ContractError(f"page support must declare route-owned {page_args}")
    body_opening = source.find("{", class_match.end())
    if body_opening < 0:
        raise ContractError(f"page support has an unterminated {page_args} class")
    depth = 0
    body_closing = None
    for index in range(body_opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                body_closing = index
                break
    if body_closing is None:
        raise ContractError(f"page support has an unterminated {page_args} class")
    page_arg_body = source[body_opening + 1 : body_closing]
    field_names = re.findall(
        r"\bfinal\s+[^;=\n]+?\s+([A-Za-z_][A-Za-z0-9_]*)\s*;",
        page_arg_body,
    )
    unused = [
        field
        for field in field_names
        if not re.search(
            rf"\b{re.escape(route_value)}\s*\.\s*{re.escape(field)}\b", arguments
        )
    ]
    if unused:
        raise ContractError(
            f"page support does not convert {page_args} fields into {view}: "
            + ", ".join(unused)
        )


def dart_sources(package_root: Path) -> list[Path]:
    lib = package_root / "lib"
    return list(lib.rglob("*.dart")) if lib.is_dir() else []


def validate_theme(
    component_file: Path, component: object, *, require_implementation: bool = True
) -> None:
    """Validate structured theme schema, generation, registration, and use."""

    mode = component.theme_mode
    ownership = component.theme_ownership
    if mode == "legacy":
        raise ContractError(component.theme_warning or "legacy Theme declaration")
    if mode in {"none", "material"}:
        if ownership:
            raise ContractError(f"Theme Ownership is not valid for Theme: {mode}")
        if require_implementation and mode == "material":
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
    if not require_implementation:
        return
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


def validate_approved_contract(contract: str) -> None:
    """Reject generated draft placeholders before derived files are prepared."""

    match = APPROVAL_PLACEHOLDER.search(contract)
    if match:
        raise ContractError(
            f"approved contract still contains draft placeholder `{match.group(0)}`"
        )


def validate_final_files(component_file: Path, component: object) -> None:
    """Require every declared part and reject unfinished derived stubs."""

    for part_name in component.parts:
        if not part_name.endswith(".dart"):
            continue
        path = component_file.parent / part_name
        if not path.is_file():
            raise ContractError(
                f"final validation requires declared part {part_name}; generate it first"
            )
    for suffix in ("v", "vm"):
        path = component_file.with_name(f"{component_file.stem}.{suffix}.dart")
        source = require_file(path, f"component .{suffix} implementation")
        if DERIVED_STUB_MARKER in source:
            raise ContractError(
                f"final validation rejects unfinished derived stub {path.name}"
            )


def validate_contract(page: object | None, component: object, *, phase: str) -> None:
    """Validate a parsed contract at the requested lifecycle phase."""

    contract = require_file(Path(component.contract_file), "component contract")
    if "FrProvider" not in contract:
        raise ContractError("XxxView must create its component FrProvider in .c.dart")
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
    validate_widget_tree(component)
    validate_model_names(component)
    validate_component_input_ownership(component_file)
    if page:
        validate_page_argument_conversion(
            Path(page.page_file),
            page.page_args,
            page.primary_view,
            require_all_fields=phase in {"contract", "final"},
        )
    if phase in {"contract", "final"}:
        validate_approved_contract(contract)
    require_implementation = phase != "contract"
    validate_theme(
        component_file,
        component,
        require_implementation=require_implementation,
    )
    validate_json_generation(component_file, require_generated_files=phase == "final")
    validate_bff_contract(component, contract, check_artifact=phase != "contract")
    if phase == "final":
        validate_final_files(component_file, component)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--page-file", type=Path)
    group.add_argument("--component-file", type=Path)
    parser.add_argument(
        "--phase",
        choices=("source", "contract", "final"),
        default="source",
        help=(
            "source preserves legacy structural validation; contract validates an "
            "approved contract before derivation; final requires all generated parts"
        ),
    )
    args = parser.parse_args()
    try:
        page = parse_page(args.page_file.resolve()) if args.page_file else None
        component = (
            page.component if page else parse_component(args.component_file.resolve())
        )
        validate_contract(page, component, phase=args.phase)
    except ContractError as error:
        print(f"contract error: {error}", file=sys.stderr)
        return 2
    if args.phase == "source":
        print("contract validation: OK")
    else:
        print(f"contract validation ({args.phase}): OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

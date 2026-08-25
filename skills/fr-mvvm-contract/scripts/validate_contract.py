#!/usr/bin/env python3
"""Validate source-first component contracts and optional page adapters."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from contract_core import (
    ContractError,
    IDENTIFIER,
    bracket_refs,
    class_names,
    find_package_pubspec,
    has_direct_dependency,
    require_file,
    validate_leaf_module_directory,
)
from contract_parser import is_api_less_bff, parse_component, parse_page
from figma_contract import parse_figma_contract_nodes
from figma_fill_data import parse_figma_fill_data
from generate_bff import generate_bff, is_bff_mode
from generate_service import contract_endpoints, operation_name
from openapi_refs import (
    DirectBusinessApiRequest,
    generated_sdk_type_fields,
    parse_business_apis,
    validate_backend_calls,
    validate_bff_business_apis,
    validate_direct_business_api_requests,
)
from resolve import (
    load_bff_response_envelope_profile,
    load_request_data_envelope_profile,
)


JSON_STATE_ANNOTATION = re.compile(r"@FrState(?:Json)?\b")
GENERATED_JSON_FUNCTION = re.compile(
    r"_\$[A-Za-z_][A-Za-z0-9_]*(?:ToJson|FromJson)\s*\("
)
SOURCE_PART_SUFFIXES = ("c", "v", "vm", "srv")
DERIVED_STUB_MARKER = "// Implement this derived file from read_contract.py output."
APPROVAL_PLACEHOLDER = re.compile(
    r"\b(?:pendingRequestField|pendingResponseField|TODO|TBD|UNKNOWN)\b"
    r"|<PENDING_[A-Z0-9_]+>",
    re.IGNORECASE,
)
DATA_BOUNDARY_TODO = re.compile(
    r"\bTODO\s*\(\s*data-boundary\s*\)", re.IGNORECASE
)
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
COMMAND_FIELDS = (
    "Effect",
    "Success",
    "Failure",
    "Navigation",
)
QUERY_FIELDS = ("UI Data", "Source", "Loading/Refresh", "Empty/Error")
UI_ONLY_RESPONSE_FIELDS = {
    "buttonlabel",
    "description",
    "message",
    "nextroute",
    "route",
    "subtitle",
    "title",
}
UI_ONLY_RESPONSE_SUFFIXES = (
    "description",
    "label",
    "message",
    "route",
    "screen",
    "subtitle",
    "text",
    "title",
)
COMMAND_EVENT_SUFFIXES = (
    "Submitted",
    "Confirmed",
    "Completed",
    "Requested",
    "Saved",
    "Deleted",
)
QUERY_EVENT_SUFFIXES = ("Started", "Loaded", "Refreshed")
FAILURE_FIELD = re.compile(r"(?:error|failure|validationMessage)$", re.IGNORECASE)


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
    """Keep sibling route types and input wrappers out of component sources."""

    stem = component_file.stem
    page_type = "".join(part.capitalize() for part in stem.split("_")) + "Page"
    sibling_adapter = f"{stem}.page.dart"
    paths = [component_file]
    paths.extend(
        component_file.with_name(f"{stem}.{suffix}.dart")
        for suffix in SOURCE_PART_SUFFIXES
    )
    for path in paths:
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8")
        if sibling_adapter in source:
            raise ContractError(
                f"{path.name} must not import or reference its sibling route "
                f"adapter {sibling_adapter}"
            )
        route_reference = re.search(
            rf"\b(?:{re.escape(page_type)}|GoRouteData|GoRouterState)\b", source
        )
        if route_reference:
            raise ContractError(
                f"{path.name} references route type {route_reference.group(0)}; "
                "component sources must remain independent of their sibling "
                "typed Page and GoRouter state"
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
    if len(component.views) == 1:
        trees = [lines]
    else:
        trees: list[list[str]] = []
        for line in lines:
            if line.startswith("- "):
                trees.append([line.removeprefix("- ").strip()])
            elif trees:
                trees[-1].append(line)
            else:
                raise ContractError(
                    "components with multiple Public Views must declare one "
                    "`Widget Tree` bullet per public View"
                )

    roots: list[str] = []
    for tree in trees:
        refs = bracket_refs(tree)
        if not refs:
            raise ContractError("each Widget Tree entry must begin with a public View")
        roots.append(refs[0])
        key_widgets = refs[1:]
        if not key_widgets:
            raise ContractError(
                "Widget Tree must reference key Widgets after its root; do not use "
                "only the root or a natural-language summary"
            )
        view_bodies = sorted(
            {name for name in key_widgets if PRIVATE_VIEW_BODY.fullmatch(name)}
        )
        if view_bodies:
            raise ContractError(
                "Widget Tree must not include formulaic _XxxViewBody wrappers: "
                + ", ".join(view_bodies)
            )
        wrappers = sorted(
            set(key_widgets).intersection(WIDGET_TREE_FORBIDDEN_WRAPPERS)
        )
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

    if roots != component.views:
        raise ContractError(
            "Widget Tree roots must match `Public Views:` in order; expected "
            + ", ".join(f"[{view}]" for view in component.views)
            + ", found "
            + ", ".join(f"[{root}]" for root in roots)
        )


def validate_model_names(component: object) -> None:
    """Require component state references to use the XxxModel suffix."""

    if not component.models:
        if component.state_ownership in {"page-owned", "component-owned"}:
            raise ContractError(
                f"{component.state_ownership} contract must reference at least "
                "one state Model"
            )
        return
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
        r"(?:(?:abstract|base|final|interface|sealed)\s+)*"
        r"class\s+([A-Za-z_][A-Za-z0-9_]*)\b",
        re.DOTALL,
    )
    return {match.group(2): match.group(1) for match in pattern.finditer(source)}


def matching_delimiter(
    source: str, opening: int, open_char: str, close_char: str
) -> int:
    """Return the matching delimiter while ignoring quoted Dart text."""

    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(opening, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return index
    raise ContractError(f"unterminated {open_char}{close_char} region")


def class_body(source: str, class_name: str) -> str:
    """Return a Dart class body for source-level contract checks."""

    match = re.search(
        rf"\bclass\s+{re.escape(class_name)}\b[^{{]*{{",
        source,
    )
    if match is None:
        raise ContractError(f"Dart class {class_name} is not declared")
    opening = source.find("{", match.start())
    closing = matching_delimiter(source, opening, "{", "}")
    return source[opening + 1 : closing]


def split_top_level(value: str, delimiter: str = ",") -> list[str]:
    """Split a Dart parameter list without splitting nested expressions."""

    parts: list[str] = []
    start = 0
    stack: list[str] = []
    pairs = {"(": ")", "[": "]", "{": "}", "<": ">"}
    quote: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
        elif char in pairs:
            stack.append(pairs[char])
        elif stack and char == stack[-1]:
            stack.pop()
        elif char == delimiter and not stack:
            parts.append(value[start:index].strip())
            start = index + 1
    tail = value[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def factory_parameters(source: str, class_name: str) -> list[str]:
    """Read named parameters from the conventional Freezed factory declaration."""

    match = re.search(rf"\bfactory\s+{re.escape(class_name)}\s*\(", source)
    if not match:
        raise ContractError(f"DTO {class_name} must declare a factory constructor")
    opening = source.find("(", match.start())
    closing = matching_delimiter(source, opening, "(", ")")
    parameters = source[opening + 1 : closing].strip()
    if parameters.startswith("{") and parameters.endswith("}"):
        parameters = parameters[1:-1]
    elif parameters:
        raise ContractError(
            f"DTO {class_name} factory must use named request/response fields"
        )
    return split_top_level(parameters)


def factory_fields(source: str, class_name: str) -> list[str]:
    """Read named fields from the conventional Freezed factory declaration."""

    fields: list[str] = []
    for parameter in factory_parameters(source, class_name):
        declaration = parameter.split("=", 1)[0]
        identifiers = re.findall(IDENTIFIER, declaration)
        if not identifiers:
            raise ContractError(
                f"cannot parse DTO field in {class_name}: {parameter.strip()}"
            )
        fields.append(identifiers[-1])
    return fields


def factory_field_type(source: str, class_name: str, field: str) -> str | None:
    """Return the simple Dart type immediately preceding one factory field."""

    for parameter in factory_parameters(source, class_name):
        declaration = parameter.split("=", 1)[0].strip()
        match = re.search(
            rf"\b({IDENTIFIER}\??)\s+{re.escape(field)}\s*$", declaration
        )
        if match:
            return match.group(1)
    return None


def _top_level_prefix(value: str, delimiter: str) -> str:
    """Return text before the first top-level delimiter."""

    stack: list[str] = []
    pairs = {"(": ")", "[": "]", "{": "}", "<": ">"}
    quote: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
        elif char in pairs:
            stack.append(pairs[char])
        elif stack and char == stack[-1]:
            stack.pop()
        elif char == delimiter and not stack:
            return value[:index]
    return value


def _strip_leading_annotations(value: str) -> str:
    """Strip metadata annotations before one Dart enum value."""

    remaining = value.strip()
    while remaining.startswith("@"):
        annotation = re.match(
            rf"@{IDENTIFIER}(?:\s*\.\s*{IDENTIFIER})*", remaining
        )
        if annotation is None:
            break
        offset = annotation.end()
        tail = remaining[offset:].lstrip()
        if tail.startswith("<"):
            closing = matching_delimiter(tail, 0, "<", ">")
            tail = tail[closing + 1 :].lstrip()
        if tail.startswith("("):
            closing = matching_delimiter(tail, 0, "(", ")")
            tail = tail[closing + 1 :].lstrip()
        remaining = tail
    return remaining


def enum_members(source: str, enum_type: str) -> set[str]:
    """Return legal value members of one documented or annotated Dart enum."""

    masked = _mask_comments_and_strings(source)
    match = re.search(rf"\benum\s+{re.escape(enum_type)}\s*\{{", masked)
    if match is None:
        return set()
    opening = masked.find("{", match.start())
    closing = matching_delimiter(masked, opening, "{", "}")
    values_region = _top_level_prefix(masked[opening + 1 : closing], ";")
    members: set[str] = set()
    for entry in split_top_level(values_region):
        identifier = re.match(
            rf"({IDENTIFIER})\b", _strip_leading_annotations(entry)
        )
        if identifier:
            members.add(identifier.group(1))
    return members


def section_bullets(
    component: object, section: str, required: tuple[str, ...]
) -> dict[str, str]:
    """Parse one structured doc section with continued bullet values."""

    lines = component.sections.get(section, [])
    if not lines:
        raise ContractError(f"contract must declare `{section}:`")
    bullets: dict[str, str] = {}
    current: str | None = None
    for line in lines:
        match = re.match(r"^-\s*([^:]+):\s*(.*)$", line)
        if match:
            current = match.group(1).strip()
            if current in bullets:
                raise ContractError(f"{section} contains duplicate `{current}`")
            bullets[current] = match.group(2).strip()
        elif current:
            bullets[current] = f"{bullets[current]} {line}".strip()
        else:
            raise ContractError(f"{section} entries must use `- Field: value`: {line}")
    missing = [name for name in required if not bullets.get(name)]
    if missing:
        raise ContractError(
            f"{section} must define non-empty fields: {', '.join(missing)}"
        )
    extras = sorted(set(bullets).difference(required))
    if extras:
        raise ContractError(
            f"{section} contains unsupported fields: {', '.join(extras)}"
        )
    for name, value in bullets.items():
        if APPROVAL_PLACEHOLDER.search(value):
            raise ContractError(f"{section} `{name}` still contains a placeholder")
    return bullets


def request_field_sources(component: object) -> dict[str, tuple[str, str]]:
    """Parse `field <- source | purpose` request provenance entries."""

    lines = component.sections.get("Request Field Sources", [])
    if not lines:
        raise ContractError("BFF contract must declare `Request Field Sources:`")
    entries: list[str] = []
    for line in lines:
        if line.startswith("-"):
            entries.append(line[1:].strip())
        elif entries:
            entries[-1] = f"{entries[-1]} {line}".strip()
        else:
            raise ContractError("Request Field Sources entries must start with `-`")
    if entries == ["none"]:
        return {}
    parsed: dict[str, tuple[str, str]] = {}
    for entry in entries:
        match = re.fullmatch(rf"({IDENTIFIER})\s*<-\s*(.+?)\s*\|\s*(.+)", entry)
        if not match:
            raise ContractError(
                "Request Field Sources entries must use "
                "`- field <- authoritative source | UI API purpose`"
            )
        field, source, purpose = (part.strip() for part in match.groups())
        if field in parsed:
            raise ContractError(f"Request Field Sources contains duplicate `{field}`")
        if APPROVAL_PLACEHOLDER.search(source + " " + purpose):
            raise ContractError(
                f"request field `{field}` source or purpose is still pending"
            )
        parsed[field] = (source, purpose)
    return parsed


def api_operation(component: object) -> tuple[str, str]:
    """Return the contract HTTP method and path."""

    lines = component.sections.get("BFF-UI-API") or component.sections.get("API") or []
    match = re.search(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(\S+)", "\n".join(lines))
    if not match:
        raise ContractError("API contract must declare an HTTP method and path")
    method, path = match.groups()
    if path.rstrip("/").endswith("/bootstrap"):
        raise ContractError(
            "API path must describe the approved operation; `/bootstrap` is a "
            "forbidden generated placeholder"
        )
    return method, path


def direct_business_request_boundaries(
    component: object, contract: str
) -> tuple[DirectBusinessApiRequest, ...]:
    """Resolve UI endpoints that reuse an exact backend method/path boundary."""

    component_file = Path(component.component_file)
    bff_file = component_file.with_suffix(".bff.md")
    if not bff_file.is_file():
        return ()
    bff_content = require_file(bff_file, "BFF artifact")
    if (
        "## 后端业务流程与业务逻辑 API" not in bff_content
        or "## 前端 UI 数据接口" not in bff_content
    ):
        return ()
    calls, _ = parse_business_apis(bff_content)
    if not calls:
        return ()
    endpoints = tuple(
        (endpoint.method, endpoint.path, endpoint.request_type)
        for endpoint in contract_endpoints(component)
    )
    source_paths = (
        component_file,
        component_file.with_name(f"{component_file.stem}.srv.dart"),
    )
    dart_sources = (contract,) + tuple(
        require_file(path, "direct backend API typedef source")
        for path in source_paths
        if path.is_file()
    )
    return validate_direct_business_api_requests(
        calls, endpoints, dart_sources=dart_sources
    )


def validate_failure_cases(value: str) -> None:
    """Require every command failure to name an App recovery/display action."""

    cases = [item.strip() for item in value.split(";") if item.strip()]
    if not cases or any(
        "->" not in item
        or not item.split("->", 1)[0].strip()
        or not item.split("->", 1)[1].strip()
        for item in cases
    ):
        raise ContractError(
            "Command `Failure` must use `error -> App recovery/display` "
            "for every semicolon-separated failure"
        )


def is_ui_only_response_field(field: str) -> bool:
    """Identify navigation and display-only response names conservatively."""

    lowered = field.lower()
    return lowered in UI_ONLY_RESPONSE_FIELDS or lowered.endswith(
        UI_ONLY_RESPONSE_SUFFIXES
    )


def _legacy_api_kind(component: object) -> str | None:
    """Infer explicit-API query/command kind without applying the BFF v9 grammar."""

    labels = {
        match.group(1).strip()
        for line in component.sections.get("Behavior", [])
        if (match := re.match(r"^-\s*([^:]+):", line))
    }
    has_query = bool(labels.intersection(QUERY_FIELDS))
    has_command = bool(labels.intersection(COMMAND_FIELDS))
    if has_query and has_command:
        return "mixed"
    if has_query:
        return "query"
    if has_command:
        return "command"
    return None


def _model_fields(component: object, contract: str) -> dict[str, set[str]]:
    return {model: set(factory_fields(contract, model)) for model in component.models}


def _validate_interaction_contract(component: object, contract: str) -> None:
    """Validate every typed Flow against Events, Widgets, Models, and endpoint behavior."""

    models = _model_fields(component, contract)
    widget_tree = component.sections.get("Widget Tree")
    widgets = set(bracket_refs(widget_tree or []))
    startup_events = set(bracket_refs(component.sections.get("Startup Event", [])))
    behaviors = {behavior.endpoint: behavior for behavior in component.behaviors}
    endpoints = {endpoint.request_type: endpoint for endpoint in component.endpoints}
    navigation_signal_owners: dict[object, object] = {}
    runtime_signal_fields: dict[str, object] = {}
    for flow in component.interactions:
        signal = flow.navigation_signal
        if signal is None:
            continue
        prior = navigation_signal_owners.get(signal)
        if prior is not None:
            raise ContractError(
                f"Navigation signal [{signal.type_name}].{signal.field} must be "
                f"owned by exactly one Flow; found `{prior.flow}` and `{flow.flow}`"
            )
        prior_field = runtime_signal_fields.get(signal.field)
        if prior_field is not None:
            raise ContractError(
                f"Navigation signal runtime field `{signal.field}` is ambiguous "
                f"between Flows `{prior_field.flow}` and `{flow.flow}`"
            )
        navigation_signal_owners[signal] = flow
        runtime_signal_fields[signal.field] = flow

    def require_model_field(flow: str, phase: str, reference: object) -> None:
        fields = models.get(reference.type_name)
        if fields is None:
            raise ContractError(
                f"Interaction Flow `{flow}` {phase} references undeclared Model "
                f"[{reference.type_name}]"
            )
        if reference.field not in fields:
            raise ContractError(
                f"Interaction Flow `{flow}` {phase} references unknown field "
                f"[{reference.type_name}].{reference.field}"
            )

    for flow in component.interactions:
        if flow.event not in component.events:
            raise ContractError(
                f"Interaction Flow `{flow.flow}` Event [{flow.event}] is not declared "
                "under Events"
            )
        if flow.trigger == "startup" and flow.event not in startup_events:
            raise ContractError(
                f"Interaction Flow `{flow.flow}` startup Event [{flow.event}] must "
                "match Startup Event"
            )
        if flow.trigger != "startup" and flow.event in startup_events:
            raise ContractError(
                f"Interaction Flow `{flow.flow}` uses Startup Event [{flow.event}] "
                "from a non-startup trigger"
            )
        if widget_tree is not None and flow.trigger_widget and flow.trigger_widget not in widgets:
            raise ContractError(
                f"Interaction Flow `{flow.flow}` trigger Widget "
                f"[{flow.trigger_widget}] is missing from legacy Widget Tree"
            )
        if flow.guard_value:
            require_model_field(flow.flow, "Guard", flow.guard_value.reference)
        phases = (
            ("Pending State", flow.pending_mutations),
            ("Success State", flow.success_mutations),
            ("Failure State", flow.failure_mutations),
        )
        for phase, mutations in phases:
            for mutation in mutations:
                owner = navigation_signal_owners.get(mutation.target)
                if owner is not None and owner.flow != flow.flow:
                    raise ContractError(
                        f"Interaction Flow `{flow.flow}` {phase} must not write "
                        f"navigation signal [{mutation.target.type_name}]."
                        f"{mutation.target.field} owned by Flow `{owner.flow}`"
                    )
                require_model_field(flow.flow, phase, mutation.target)
                if mutation.source:
                    if mutation.source.type_name in models:
                        require_model_field(flow.flow, phase, mutation.source)
                    elif flow.endpoint is None:
                        raise ContractError(
                            f"Interaction Flow `{flow.flow}` local {phase} cannot "
                            f"reference response [{mutation.source.type_name}]"
                        )
                    else:
                        endpoint = endpoints[flow.endpoint]
                        if mutation.source.type_name != endpoint.response_type:
                            raise ContractError(
                                f"Interaction Flow `{flow.flow}` {phase} must map from "
                                f"[{endpoint.response_type}], not "
                                f"[{mutation.source.type_name}]"
                            )
                        response_fields = set(
                            factory_fields(contract, endpoint.response_type)
                        )
                        if mutation.source.field not in response_fields:
                            raise ContractError(
                                f"Interaction Flow `{flow.flow}` {phase} references "
                                f"unknown response field [{endpoint.response_type}]."
                                f"{mutation.source.field}"
                            )
                if phase == "Pending State" and mutation.source:
                    raise ContractError(
                        f"Interaction Flow `{flow.flow}` Pending State cannot read a "
                        "response before the API call"
                    )
                if phase != "Failure State" and mutation.value == "error":
                    raise ContractError(
                        f"Interaction Flow `{flow.flow}` may map `error` only in "
                        "Failure State"
                    )
                if (
                    phase == "Failure State"
                    and mutation.operator == "<-"
                    and mutation.value != "error"
                ):
                    raise ContractError(
                        f"Interaction Flow `{flow.flow}` Failure State mappings "
                        "may read only `error`"
                    )
        signal = flow.navigation_signal
        enum_type = flow.navigation_enum
        enum_member = flow.navigation_member
        if signal is not None:
            assert enum_type is not None and enum_member is not None
            require_model_field(flow.flow, "Navigation", signal)
            declared_type = factory_field_type(contract, signal.type_name, signal.field)
            if declared_type != f"{enum_type}?":
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` Navigation signal "
                    f"[{signal.type_name}].{signal.field} must have nullable "
                    f"semantic enum type `{enum_type}?`; found "
                    f"`{declared_type or 'unresolved'}`"
                )
            if enum_member not in enum_members(contract, enum_type):
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` Navigation references "
                    f"undeclared enum member {enum_type}.{enum_member}"
                )
            pending_writes = [
                mutation
                for mutation in flow.pending_mutations
                if mutation.target == signal
            ]
            success_writes = [
                mutation
                for mutation in flow.success_mutations
                if mutation.target == signal
            ]
            failure_writes = [
                mutation
                for mutation in flow.failure_mutations
                if mutation.target == signal
            ]
            if not (
                len(pending_writes) == 1
                and pending_writes[0].operator == "="
                and pending_writes[0].value == "null"
            ):
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` Pending State must reset "
                    f"[{signal.type_name}].{signal.field} = null and write only "
                    "that value for its navigation signal"
                )
            if not (
                len(success_writes) == 1
                and success_writes[0].operator == "="
                and success_writes[0].value == f"{enum_type}.{enum_member}"
            ):
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` Success State must write only "
                    f"[{signal.type_name}].{signal.field} = "
                    f"{enum_type}.{enum_member} for its navigation signal"
                )
            if failure_writes:
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` Navigation signal may be "
                    "emitted only from Success State; Failure State must not "
                    f"write [{signal.type_name}].{signal.field}"
                )
        if flow.endpoint is None:
            if signal is not None:
                business_success = tuple(
                    mutation
                    for mutation in flow.success_mutations
                    if mutation.target != signal
                )
                if not business_success:
                    raise ContractError(
                        f"Interaction Flow `{flow.flow}` Uses: local navigation must "
                        "also own a non-navigation Success State decision; direct "
                        "presentation routing belongs in the View with no Flow"
                    )
                no_op = next(
                    (
                        mutation
                        for mutation in business_success
                        if _is_obvious_state_self_assignment(mutation)
                    ),
                    None,
                )
                if no_op is not None:
                    raise ContractError(
                        f"Interaction Flow `{flow.flow}` Uses: local navigation "
                        f"non-navigation Success mutation "
                        f"[{no_op.target.type_name}].{no_op.target.field} = "
                        f"{no_op.value} is an obvious no-op self-assignment; "
                        "declare a real ViewModel-owned state/business decision"
                    )
            continue
        behavior = behaviors[flow.endpoint]
        endpoint = endpoints[flow.endpoint]
        response_mappings = [
            mutation
            for mutation in flow.success_mutations
            if mutation.source
            and mutation.source.type_name == endpoint.response_type
        ]
        if not response_mappings:
            raise ContractError(
                f"Interaction Flow `{flow.flow}` Success State must map at least "
                f"one [{endpoint.response_type}] field into frontend state"
            )
        if behavior.kind == "query":
            if flow.navigation != "none":
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` query endpoint [{flow.endpoint}] "
                    "must declare Navigation: none"
                )
            if flow.concurrency != "latest-wins":
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` query endpoint "
                    f"[{flow.endpoint}] must declare Concurrency: latest-wins"
                )
        if behavior.kind == "command":
            if behavior.navigation == "none" and flow.navigation != "none":
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` Navigation `{flow.navigation}` "
                    f"does not match command Behavior [{flow.endpoint}] Navigation "
                    "`none`"
                )
            if behavior.navigation == "app" and signal is None:
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` command Behavior navigation "
                    "`app` requires `Navigation: view-listener-on-success "
                    "[Model].field = Enum.member`"
                )
        if flow.concurrency == "ignore-while-active":
            if flow.guard_value is None:
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` ignore-while-active requires "
                    "a boolean Guard"
                )
            guard = flow.guard_value
            active = "false" if guard.expected else "true"
            reset = "true" if guard.expected else "false"
            for label, mutations, expected in (
                ("Pending State", flow.pending_mutations, active),
                ("Success State", flow.success_mutations, reset),
                ("Failure State", flow.failure_mutations, reset),
            ):
                if not any(
                    mutation.target == guard.reference
                    and mutation.operator == "="
                    and mutation.value == expected
                    for mutation in mutations
                ):
                    raise ContractError(
                        f"Interaction Flow `{flow.flow}` {label} must set Guard "
                        f"field [{guard.reference.type_name}].{guard.reference.field} "
                        f"to {expected}"
                    )


def validate_api_semantics(component: object, contract: str) -> None:
    """Enforce explicit API semantics and the breaking BFF v9 endpoint/Flow model."""

    has_bff = "BFF-UI-API" in component.sections
    has_explicit_api = "API" in component.sections
    if not has_bff and not has_explicit_api:
        forbidden = sorted(
            name
            for name in (
                "Behavior",
                "Behaviors",
                "Interactions",
                "Request Field Sources",
                "BFF Service",
            )
            if name in component.sections
        )
        if forbidden:
            raise ContractError(
                "local component contract must not declare API-only sections: "
                + ", ".join(forbidden)
            )
        return
    if has_bff and has_explicit_api:
        raise ContractError("a component contract must not mix `API:` and `BFF-UI-API:`")
    if has_explicit_api:
        bff_only = sorted(
            name
            for name in (
                "Behaviors",
                "Interactions",
                "Request Field Sources",
                "BFF Service",
            )
            if name in component.sections
        )
        if bff_only:
            raise ContractError(
                "explicit `API:` mode must not declare BFF-only sections: "
                + ", ".join(bff_only)
            )
    if "API Type" in component.sections:
        raise ContractError(
            "API Type is obsolete; describe semantics with Behavior/Behaviors"
        )
    legacy_sections = sorted(
        name for name in ("Data", "Business") if name in component.sections
    )
    if legacy_sections:
        raise ContractError(
            "legacy semantic sections are obsolete: " + ", ".join(legacy_sections)
        )
    validate_backend_calls(component)

    if has_explicit_api:
        api_kind = _legacy_api_kind(component)
        if api_kind == "mixed":
            raise ContractError("Behavior must describe either a query or a command")
        if api_kind not in {"query", "command"}:
            raise ContractError(
                "Behavior must contain the complete query or command field set"
            )
        method, _ = api_operation(component)
        fields = QUERY_FIELDS if api_kind == "query" else COMMAND_FIELDS
        behavior = section_bullets(component, "Behavior", fields)
        if api_kind == "query" and method in {"PUT", "PATCH", "DELETE"}:
            raise ContractError(f"query cannot use state-changing HTTP method {method}")
        if api_kind == "command":
            if method == "GET":
                raise ContractError("command cannot use GET")
            if behavior["Navigation"] not in {"app", "none"}:
                raise ContractError("Command `Navigation` must be `app` or `none`")
            validate_failure_cases(behavior["Failure"])
        return

    if "BFF Runtime" in component.sections:
        raise ContractError(
            "BFF Runtime is obsolete; declare `BFF Service: [Type]`"
        )
    _validate_interaction_contract(component, contract)
    if is_api_less_bff(component):
        return
    if not re.fullmatch(rf"\[({IDENTIFIER})\]", component.bff_service or ""):
        raise ContractError(
            "BFF v9 requires `BFF Service: [Type]`; contract-only delivery is "
            "not supported"
        )
    direct_requests = {
        boundary.request_type: boundary.sdk_request_type
        for boundary in direct_business_request_boundaries(component, contract)
    }
    behavior_by_endpoint = {
        behavior.endpoint: behavior for behavior in component.behaviors
    }
    sources_by_endpoint = {
        source.endpoint: {field.field for field in source.fields}
        for source in component.request_sources
    }
    for endpoint in component.endpoints:
        behavior = behavior_by_endpoint[endpoint.request_type]
        if endpoint.path.rstrip("/").endswith("/bootstrap"):
            raise ContractError(
                f"endpoint [{endpoint.request_type}] path uses forbidden generated "
                "placeholder `/bootstrap`"
            )
        if behavior.kind == "query" and endpoint.method in {"PUT", "PATCH", "DELETE"}:
            raise ContractError(
                f"endpoint [{endpoint.request_type}] query cannot use "
                f"state-changing method {endpoint.method}"
            )
        if behavior.kind == "command":
            if endpoint.method == "GET":
                raise ContractError(
                    f"endpoint [{endpoint.request_type}] command cannot use GET"
                )
            if behavior.navigation not in {"app", "none"}:
                raise ContractError(
                    f"endpoint [{endpoint.request_type}] command Navigation must be "
                    "`app` or `none`"
                )
            validate_failure_cases(behavior.failure or "")
        request_fields = set(
            generated_sdk_type_fields(
                Path(component.component_file), direct_requests[endpoint.request_type]
            )
            if endpoint.request_type in direct_requests
            else factory_fields(contract, endpoint.request_type)
        )
        declared_sources = sources_by_endpoint[endpoint.request_type]
        missing = sorted(request_fields - declared_sources)
        unknown = sorted(declared_sources - request_fields)
        if missing:
            raise ContractError(
                f"endpoint [{endpoint.request_type}] request fields missing source "
                "and purpose: " + ", ".join(missing)
            )
        if unknown:
            raise ContractError(
                f"endpoint [{endpoint.request_type}] Request Field Sources references "
                "unknown fields: " + ", ".join(unknown)
            )
        if behavior.kind != "command":
            continue
        response_fields = factory_fields(contract, endpoint.response_type)
        result_fields = [
            field for field in response_fields if not is_ui_only_response_field(field)
        ]
        if not result_fields:
            raise ContractError(
                f"endpoint [{endpoint.request_type}] command response "
                f"{endpoint.response_type} contains only UI/navigation fields"
            )
        if not any(
            re.search(rf"\b{re.escape(field)}\b", behavior.success or "")
            for field in result_fields
        ):
            raise ContractError(
                f"endpoint [{endpoint.request_type}] Success must reference a non-UI "
                f"field in {endpoint.response_type}: {', '.join(result_fields)}"
            )


def declared_service_field(vm_source: str, vm_class: str, service_type: str) -> str:
    """Return the injected service field name from the ViewModel constructor."""

    fields = re.findall(
        rf"\bfinal\s+{re.escape(service_type)}\s+({IDENTIFIER})\s*;", vm_source
    )
    if not fields:
        raise ContractError(
            f"ViewModel must retain injected {service_type} in a final field"
        )
    constructor = re.search(rf"\b{re.escape(vm_class)}\s*\(", vm_source)
    if not constructor:
        raise ContractError(f"ViewModel must declare {vm_class}(...) constructor")
    opening = vm_source.find("(", constructor.start())
    closing = matching_delimiter(vm_source, opening, "(", ")")
    parameters = vm_source[opening + 1 : closing]
    for field in fields:
        if re.search(rf"\bthis\.{re.escape(field)}\b", parameters):
            return field
        parameter = re.search(
            rf"\b{re.escape(service_type)}\s+({IDENTIFIER})\b", parameters
        )
        if parameter and re.search(
            rf"\b{re.escape(field)}\s*=\s*{re.escape(parameter.group(1))}\b",
            vm_source[closing : closing + 300],
        ):
            return field
    raise ContractError(
        f"{vm_class} constructor must receive and retain {service_type}"
    )


def registered_flow_handler(vm_source: str, flow: object) -> tuple[str, str]:
    """Return one Flow's exact Event handler and complete registration arguments."""

    matches = list(
        re.finditer(
            rf"\bon\s*<\s*{re.escape(flow.event)}\s*>\s*\(", vm_source
        )
    )
    if len(matches) != 1:
        raise ContractError(
            f"Interaction Flow `{flow.flow}` must register Event [{flow.event}] "
            f"exactly once; found {len(matches)}"
        )
    opening = vm_source.find("(", matches[0].start())
    closing = matching_delimiter(vm_source, opening, "(", ")")
    arguments = vm_source[opening + 1 : closing]
    handler = re.match(rf"\s*({IDENTIFIER})", arguments)
    if handler is None:
        raise ContractError(
            f"Interaction Flow `{flow.flow}` Event [{flow.event}] must use a named "
            "handler"
        )
    return handler.group(1), arguments


def function_body_region(source: str, name: str) -> tuple[str, str, int, int]:
    """Return a named function signature, body, and absolute body offsets."""

    for match in re.finditer(rf"\b{re.escape(name)}\s*\(", source):
        opening = source.find("(", match.start())
        closing = matching_delimiter(source, opening, "(", ")")
        brace = source.find("{", closing)
        semicolon = source.find(";", closing)
        if brace < 0 or (semicolon >= 0 and semicolon < brace):
            continue
        signature_start = max(source.rfind("\n", 0, match.start()), 0)
        signature = source[signature_start:brace]
        body_end = matching_delimiter(source, brace, "{", "}")
        return signature, source[brace + 1 : body_end], brace + 1, body_end
    raise ContractError(f"registered handler `{name}` must have a block body")


def function_body(source: str, name: str) -> tuple[str, str]:
    """Return a named Dart function signature tail and brace body."""

    signature, body, _, _ = function_body_region(source, name)
    return signature, body


def _is_raw_dart_string(source: str, opening: int) -> bool:
    return (
        opening > 0
        and source[opening - 1] in {"r", "R"}
        and (opening < 2 or not re.match(r"[A-Za-z0-9_]", source[opening - 2]))
    )


def _dart_string_extent(
    source: str, opening: int
) -> tuple[int, tuple[tuple[int, int], ...]]:
    """Return one Dart string end plus executable `${...}` expression ranges."""

    quote = source[opening]
    delimiter = quote * 3 if source.startswith(quote * 3, opening) else quote
    raw = _is_raw_dart_string(source, opening)
    interpolations: list[tuple[int, int]] = []
    index = opening + len(delimiter)
    while index < len(source):
        if source.startswith(delimiter, index):
            return index + len(delimiter), tuple(interpolations)
        if not raw and source[index] == "\\":
            index += 2
            continue
        if not raw and source.startswith("${", index):
            closing = _matching_dart_interpolation_brace(source, index + 1)
            interpolations.append((index + 2, closing))
            index = closing + 1
            continue
        index += 1
    return len(source), tuple(interpolations)


def _matching_dart_interpolation_brace(source: str, opening: int) -> int:
    """Match a `${...}` brace while respecting nested Dart lexical regions."""

    depth = 1
    index = opening + 1
    while index < len(source):
        if source.startswith("//", index):
            end = source.find("\n", index)
            index = len(source) if end < 0 else end
            continue
        if source.startswith("/*", index):
            comment_depth = 1
            index += 2
            while index < len(source) and comment_depth:
                if source.startswith("/*", index):
                    comment_depth += 1
                    index += 2
                elif source.startswith("*/", index):
                    comment_depth -= 1
                    index += 2
                else:
                    index += 1
            continue
        if source[index] in {"'", '"'}:
            index, _ = _dart_string_extent(source, index)
            continue
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return len(source)


def _strip_comments(source: str) -> str:
    """Replace Dart comments with whitespace while preserving strings and offsets."""

    cleaned = list(source)
    index = 0
    while index < len(source):
        if source[index] in {"'", '"'}:
            index, _ = _dart_string_extent(source, index)
            continue
        if source.startswith("//", index):
            end = source.find("\n", index)
            end = len(source) if end < 0 else end
            for offset in range(index, end):
                if cleaned[offset] not in {"\r", "\n"}:
                    cleaned[offset] = " "
            index = end
            continue
        if source.startswith("/*", index):
            depth = 1
            end = index + 2
            while end < len(source) and depth:
                if source.startswith("/*", end):
                    depth += 1
                    end += 2
                elif source.startswith("*/", end):
                    depth -= 1
                    end += 2
                else:
                    end += 1
            for offset in range(index, end):
                if cleaned[offset] not in {"\r", "\n"}:
                    cleaned[offset] = " "
            index = end
            continue
        index += 1
    return "".join(cleaned)


def _mask_comments_and_strings(source: str) -> str:
    """Mask inert Dart text but retain executable `${...}` interpolation code."""

    uncommented = _strip_comments(source)
    cleaned = list(uncommented)
    index = 0
    while index < len(uncommented):
        if uncommented[index] not in {"'", '"'}:
            index += 1
            continue
        start = index
        end, interpolations = _dart_string_extent(uncommented, start)
        for offset in range(start, min(end, len(cleaned))):
            if cleaned[offset] not in {"\r", "\n"}:
                cleaned[offset] = " "
        for expression_start, expression_end in interpolations:
            expression = _mask_comments_and_strings(
                uncommented[expression_start:expression_end]
            )
            cleaned[expression_start:expression_end] = expression
        index = end
    return "".join(cleaned)


def _try_catch_regions(
    body: str, awaited_start: int, awaited_end: int
) -> tuple[str, str, str] | None:
    """Return success, catch, and post-catch regions covering the await."""

    candidates = list(re.finditer(r"\btry\s*\{", body[:awaited_start]))
    for candidate in reversed(candidates):
        opening = body.find("{", candidate.start())
        closing = matching_delimiter(body, opening, "{", "}")
        if not (opening < awaited_start < awaited_end <= closing):
            continue
        catch = re.match(
            rf"\s*catch\s*\(\s*({IDENTIFIER})(?:\s*,\s*{IDENTIFIER})?\s*\)\s*\{{",
            body[closing + 1 :],
        )
        if catch is None:
            continue
        catch_opening = body.find("{", closing + 1 + catch.start())
        catch_closing = matching_delimiter(body, catch_opening, "{", "}")
        return (
            body[awaited_end:closing],
            body[catch_opening + 1 : catch_closing],
            body[catch_closing + 1 :],
        )
    return None


def _emit_arguments(region: str) -> tuple[str, ...]:
    """Return `state.copyWith` arguments nested in exact state emit calls."""

    region = _strip_comments(region)
    arguments: list[str] = []
    for match in re.finditer(r"\bemit\s*\(", region):
        opening = region.find("(", match.start())
        try:
            closing = matching_delimiter(region, opening, "(", ")")
        except ContractError:
            continue
        emit_argument = region[opening + 1 : closing].strip()
        copy_with = re.match(r"^state\s*\.\s*copyWith\s*\(", emit_argument)
        if copy_with is None:
            continue
        copy_opening = emit_argument.find("(", copy_with.start())
        try:
            copy_closing = matching_delimiter(
                emit_argument, copy_opening, "(", ")"
            )
        except ContractError:
            continue
        if emit_argument[copy_closing + 1 :].strip():
            continue
        arguments.append(emit_argument[copy_opening + 1 : copy_closing])
    return tuple(arguments)


def _copy_with_values(region: str) -> dict[str, list[str]]:
    """Return top-level named values from direct emit(state.copyWith(...))."""

    values: dict[str, list[str]] = {}
    for arguments in _emit_arguments(region):
        for parameter in split_top_level(arguments):
            match = re.fullmatch(rf"({IDENTIFIER})\s*:\s*([\s\S]+)", parameter)
            if match:
                values.setdefault(match.group(1), []).append(match.group(2).strip())
    return values


def _copy_with_assignments(region: str) -> tuple[tuple[str, str, int], ...]:
    """Return masked direct state.copyWith assignments and their emit offsets."""

    source = _mask_comments_and_strings(region)
    assignments: list[tuple[str, str, int]] = []
    for emit in re.finditer(r"\bemit\s*\(", source):
        opening = source.find("(", emit.start())
        try:
            closing = matching_delimiter(source, opening, "(", ")")
        except ContractError:
            continue
        argument = source[opening + 1 : closing].strip()
        copy_with = re.match(r"^state\s*\.\s*copyWith\s*\(", argument)
        if copy_with is None:
            continue
        copy_opening = argument.find("(", copy_with.start())
        try:
            copy_closing = matching_delimiter(argument, copy_opening, "(", ")")
        except ContractError:
            continue
        if argument[copy_closing + 1 :].strip():
            continue
        for parameter in split_top_level(argument[copy_opening + 1 : copy_closing]):
            match = re.fullmatch(rf"({IDENTIFIER})\s*:\s*([\s\S]+)", parameter)
            if match:
                assignments.append(
                    (match.group(1), match.group(2).strip(), emit.start())
                )
    return tuple(assignments)


def _normalized_expression(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _navigation_signal_values(region: str, field: str) -> list[str]:
    """Return signal values proved by direct `emit(state.copyWith(...))`."""

    return [
        _normalized_expression(value)
        for candidate, value, _ in _copy_with_assignments(region)
        if candidate == field
    ]


def _named_assignment_expression(source: str, start: int) -> str:
    """Read one conventional named-argument expression from masked Dart source."""

    pairs = {"(": ")", "[": "]", "{": "}"}
    stack: list[str] = []
    index = start
    while index < len(source):
        char = source[index]
        if char in pairs:
            stack.append(pairs[char])
        elif char in {")", "]", "}"}:
            if not stack:
                break
            if char == stack[-1]:
                stack.pop()
        elif char in {",", ";"} and not stack:
            break
        index += 1
    return source[start:index].strip()


def _navigation_signal_assignments(
    region: str, field: str
) -> tuple[tuple[str, int], ...]:
    """Return every executable `field: value` occurrence for one signal."""

    source = _mask_comments_and_strings(region)
    assignments: list[tuple[str, int]] = []
    for match in re.finditer(rf"\b{re.escape(field)}\s*:\s*", source):
        value = _named_assignment_expression(source, match.end())
        assignments.append((_normalized_expression(value), match.start()))
    return tuple(assignments)


def _navigation_signal_assignment_values(region: str, field: str) -> list[str]:
    return [value for value, _ in _navigation_signal_assignments(region, field)]


def _is_obvious_state_self_assignment(mutation: object) -> bool:
    """Recognize only direct `field = state.field` local no-op declarations."""

    if mutation.operator != "=":
        return False
    value = _normalized_expression(mutation.value)
    while value.startswith("(") and value.endswith(")"):
        try:
            closing = matching_delimiter(value, 0, "(", ")")
        except ContractError:
            break
        if closing != len(value) - 1:
            break
        value = value[1:-1]
    field = mutation.target.field
    return value in {f"state.{field}", f"this.state.{field}"}


def _contains_state_writes(region: str, mutations: tuple[object, ...]) -> bool:
    if not mutations:
        return True
    values = _copy_with_values(region)
    for mutation in mutations:
        candidates = values.get(mutation.target.field, [])
        if len(candidates) != 1:
            return False
        if mutation.operator == "=":
            expected = re.sub(r"\s+", "", mutation.value)
            actual = re.sub(r"\s+", "", candidates[0])
            if actual != expected:
                return False
        elif mutation.operator == "<-" and mutation.value == "error":
            if (
                re.fullmatch(
                    r"error(?:\.[A-Za-z_][A-Za-z0-9_]*\([^)]*\))?",
                    candidates[0],
                )
                is None
            ):
                return False
    return True


def _mapped_state_write_present(
    region: str,
    mutation: object,
    *,
    response_type: str | None = None,
    response_variable: str | None = None,
) -> bool:
    """Prove one source value is assigned to its declared target field."""

    if mutation.source is None:
        return True
    source = re.escape(mutation.source.field)
    if mutation.source.type_name == response_type and response_variable:
        expression = rf"{re.escape(response_variable)}\s*\.\s*{source}"
    else:
        expression = rf"state\s*\.\s*{source}"
    candidates = _copy_with_values(region).get(mutation.target.field, [])
    return len(candidates) == 1 and re.fullmatch(expression, candidates[0]) is not None


def _validate_guard_runtime(flow: object, body: str) -> None:
    if flow.guard_value is None:
        return
    clean_body = _strip_comments(body)
    field = re.escape(flow.guard_value.reference.field)
    if flow.guard_value.expected:
        blocked_condition = (
            rf"(?:!\s*state\s*\.\s*{field}\b|"
            rf"state\s*\.\s*{field}\s*(?:==\s*false|!=\s*true))"
        )
    else:
        blocked_condition = (
            rf"(?:state\s*\.\s*{field}\b(?!\s*(?:==\s*false|!=\s*true))|"
            rf"state\s*\.\s*{field}\s*(?:==\s*true|!=\s*false))"
        )
    guard = re.search(
        rf"\bif\s*\(\s*{blocked_condition}\s*\)\s*"
        rf"(?:return\s*;|\{{\s*return\s*;\s*\}})",
        clean_body,
    )
    if guard is None:
        raise ContractError(
            f"Interaction Flow `{flow.flow}` must implement the inverse of Guard "
            f"`{flow.guard}` as an immediate early return"
        )
    prefix = clean_body[: guard.start()]
    if prefix.strip():
        raise ContractError(
            f"Interaction Flow `{flow.flow}` Guard must be the handler's first "
            "executable statement"
        )


def _validate_concurrency_runtime(flow: object, registration: str) -> None:
    transformer = {
        # ignore-while-active is proved by the explicit Guard plus active/reset
        # state contract; a droppable transformer may be used but is not required.
        "ignore-while-active": None,
        "latest-wins": "restartable",
        "queue": "sequential",
        "allow-parallel": "concurrent",
        "not-applicable": None,
    }[flow.concurrency]
    if transformer is None:
        return
    if not re.search(
        rf"\btransformer\s*:\s*{transformer}\s*\(\s*\)", registration
    ):
        raise ContractError(
            f"Interaction Flow `{flow.flow}` Concurrency `{flow.concurrency}` "
            f"requires transformer: {transformer}()"
        )


def _validate_widget_trigger_runtime(
    flow: object, view_source: str, view_model_type: str
) -> None:
    """Prove the declared Widget/action callback dispatches the Flow Event."""

    if flow.trigger_widget is None:
        return
    action = flow.trigger.rsplit(".", 1)[-1]
    callback_names = {
        "tap": ("onTap", "onPressed"),
        "change": ("onChanged",),
        "submit": ("onSubmitted", "onPressed"),
        "refresh": ("onRefresh",),
        "retry": ("onRetry", "onPressed"),
        "select": ("onSelected", "onTap"),
        "dismiss": ("onDismissed", "onTap"),
    }[action]
    receiver = (
        rf"(?:(?P<named>\b(?:vm|viewModel|bloc))|"
        rf"(?P<context>context\s*\.\s*(?:read|watch)\s*<\s*"
        rf"{re.escape(view_model_type)}\s*>\s*\(\s*\)))"
    )
    dispatch = re.compile(
        rf"{receiver}\s*\.\s*add\s*\(\s*(?:const\s+)?"
        rf"{re.escape(flow.event)}\s*\("
    )
    for widget in re.finditer(
        rf"\b{re.escape(flow.trigger_widget)}\s*\(", view_source
    ):
        opening = view_source.find("(", widget.start())
        closing = matching_delimiter(view_source, opening, "(", ")")
        constructor = view_source[opening + 1 : closing]
        for callback_name in callback_names:
            callback = re.search(
                rf"\b{callback_name}\s*:\s*(?:\([^)]*\)|{IDENTIFIER})?\s*"
                rf"(?:async\s*)?(?:=>|\{{)",
                constructor,
            )
            if callback is None:
                continue
            marker = callback.group(0).rstrip()
            if marker.endswith("{"):
                callback_opening = constructor.find("{", callback.start())
                callback_closing = matching_delimiter(
                    constructor, callback_opening, "{", "}"
                )
                callback_region = constructor[
                    callback_opening + 1 : callback_closing
                ]
            else:
                expression_end = constructor.find(",", callback.end())
                callback_region = constructor[
                    callback.end() : expression_end if expression_end >= 0 else None
                ]
            for dispatch_match in dispatch.finditer(callback_region):
                named_receiver = dispatch_match.group("named")
                if named_receiver is None:
                    return
                callback_parameters = re.search(
                    r":\s*\(([^)]*)\)", callback.group(0)
                )
                if callback_parameters and re.search(
                    rf"\b{re.escape(named_receiver)}\b",
                    callback_parameters.group(1),
                ):
                    if re.search(
                        rf"\b{re.escape(view_model_type)}\s+"
                        rf"{re.escape(named_receiver)}\b",
                        callback_parameters.group(1),
                    ):
                        return
                    continue
                declared_types = set(
                    re.findall(
                        rf"\b({IDENTIFIER})\s+{re.escape(named_receiver)}\b",
                        view_source,
                    )
                )
                if declared_types == {view_model_type}:
                    return
    raise ContractError(
        f"Interaction Flow `{flow.flow}` must dispatch [{flow.event}] inline "
        f"from {flow.trigger}; the Event was not proven in that Widget callback"
    )


def _listener_callbacks(
    source: str,
) -> list[tuple[str, str, str, str, str, str]]:
    """Return exact generic types and callback bindings for FlowR listeners."""

    callbacks: list[tuple[str, str, str, str, str, str]] = []
    for widget in re.finditer(
        rf"\bFr(?:Listener|Consumer)\s*<\s*({IDENTIFIER})\s*,\s*"
        rf"({IDENTIFIER})\s*>\s*\(",
        source,
    ):
        opening = source.find("(", widget.start())
        closing = matching_delimiter(source, opening, "(", ")")
        constructor = source[opening + 1 : closing]
        listener = re.search(r"\blistener\s*:\s*\(", constructor)
        if listener is None:
            continue
        parameters_opening = constructor.find("(", listener.start())
        parameters_closing = matching_delimiter(
            constructor, parameters_opening, "(", ")"
        )
        names: list[str] = []
        for parameter in split_top_level(
            constructor[parameters_opening + 1 : parameters_closing]
        ):
            identifiers = re.findall(IDENTIFIER, parameter)
            if identifiers:
                names.append(identifiers[-1])
        if len(names) < 3:
            continue
        tail = constructor[parameters_closing + 1 :].lstrip()
        if tail.startswith("async"):
            tail = tail[len("async") :].lstrip()
        if not tail.startswith("{"):
            continue
        body_closing = matching_delimiter(tail, 0, "{", "}")
        callbacks.append(
            (
                widget.group(1),
                widget.group(2),
                names[0],
                names[1],
                names[2],
                tail[1:body_closing],
            )
        )
    return callbacks


def _has_view_navigation(region: str, context_name: str) -> bool:
    """Recognize typed Page helpers or explicit router navigation in one branch."""

    context = re.escape(context_name)
    typed_page = re.compile(
        rf"\b{IDENTIFIER}Page\s*\([\s\S]*?\)\s*\.\s*"
        rf"(?:go|push|replace)(?:\s*<[^>]+>)?\s*\(\s*{context}\b"
    )
    router = re.compile(
        rf"(?:\b{context}\s*[?!]?\s*\.\s*"
        rf"(?:go|goNamed|push|pushNamed|pushReplacement|replace|pop|maybePop)"
        rf"(?:\s*<[^>]+>)?\s*\(|"
        rf"\b(?:GoRouter|Navigator)\s*\.\s*of\s*\(\s*{context}\s*\)\s*"
        rf"[?!]?\s*\.\s*(?:go|goNamed|push|pushNamed|pushReplacement|"
        rf"replace|pop|maybePop)(?:\s*<[^>]+>)?\s*\()"
    )
    return typed_page.search(region) is not None or router.search(region) is not None


def _braced_if_branches(
    source: str,
) -> list[tuple[str, str, int, int, int]]:
    """Return condition, body, start, body start, and end for braced if branches."""

    branches: list[tuple[str, str, int, int, int]] = []
    for match in re.finditer(r"\bif\s*\(", source):
        opening = source.find("(", match.start())
        closing = matching_delimiter(source, opening, "(", ")")
        brace = closing + 1
        while brace < len(source) and source[brace].isspace():
            brace += 1
        if brace >= len(source) or source[brace] != "{":
            continue
        body_end = matching_delimiter(source, brace, "{", "}")
        branches.append(
            (
                source[opening + 1 : closing],
                source[brace + 1 : body_end],
                match.start(),
                brace + 1,
                body_end + 1,
            )
        )
    return branches


def _brace_depth(source: str, offset: int) -> int:
    return source[:offset].count("{") - source[:offset].count("}")


def _canonical_condition(value: str) -> str:
    """Normalize whitespace and balanced outer parentheses for exact checks."""

    value = re.sub(r"\s+", "", value)
    while value.startswith("("):
        try:
            closing = matching_delimiter(value, 0, "(", ")")
        except ContractError:
            break
        if closing != len(value) - 1:
            break
        value = value[1:-1]
    return value


def _split_top_level_operator(value: str, operator: str) -> tuple[str, ...]:
    """Split one conventional boolean condition at a top-level operator."""

    value = _canonical_condition(value)
    parts: list[str] = []
    start = 0
    depth = 0
    index = 0
    while index < len(value):
        if value[index] == "(":
            depth += 1
        elif value[index] == ")":
            depth -= 1
        elif depth == 0 and value.startswith(operator, index):
            parts.append(_canonical_condition(value[start:index]))
            index += len(operator)
            start = index
            continue
        index += 1
    parts.append(_canonical_condition(value[start:]))
    return tuple(parts)


def _has_equality_early_return(
    source: str, before: int, equal_conditions: set[str]
) -> bool:
    """Recognize a top-level exact equality guard that immediately returns."""

    for match in re.finditer(r"\bif\s*\(", source[:before]):
        if _brace_depth(source, match.start()) != 0:
            continue
        opening = source.find("(", match.start())
        closing = matching_delimiter(source, opening, "(", ")")
        if _canonical_condition(source[opening + 1 : closing]) not in equal_conditions:
            continue
        tail = source[closing + 1 : before].lstrip()
        if re.match(r"return\s*;", tail):
            return True
        if not tail.startswith("{"):
            continue
        body_end = matching_delimiter(tail, 0, "{", "}")
        if tail[1:body_end].strip() == "return;":
            return True
    return False


def _validate_view_listener_navigation(
    flow: object, view_source: str, view_model_type: str
) -> None:
    """Prove one exact listener transition branch owns navigation."""

    signal = flow.navigation_signal
    enum_type = flow.navigation_enum
    enum_member = flow.navigation_member
    if signal is None or enum_type is None or enum_member is None:
        return
    for (
        generic_vm,
        generic_model,
        context_name,
        previous_name,
        current_name,
        body,
    ) in _listener_callbacks(_mask_comments_and_strings(view_source)):
        if generic_vm != view_model_type or generic_model != signal.type_name:
            continue
        previous_field = f"{previous_name}.{signal.field}"
        current_field = f"{current_name}.{signal.field}"
        member = f"{enum_type}.{enum_member}"
        different_conditions = {
            f"{previous_field}!={current_field}",
            f"{current_field}!={previous_field}",
        }
        equal_conditions = {
            f"{previous_field}=={current_field}",
            f"{current_field}=={previous_field}",
        }
        member_conditions = {
            f"{current_field}=={member}",
            f"{member}=={current_field}",
        }
        branches = _braced_if_branches(body)
        for condition, branch_body, start, _, _ in branches:
            canonical = _canonical_condition(condition)
            conjunction = _split_top_level_operator(condition, "&&")
            exact_member_branch = canonical in member_conditions
            exact_combined_branch = (
                len(conjunction) == 2
                and any(part in different_conditions for part in conjunction)
                and any(part in member_conditions for part in conjunction)
            )
            if not exact_member_branch and not exact_combined_branch:
                continue
            if not _has_view_navigation(branch_body, context_name):
                continue
            if exact_combined_branch:
                return
            exact_transition_parent = any(
                parent_start < start < parent_end
                and _canonical_condition(parent_condition)
                in different_conditions
                for parent_condition, _, parent_start, _, parent_end in branches
            )
            if exact_transition_parent or _has_equality_early_return(
                body, start, equal_conditions
            ):
                return
    raise ContractError(
        f"Interaction Flow `{flow.flow}` must bind exact "
        f"FrListener/FrConsumer<{view_model_type}, {signal.type_name}> generics, "
        "compares previous/current with `!=` or an equality early-return guard, "
        "and navigate inside the exact enum member braced branch"
    )


def _validate_view_model_navigation_boundary(vm_source: str) -> None:
    """Keep Flutter routing authority and BuildContext out of the ViewModel."""

    source = _mask_comments_and_strings(vm_source)
    if re.search(
        r"\b(?:BuildContext|GoRouter|GoRouterState|GoRouteData|Navigator|"
        r"NavigatorState|RouterConfig|RouterDelegate|RouteInformationParser)\b",
        source,
    ):
        raise ContractError(
            "ViewModel must not own BuildContext or router types; emit a nullable "
            "semantic enum signal and navigate from a View FrListener/FrConsumer"
        )
    typed_page_call = re.search(
        rf"\b{IDENTIFIER}Page\s*\([\s\S]*?\)\s*\.\s*"
        r"(?:go|push|replace)(?:\s*<[^>]+>)?\s*\(",
        source,
    )
    navigation_methods = (
        r"(?:go|goNamed|goBranch|push|pushNamed|pushReplacement|"
        r"pushReplacementNamed|pushNamedAndRemoveUntil|pushAndRemoveUntil|"
        r"replace|replaceNamed|pop|popUntil|maybePop|popAndPushNamed)"
    )
    known_router_call = re.search(
        rf"(?:\b(?:context|ctx|router|goRouter|appRouter|navigator|nav|navigation|"
        rf"routerDelegate|rootNavigator)\s*[?!]?\s*\.\s*{navigation_methods}|"
        rf"\bnavigatorKey\s*\.\s*currentState\s*[?!]?\s*\.\s*"
        rf"{navigation_methods})\s*(?:<[^>]+>)?\s*\(",
        source,
    )
    distinctive_method = (
        r"(?:go|goNamed|goBranch|pushNamed[A-Za-z0-9_]*|"
        r"pushReplacement[A-Za-z0-9_]*|pushAndRemoveUntil|replaceNamed|"
        r"maybePop|popUntil|popAndPushNamed|restorablePush[A-Za-z0-9_]*)"
    )
    distinctive_router_call = re.search(
        rf"\.\s*{distinctive_method}\s*(?:<[^>]+>)?\s*\(", source
    )
    if typed_page_call or known_router_call or distinctive_router_call:
        raise ContractError(
            "ViewModel must not call router navigation; emit a nullable semantic "
            "enum signal and navigate from a View FrListener/FrConsumer"
        )


def validate_runtime_integration(component: object, contract: str) -> None:
    """Prove every BFF v9 Flow independently in the final component sources."""

    if not is_bff_mode(component):
        return
    component_file = Path(component.component_file)
    if len(component.view_models) > 1:
        raise ContractError(
            "BFF runtime validation supports at most one ViewModel reference"
        )
    if not component.view_models:
        if component.interactions:
            raise ContractError(
                "BFF v9 interaction validation requires exactly one ViewModel "
                "reference"
            )
        return
    vm_class = component.view_models[0]
    vm_file = component_file.with_name(f"{component_file.stem}.vm.dart")
    vm_source = require_file(vm_file, "component ViewModel")
    _validate_view_model_navigation_boundary(vm_source)
    if not component.interactions:
        return
    view_file = component_file.with_name(f"{component_file.stem}.v.dart")
    view_source = require_file(view_file, "component View")

    service_type: str | None = None
    service_field: str | None = None
    service_source = ""
    if component.endpoints:
        service = re.fullmatch(rf"\[({IDENTIFIER})\]", component.bff_service or "")
        if service is None:
            raise ContractError("BFF v9 endpoint Flows require BFF Service: [Type]")
        service_type = service.group(1)
        service_name = f"{component_file.stem}.srv.dart"
        if service_name not in component.imports:
            raise ContractError(
                f"BFF service must be imported as `import '{service_name}';`"
            )
        service_file = component_file.with_name(service_name)
        service_source = require_file(service_file, "BFF service")
        if not re.search(rf"\bclass\s+{re.escape(service_type)}\b", service_source):
            raise ContractError(f"BFF service does not declare class {service_type}")
        if "@RestApi" in service_source:
            raise ContractError(
                f"{service_type} must be a lib/api/gen SDK adapter, not @RestApi"
            )
        if not re.search(
            r"import\s+['\"][^'\"]*api/gen/[^'\"]+['\"](?:\s+as\s+\w+)?\s*;",
            service_source,
        ):
            raise ContractError(
                f"{service_type} must import generated SDK files from lib/api/gen"
            )
        service_field = declared_service_field(vm_source, vm_class, service_type)

    flow_events = {flow.event for flow in component.interactions}
    registered_contract_events = {
        event
        for event in re.findall(rf"\bon\s*<\s*({IDENTIFIER})\s*>", vm_source)
        if event in component.events
    }
    uncovered_events = sorted(registered_contract_events - flow_events)
    if uncovered_events:
        raise ContractError(
            "BFF v9 registered Events missing Interaction Flows: "
            + ", ".join(uncovered_events)
        )
    signal_owners: dict[str, tuple[object, int, int]] = {}
    for flow in component.interactions:
        signal = flow.navigation_signal
        if signal is None:
            continue
        if signal.field in signal_owners:
            prior = signal_owners[signal.field][0]
            raise ContractError(
                f"Navigation signal runtime field `{signal.field}` must be owned "
                f"by exactly one Flow; found `{prior.flow}` and `{flow.flow}`"
            )
        handler_name, _ = registered_flow_handler(vm_source, flow)
        _, _, body_start, body_end = function_body_region(vm_source, handler_name)
        signal_owners[signal.field] = (flow, body_start, body_end)
    for field, (flow, body_start, body_end) in signal_owners.items():
        for _, offset in _navigation_signal_assignments(vm_source, field):
            if not body_start <= offset < body_end:
                raise ContractError(
                    f"Navigation signal [{flow.navigation_signal.type_name}]."
                    f"{field} must not be written outside owning Flow "
                    f"`{flow.flow}` handler"
                )
    endpoint_by_request = {
        endpoint.request_type: endpoint for endpoint in component.endpoints
    }
    for flow in component.interactions:
        handler_name, registration = registered_flow_handler(vm_source, flow)
        _validate_concurrency_runtime(flow, registration)
        signature, body = function_body(vm_source, handler_name)
        body = _strip_comments(body)
        _validate_guard_runtime(flow, body)
        _validate_widget_trigger_runtime(flow, view_source, vm_class)
        if flow.endpoint is None:
            writes = (
                flow.pending_mutations
                + flow.success_mutations
                + flow.failure_mutations
            )
            signal = flow.navigation_signal
            ordinary_writes = tuple(
                mutation
                for mutation in writes
                if signal is None or mutation.target != signal
            )
            if ordinary_writes and not _contains_state_writes(body, ordinary_writes):
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` local handler must implement "
                    "its declared state writes"
                )
            if any(
                not _mapped_state_write_present(body, mutation)
                for mutation in ordinary_writes
                if mutation.source is not None
            ):
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` local handler must map each "
                    "declared source to its exact target state field"
                )
            if signal is not None:
                expected_member = f"{flow.navigation_enum}.{flow.navigation_member}"
                assignments = _navigation_signal_assignment_values(body, signal.field)
                emitted_values = _navigation_signal_values(body, signal.field)
                expected_values = ["null", expected_member]
                if assignments != expected_values or emitted_values != expected_values:
                    raise ContractError(
                        f"Interaction Flow `{flow.flow}` local handler must write "
                        f"[{signal.type_name}].{signal.field} exactly as direct "
                        f"Pending null then Success {expected_member}; found named "
                        f"assignments {assignments} and direct emissions "
                        f"{emitted_values}"
                    )
                _validate_view_listener_navigation(flow, view_source, vm_class)
            continue

        if "async" not in signature or not re.search(
            r"\bFuture(?:\s*<[^>]+>)?", signature
        ):
            raise ContractError(
                f"Interaction Flow `{flow.flow}` API handler must return Future and "
                "be async"
            )
        endpoint = endpoint_by_request[flow.endpoint]
        assert service_type is not None and service_field is not None
        operation = operation_name(service_type, endpoint.request_type)
        if not re.search(rf"\b{re.escape(operation)}\s*\(", service_source):
            raise ContractError(
                f"Interaction Flow `{flow.flow}` requires {service_type}.{operation}"
            )
        request = re.search(
            rf"\b(?:final|{re.escape(endpoint.request_type)})\s+({IDENTIFIER})\s*=\s*"
            rf"{re.escape(endpoint.request_type)}\s*\(",
            body,
        )
        if request is None:
            raise ContractError(
                f"Interaction Flow `{flow.flow}` must construct "
                f"{endpoint.request_type}"
            )
        service_ref = rf"(?:this\.)?{re.escape(service_field)}"
        awaited = re.search(
            rf"\b(?:final|{re.escape(endpoint.response_type)})\s+({IDENTIFIER})\s*=\s*"
            rf"await\s+{service_ref}\.{re.escape(operation)}\s*\(([^;]*)\)\s*;",
            body,
            re.DOTALL,
        )
        if awaited is None:
            raise ContractError(
                f"Interaction Flow `{flow.flow}` must await {service_type}."
                f"{operation} and retain {endpoint.response_type}"
            )
        if not re.search(rf"\b{re.escape(request.group(1))}\b", awaited.group(2)):
            raise ContractError(
                f"Interaction Flow `{flow.flow}` must pass its "
                f"{endpoint.request_type} request to {operation}"
            )
        before_call = body[: awaited.start()]
        covered_regions = _try_catch_regions(body, awaited.start(), awaited.end())
        if covered_regions is None:
            raise ContractError(
                f"Interaction Flow `{flow.flow}` API await must be covered by its "
                "own try/catch"
            )
        success_region, failure_region, after_catch = covered_regions
        if not _contains_state_writes(before_call, flow.pending_mutations):
            raise ContractError(
                f"Interaction Flow `{flow.flow}` must emit all Pending State writes "
                "before the API call"
            )
        if not _contains_state_writes(success_region, flow.success_mutations):
            raise ContractError(
                f"Interaction Flow `{flow.flow}` must emit all Success State writes "
                "after the API response"
            )
        if not _contains_state_writes(failure_region, flow.failure_mutations):
            raise ContractError(
                f"Interaction Flow `{flow.flow}` must emit all Failure State writes "
                "from catch"
            )
        response_variable = awaited.group(1)
        for mutation in flow.success_mutations:
            if not _mapped_state_write_present(
                success_region,
                mutation,
                response_type=endpoint.response_type,
                response_variable=response_variable,
            ):
                source = mutation.source
                assert source is not None
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` Success State must assign "
                    f"[{source.type_name}].{source.field} to exact target "
                    f"[{mutation.target.type_name}].{mutation.target.field}"
                )
        if flow.navigation_signal is not None:
            signal = flow.navigation_signal
            expected_member = f"{flow.navigation_enum}.{flow.navigation_member}"
            before_assignments = _navigation_signal_assignment_values(
                before_call, signal.field
            )
            success_assignments = _navigation_signal_assignment_values(
                success_region, signal.field
            )
            failure_assignments = _navigation_signal_assignment_values(
                failure_region, signal.field
            )
            after_assignments = _navigation_signal_assignment_values(
                after_catch, signal.field
            )
            before_emissions = _navigation_signal_values(before_call, signal.field)
            success_emissions = _navigation_signal_values(
                success_region, signal.field
            )
            if before_assignments != ["null"] or before_emissions != ["null"]:
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` owning API handler may write "
                    f"[{signal.type_name}].{signal.field} only as one direct null "
                    f"assignment before the API call; found named assignments "
                    f"{before_assignments} and direct emissions {before_emissions}"
                )
            if (
                success_assignments != [expected_member]
                or success_emissions != [expected_member]
            ):
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` owning API handler must write "
                    f"[{signal.type_name}].{signal.field} exactly as one direct "
                    f"{expected_member} assignment in Success; found named "
                    f"assignments {success_assignments} and direct emissions "
                    f"{success_emissions}"
                )
            if failure_assignments or after_assignments:
                raise ContractError(
                    f"Interaction Flow `{flow.flow}` Navigation signal may be "
                    "assigned only after success; Failure and post-catch writes "
                    "are forbidden"
                )
            _validate_view_listener_navigation(flow, view_source, vm_class)


def validate_bff_contract(
    component, contract: str, *, check_artifact: bool = True
) -> None:
    """Require a complete, reproducible BFF-JSON delivery contract."""

    if not is_bff_mode(component):
        return
    if is_api_less_bff(component):
        if check_artifact:
            generate_bff(component, check=True)
        return
    component_file = Path(component.component_file)
    data_envelope = load_request_data_envelope_profile(component_file)
    response_envelope = load_bff_response_envelope_profile(component_file)
    shell = require_file(component_file, "component library")
    if "package:fr_acdd/fr_acdd.dart" not in shell:
        raise ContractError(
            "BFF-JSON component shell must import package:fr_acdd/fr_acdd.dart"
        )
    view_file = component_file.with_name(f"{component_file.stem}.v.dart")
    view_source = require_file(view_file, "component View source")
    page_annotations = re.findall(
        r"@FrAcddPage\s*\((.*?)\)",
        contract + "\n" + view_source,
        re.DOTALL,
    )
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
    api_lines = component.sections.get("BFF-UI-API", [])
    api_text = "\n".join(api_lines)
    refs = bracket_refs(api_lines)
    if (
        not re.search(r"\b(?:GET|POST|PUT|PATCH|DELETE)\s+\S+", api_text)
        or len(refs) < 2
    ):
        raise ContractError(
            "BFF-UI-API must describe an HTTP method, path, request DTO, and response DTO"
        )
    if len(refs) % 2 != 0:
        raise ContractError(
            "BFF-UI-API must declare request/response DTO references in pairs"
        )
    direct_request_types = {
        boundary.request_type
        for boundary in direct_business_request_boundaries(component, contract)
    }
    invalid_requests = sorted(
        {
            name
            for name in refs[0::2]
            if not name.endswith("BffReq")
            and not (data_envelope is not None and name.endswith("RequestDto"))
        }
    )
    invalid_responses = sorted(
        {name for name in refs[1::2] if not name.endswith("BffRsp")}
    )
    if invalid_requests:
        raise ContractError(
            "BFF request boundary classes must use the XxxBffReq suffix "
            "(or XxxRequestDto when the request-data-envelope profile is enabled): "
            + ", ".join(invalid_requests)
        )
    if invalid_responses:
        raise ContractError(
            "BFF response boundary classes must use the XxxBffRsp suffix: "
            + ", ".join(invalid_responses)
        )
    if response_envelope:
        required_fields = (
            response_envelope.state_field,
            response_envelope.code_field,
            response_envelope.message_field,
            response_envelope.data_field,
        )
        for response_type in refs[1::2]:
            fields = set(factory_fields(contract, response_type))
            missing_fields = [field for field in required_fields if field not in fields]
            if missing_fields:
                raise ContractError(
                    f"BFF response DTO {response_type} must define the configured "
                    "gateway envelope fields: " + ", ".join(missing_fields)
                )
    class_required_refs = set(refs).difference(direct_request_types)
    names = set(class_names(contract))
    missing_classes = sorted(class_required_refs.difference(names))
    if missing_classes:
        raise ContractError(
            "BFF-UI-API references undefined DTOs: " + ", ".join(missing_classes)
        )
    missing = sorted(class_required_refs.difference(dto_classes))
    if missing:
        raise ContractError(
            "BFF-UI-API references classes that are not @FrAcddDto values: "
            + ", ".join(missing)
        )
    for request_type in refs[0::2]:
        if request_type in direct_request_types:
            continue
        body = class_body(contract, request_type)
        if not re.search(
            r"\bMap\s*<\s*String\s*,\s*dynamic\s*>\s+toJson\s*\(\s*\)\s*;",
            body,
        ):
            raise ContractError(
                f"BFF request DTO {request_type} must explicitly declare "
                "Map<String, dynamic> toJson() for Retrofit serialization"
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


def validate_page_route_conversion(
    page_file: Path,
    page_class: str,
    view: str,
    *,
    require_all_fields: bool = False,
) -> None:
    """Require typed Page route fields to be expanded into ordinary View fields."""

    source = require_file(page_file, "page support")
    if "<PENDING_ROUTE>" in source:
        raise ContractError(
            "typed page route must replace <PENDING_ROUTE> before validation"
        )
    class_match = re.search(rf"\bclass\s+{re.escape(page_class)}\b", source)
    if not class_match:
        raise ContractError(f"page support must declare typed route {page_class}")
    body_opening = source.find("{", class_match.end())
    if body_opening < 0:
        raise ContractError(f"page support has an unterminated {page_class} class")
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
        raise ContractError(f"page support has an unterminated {page_class} class")
    page_body = source[body_opening + 1 : body_closing]
    call_start = re.search(rf"\b{re.escape(view)}\s*\(", page_body)
    if not call_start:
        raise ContractError(
            f"typed route {page_class} must construct its primary view `{view}`"
        )
    opening = page_body.find("(", call_start.start())
    depth = 0
    closing = None
    for index in range(opening, len(page_body)):
        if page_body[index] == "(":
            depth += 1
        elif page_body[index] == ")":
            depth -= 1
            if depth == 0:
                closing = index
                break
    if closing is None:
        raise ContractError(f"page support has an unterminated `{view}` constructor")
    view_arguments = page_body[opening + 1 : closing]
    if re.search(r"\bargs\s*:", view_arguments):
        raise ContractError(
            f"typed page support must construct {view} with ordinary named fields; "
            "do not pass an args wrapper"
        )
    if not require_all_fields:
        return
    build_match = re.search(r"\bWidget\s+build\s*\(", page_body)
    if not build_match:
        raise ContractError(f"typed route {page_class} must declare Widget build")
    parameters_opening = page_body.find("(", build_match.start())
    parameters_closing = matching_delimiter(
        page_body, parameters_opening, "(", ")"
    )
    implementation = page_body[parameters_closing + 1 :].lstrip()
    if implementation.startswith("=>"):
        semicolon = implementation.find(";")
        build_region = implementation[2:semicolon if semicolon >= 0 else None]
    elif implementation.startswith("{"):
        implementation_closing = matching_delimiter(
            implementation, 0, "{", "}"
        )
        build_region = implementation[1:implementation_closing]
    else:
        raise ContractError(
            f"typed route {page_class} build must use an expression or block body"
        )
    field_names = re.findall(
        r"(?m)^\s*final\s+[^;=\n]+?\s+(\$?[A-Za-z_][A-Za-z0-9_]*)\s*;",
        page_body,
    )
    unused = [
        field
        for field in field_names
        if not re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(field)}\b", build_region
        )
    ]
    if unused:
        raise ContractError(
            f"page support does not consume {page_class} route fields in its "
            f"Provider/View construction: "
            + ", ".join(unused)
        )


def validate_state_ownership(page: object | None, component: object) -> None:
    """Place Providers at the lifecycle owner and reject redundant component VMs."""

    component_file = Path(component.component_file)
    component_paths = [
        component_file.with_name(f"{component_file.stem}.{suffix}.dart")
        for suffix in ("c", "v")
    ]
    component_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in component_paths
        if path.is_file()
    )
    ownership = component.state_ownership
    state_vm = component.state_view_model
    owns_vm = ownership in {"page-owned", "component-owned"}
    startup_events = bracket_refs(component.sections.get("Startup Event", []))

    if state_vm and component.view_models != [state_vm]:
        raise ContractError(
            f"State Ownership `{ownership} [{state_vm}]` must match exactly one "
            "ViewModels reference"
        )
    if ownership == "none" and component.view_models:
        raise ContractError("State Ownership `none` must not declare ViewModels")
    if ownership in {"none", "app-owned"} and (
        component.events or component.models
    ):
        raise ContractError(
            f"State Ownership `{ownership}` must not declare component-owned "
            "Events or Models"
        )
    if owns_vm and (not component.events or not component.models):
        raise ContractError(
            f"State Ownership `{ownership}` requires Events and Models"
        )
    if len(startup_events) > 1:
        raise ContractError("Startup Event must reference at most one Event")
    if startup_events and startup_events[0] not in component.events:
        raise ContractError(
            f"Startup Event [{startup_events[0]}] must also appear in Events"
        )

    vm_part = f"{component_file.stem}.vm.dart"
    if owns_vm and vm_part not in component.parts:
        raise ContractError(
            f"State Ownership `{ownership}` requires `part '{vm_part}';`"
        )
    if not owns_vm and vm_part in component.parts:
        raise ContractError(
            f"State Ownership `{ownership}` must not declare redundant VM part "
            f"`{vm_part}`"
        )

    has_component_provider = "FrProvider" in component_source
    if ownership == "component-owned":
        if not has_component_provider:
            raise ContractError(
                "component-owned state requires XxxView to create FrProvider"
            )
        if startup_events and (
            "onCreated:" not in component_source
            or not re.search(
                rf"\.add\s*\(\s*const\s+{re.escape(startup_events[0])}\s*\(",
                component_source,
            )
        ):
            raise ContractError(
                "component-owned FrProvider must dispatch its declared Startup Event"
            )
    elif has_component_provider:
        raise ContractError(
            f"State Ownership `{ownership}` must not create FrProvider inside "
            "the component"
        )

    if ownership == "page-owned":
        if page is None:
            raise ContractError(
                "page-owned state requires validation through its sibling "
                ".page.dart adapter"
            )
        page_source = require_file(Path(page.page_file), "page support")
        for page_class in page.page_classes:
            body = class_body(page_source, page_class)
            if "FrProvider" not in body:
                raise ContractError(
                    f"{page_class} must provide {state_vm} with FrProvider in "
                    ".page.dart"
                )
            if not re.search(rf"\b{re.escape(state_vm or '')}\s*\(", body):
                raise ContractError(
                    f"{page_class} FrProvider must create {state_vm}"
                )
            if startup_events and (
                "onCreated:" not in body
                or not re.search(
                    rf"\.add\s*\(\s*const\s+{re.escape(startup_events[0])}\s*\(",
                    body,
                )
            ):
                raise ContractError(
                    f"{page_class} FrProvider must dispatch declared Startup Event "
                    f"[{startup_events[0]}]"
                )
    elif page is not None and ownership == "component-owned":
        page_source = require_file(Path(page.page_file), "page support")
        if "FrProvider" in page_source:
            raise ContractError(
                "component-owned state must not duplicate its Provider in .page.dart"
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
            "custom Theme requires app-shared [ThemeType] or component [ThemeType]"
        )
    pubspec = find_package_pubspec(component_file)
    if not has_direct_dependency(pubspec, "fr_mvvm_theme", section="dependencies"):
        raise ContractError(
            f"{pubspec} must directly declare fr_mvvm_theme for Theme: {ownership}"
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
            "custom Theme contract"
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

    if DATA_BOUNDARY_TODO.search(contract):
        raise ContractError(
            "approved contract still contains unresolved `TODO(data-boundary)`; "
            "record an approved UI API/OpenAPI binding or an explicit API-less "
            "local-only decision"
        )
    match = APPROVAL_PLACEHOLDER.search(contract)
    if match:
        raise ContractError(
            f"approved contract still contains draft placeholder `{match.group(0)}`"
        )


def validate_figma_fill_data(component: object, *, phase: str) -> None:
    """Reject unresolved Figma fills and prove bound fields reach the View."""

    sections = component.sections
    if "Figma Data" not in sections:
        return
    entries = parse_figma_fill_data(sections)
    if phase not in {"contract", "final"}:
        return
    pending = [entry.id for entry in entries if entry.binding == "pending"]
    if pending:
        raise ContractError(
            "approved contract still contains pending Figma Data bindings: "
            + ", ".join(pending)
        )
    component_file = Path(component.component_file)
    view_file = component_file.with_name(f"{component_file.stem}.v.dart")
    if not view_file.exists():
        return
    view_source = require_file(view_file, "component .v.dart implementation")
    for entry in entries:
        if entry.binding != "bound" or entry.render is None:
            continue
        model, field = entry.render.split(".", 1)
        if model not in component.models:
            raise ContractError(
                f"Figma Data `{entry.id}` Render model `{model}` is not declared"
            )
        if re.search(rf"\.\s*{re.escape(field)}\b", view_source) is None:
            raise ContractError(
                f"Figma Data `{entry.id}` Render `{entry.render}` is not used "
                f"by {view_file.name}"
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
    implementation_suffixes = ["v"]
    if component.state_ownership in {"page-owned", "component-owned"}:
        implementation_suffixes.append("vm")
    for suffix in implementation_suffixes:
        path = component_file.with_name(f"{component_file.stem}.{suffix}.dart")
        source = require_file(path, f"component .{suffix} implementation")
        if DERIVED_STUB_MARKER in source:
            raise ContractError(
                f"final validation rejects unfinished derived stub {path.name}"
            )


def validate_contract(page: object | None, component: object, *, phase: str) -> None:
    """Validate a parsed contract at the requested lifecycle phase."""

    component_file = Path(component.component_file)
    validate_leaf_module_directory(component_file)
    contract = require_file(Path(component.contract_file), "component contract")
    validate_state_ownership(page, component)
    implementation_suffixes = ["v"]
    if component.state_ownership in {"page-owned", "component-owned"}:
        implementation_suffixes.append("vm")
    for suffix in implementation_suffixes:
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
    if any(
        section in component.sections
        for section in ("Figma States", "Figma References", "Figma Excluded")
    ):
        parse_figma_contract_nodes(component.sections)
    validate_widget_tree(component)
    validate_model_names(component)
    validate_component_input_ownership(component_file)
    if page:
        for page_class in page.page_classes:
            validate_page_route_conversion(
                Path(page.page_file),
                page_class,
                page.primary_view,
                require_all_fields=phase in {"contract", "final"},
            )
    if phase in {"contract", "final"}:
        validate_figma_fill_data(component, phase=phase)
        validate_approved_contract(contract)
        validate_api_semantics(component, contract)
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
        validate_runtime_integration(component, contract)


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
        component_file = (
            args.component_file.resolve()
            if args.component_file
            else args.page_file.resolve().with_name(
                args.page_file.name.removesuffix(".page.dart") + ".dart"
            )
        )
        validate_leaf_module_directory(component_file)
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

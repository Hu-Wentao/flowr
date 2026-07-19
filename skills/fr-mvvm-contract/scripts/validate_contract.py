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
)
from contract_parser import parse_component, parse_page
from generate_bff import generate_bff, is_bff_mode


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
BUSINESS_FIELDS = (
    "Goal",
    "Upstream Proof",
    "Effect",
    "Success Condition",
    "Failure Cases",
    "Navigation Ownership",
)
DATA_FIELDS = ("UI Data", "Source", "Loading/Refresh", "Empty/Error")
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
BUSINESS_EVENT_SUFFIXES = (
    "Submitted",
    "Confirmed",
    "Completed",
    "Requested",
    "Saved",
    "Deleted",
)
DATA_EVENT_SUFFIXES = ("Started", "Loaded", "Refreshed")
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
        raise ContractError(
            "component contract must reference at least one state Model"
        )
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


def factory_fields(source: str, class_name: str) -> list[str]:
    """Read named fields from the conventional Freezed factory declaration."""

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
    fields: list[str] = []
    for parameter in split_top_level(parameters):
        declaration = parameter.split("=", 1)[0]
        identifiers = re.findall(IDENTIFIER, declaration)
        if not identifiers:
            raise ContractError(
                f"cannot parse DTO field in {class_name}: {parameter.strip()}"
            )
        fields.append(identifiers[-1])
    return fields


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
                "`- field <- authoritative source | backend purpose`"
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

    lines = component.sections.get("BFF-API") or component.sections.get("API") or []
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


def validate_failure_cases(value: str) -> None:
    """Require every business failure to name an App recovery/display action."""

    cases = [item.strip() for item in value.split(";") if item.strip()]
    if not cases or any(
        "->" not in item
        or not item.split("->", 1)[0].strip()
        or not item.split("->", 1)[1].strip()
        for item in cases
    ):
        raise ContractError(
            "Business `Failure Cases` must use `error -> App recovery/display` "
            "for every semicolon-separated failure"
        )


def is_ui_only_response_field(field: str) -> bool:
    """Identify navigation and display-only response names conservatively."""

    lowered = field.lower()
    return lowered in UI_ONLY_RESPONSE_FIELDS or lowered.endswith(
        UI_ONLY_RESPONSE_SUFFIXES
    )


def validate_api_semantics(component: object, contract: str) -> None:
    """Enforce data/business meaning before any derived file is generated."""

    api_type = component.api_type
    if api_type not in {"data", "business"}:
        raise ContractError("API Type must be exactly `data` or `business`")
    method, _ = api_operation(component)
    if api_type == "data":
        if "Business" in component.sections:
            raise ContractError("data API must remove the draft `Business:` section")
        section_bullets(component, "Data", DATA_FIELDS)
        if method in {"PUT", "PATCH", "DELETE"}:
            raise ContractError(
                f"data API cannot use state-changing HTTP method {method}"
            )
    else:
        if "Data" in component.sections:
            raise ContractError("business API must remove the draft `Data:` section")
        business = section_bullets(component, "Business", BUSINESS_FIELDS)
        if method == "GET":
            raise ContractError("business API cannot use GET for a command operation")
        if business["Navigation Ownership"] not in {"app", "none"}:
            raise ContractError(
                "Business `Navigation Ownership` must be `app` or `none`"
            )
        validate_failure_cases(business["Failure Cases"])

    if "BFF Runtime" in component.sections:
        raise ContractError(
            "BFF Runtime is obsolete; omit BFF Service for contract-only delivery "
            "or declare `BFF Service: [Type]` to reference the generated Dart class"
        )
    if not is_bff_mode(component):
        return
    requires_runtime = component.bff_service is not None
    if requires_runtime and not re.fullmatch(
        rf"\[({IDENTIFIER})\]", component.bff_service or ""
    ):
        raise ContractError(
            "BFF Service must be omitted for contract-only delivery or declared as "
            "`[Type]` to reference the generated Dart class"
        )
    if component.bff_service:
        pubspec = find_package_pubspec(Path(component.component_file))
        missing_retrofit = [
            package
            for package, section in (
                ("dio", "dependencies"),
                ("efficient_dio_logger", "dependencies"),
                ("retrofit", "dependencies"),
                ("build_runner", "dev_dependencies"),
                ("retrofit_generator", "dev_dependencies"),
            )
            if not has_direct_dependency(pubspec, package, section=section)
        ]
        if missing_retrofit:
            raise ContractError(
                f"{pubspec} must directly declare BFF Service dependencies: "
                + ", ".join(missing_retrofit)
            )

    api_lines = component.sections.get("BFF-API", [])
    refs = bracket_refs(api_lines)
    if requires_runtime and len(refs) != 2:
        raise ContractError(
            "BFF Service runtime integration currently supports exactly one "
            "request/response pair; split APIs into separate contracts or omit "
            "BFF Service for approved contract-only scope"
        )
    request_types = refs[0::2]
    response_types = refs[1::2]
    request_fields = {
        field for name in request_types for field in factory_fields(contract, name)
    }
    sources = request_field_sources(component)
    missing_sources = sorted(request_fields.difference(sources))
    unknown_sources = sorted(set(sources).difference(request_fields))
    if missing_sources:
        raise ContractError(
            "request fields missing source and purpose: " + ", ".join(missing_sources)
        )
    if unknown_sources:
        raise ContractError(
            "Request Field Sources references unknown request fields: "
            + ", ".join(unknown_sources)
        )

    if api_type != "business":
        return
    business = section_bullets(component, "Business", BUSINESS_FIELDS)
    success = business["Success Condition"]
    for response_type in response_types:
        response_fields = factory_fields(contract, response_type)
        business_fields = [
            field for field in response_fields if not is_ui_only_response_field(field)
        ]
        if not business_fields:
            raise ContractError(
                f"command response {response_type} contains only UI/navigation "
                "fields; add a business result field"
            )
        if not any(
            re.search(rf"\b{re.escape(field)}\b", success) for field in business_fields
        ):
            raise ContractError(
                "Business `Success Condition` must reference a non-UI field in "
                f"{response_type}: {', '.join(business_fields)}"
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


def registered_handler(
    vm_source: str, events: list[str], api_type: str
) -> tuple[str, str]:
    """Return the relevant registered Event and handler names."""

    suffixes = (
        BUSINESS_EVENT_SUFFIXES if api_type == "business" else DATA_EVENT_SUFFIXES
    )
    candidates = [event for event in events if event.endswith(suffixes)]
    for event in candidates:
        match = re.search(
            rf"\bon\s*<\s*{re.escape(event)}\s*>\s*\(\s*({IDENTIFIER})",
            vm_source,
        )
        if match:
            return event, match.group(1)
    kind = "command" if api_type == "business" else "load/refresh"
    raise ContractError(
        f"BFF Service runtime integration needs a registered asynchronous {kind} "
        "Event handler"
    )


def function_body(source: str, name: str) -> tuple[str, str]:
    """Return a named Dart function signature tail and brace body."""

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
        return signature, source[brace + 1 : body_end]
    raise ContractError(f"registered handler `{name}` must have a block body")


def validate_runtime_integration(component: object, contract: str) -> None:
    """Prove required BFF service execution in the final component sources."""

    if not is_bff_mode(component) or component.bff_service is None:
        return
    service = re.fullmatch(rf"\[({IDENTIFIER})\]", component.bff_service or "")
    if not service:
        raise ContractError("runtime integration has no valid BFF Service")
    service_type = service.group(1)
    component_file = Path(component.component_file)
    service_name = f"{component_file.stem}.srv.dart"
    if service_name not in component.imports:
        raise ContractError(
            f"BFF service must be imported as `import '{service_name}';`"
        )
    service_file = component_file.with_name(service_name)
    service_source = require_file(service_file, "BFF service")
    if not re.search(rf"\bclass\s+{re.escape(service_type)}\b", service_source):
        raise ContractError(f"BFF service does not declare class {service_type}")
    generated_name = f"{component_file.stem}.srv.g.dart"
    if f"part '{generated_name}';" not in service_source:
        raise ContractError(
            f"BFF service must declare `part '{generated_name}';`"
        )
    require_file(
        component_file.with_name(generated_name),
        "generated Retrofit service implementation",
    )

    if len(component.view_models) != 1:
        raise ContractError(
            "BFF Service runtime integration must declare exactly one ViewModel "
            "reference"
        )
    vm_class = component.view_models[0]
    vm_file = component_file.with_name(f"{component_file.stem}.vm.dart")
    vm_source = require_file(vm_file, "component ViewModel")
    service_field = declared_service_field(vm_source, vm_class, service_type)
    _, handler_name = registered_handler(
        vm_source, component.events, component.api_type or ""
    )
    signature, body = function_body(vm_source, handler_name)
    if "async" not in signature or not re.search(r"\bFuture(?:\s*<[^>]+>)?", signature):
        raise ContractError(
            f"BFF handler `{handler_name}` must return Future and be async"
        )

    refs = bracket_refs(component.sections.get("BFF-API", []))
    request_type, response_type = refs[0], refs[1]
    request = re.search(
        rf"\b(?:final|{re.escape(request_type)})\s+({IDENTIFIER})\s*=\s*"
        rf"{re.escape(request_type)}\s*\(",
        body,
    )
    inline_request = re.search(rf"{re.escape(request_type)}\s*\(", body)
    if not request and not inline_request:
        raise ContractError(
            f"BFF handler `{handler_name}` must construct {request_type}"
        )
    service_ref = rf"(?:this\.)?{re.escape(service_field)}"
    awaited = re.search(
        rf"\b(?:final|{re.escape(response_type)})\s+({IDENTIFIER})\s*=\s*"
        rf"await\s+{service_ref}\.({IDENTIFIER})\s*\(([^;]*)\)\s*;",
        body,
        re.DOTALL,
    )
    if not awaited:
        raise ContractError(
            f"BFF handler `{handler_name}` must await {service_type} and retain "
            f"the {response_type} result"
        )
    response_variable = awaited.group(1)
    call_arguments = awaited.group(3)
    if request and not re.search(rf"\b{re.escape(request.group(1))}\b", call_arguments):
        raise ContractError(
            f"BFF handler `{handler_name}` must pass its {request_type} to the service"
        )
    after_call = body[awaited.end() :]
    catch_index = after_call.find("catch")
    success_region = after_call if catch_index < 0 else after_call[:catch_index]
    response_fields = factory_fields(contract, response_type)
    used_fields = [
        field
        for field in response_fields
        if re.search(
            rf"\b{re.escape(response_variable)}\s*\.\s*{re.escape(field)}\b",
            success_region,
        )
    ]
    if not used_fields or not re.search(r"\bemit\s*\(", success_region):
        raise ContractError(
            f"BFF handler `{handler_name}` must use {response_type} fields to emit state"
        )

    model_fields = {
        field for model in component.models for field in factory_fields(contract, model)
    }
    if "isSubmitting" not in model_fields:
        raise ContractError(
            "BFF Service runtime integration model must expose `isSubmitting`"
        )
    if not any(FAILURE_FIELD.search(field) for field in model_fields):
        raise ContractError(
            "BFF Service runtime integration model must expose an error/failure state"
        )
    if not re.search(r"\btry\s*{", body) or not re.search(r"\bcatch\s*\(", body):
        raise ContractError(
            f"BFF handler `{handler_name}` must handle service failures with try/catch"
        )
    before_call = body[: awaited.start()]
    if not re.search(r"\bisSubmitting\s*:\s*true\b", before_call):
        raise ContractError(
            f"BFF handler `{handler_name}` must set isSubmitting true before the call"
        )
    finally_reset = re.search(
        r"\bfinally\s*{[\s\S]*?\bisSubmitting\s*:\s*false\b", after_call
    )
    success_reset = re.search(
        r"\bisSubmitting\s*:\s*false\b",
        after_call if catch_index < 0 else after_call[:catch_index],
    )
    failure_reset = (
        re.search(r"\bisSubmitting\s*:\s*false\b", after_call[catch_index:])
        if catch_index >= 0
        else None
    )
    if not finally_reset and not (success_reset and failure_reset):
        raise ContractError(
            f"BFF handler `{handler_name}` must restore isSubmitting after success "
            "and failure"
        )
    if catch_index < 0 or not re.search(
        r"\b(?:error|failure|validationMessage)\s*:",
        after_call[catch_index:],
        re.IGNORECASE,
    ):
        raise ContractError(
            f"BFF handler `{handler_name}` must emit a failure value for the UI"
        )

    navigation = re.compile(r"\bnextRoute\s*:|\.(?:go|push|replace)\s*\(")
    if navigation.search(before_call):
        raise ContractError(
            "navigation must not be triggered before the BFF success response"
        )
    if catch_index >= 0 and navigation.search(after_call[catch_index:]):
        raise ContractError(
            "navigation must not be triggered from the BFF failure path"
        )


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

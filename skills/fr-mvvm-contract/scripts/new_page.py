#!/usr/bin/env python3
"""Generate a contract-first FlowR page from a structured spec."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_IMPORTS = (
    "package:flowr/flowr_mvvm.dart",
    "package:freezed_annotation/freezed_annotation.dart",
    "package:flutter/material.dart",
)
DEFAULT_ENTRY_KIND = "page"
ENTRY_KINDS = ("page", "view")
CONTRACT_SECTION_PLACEMENTS = {
    "after_figma",
    "after_api",
    "after_route",
    "after_widget_tree",
    "after_models",
}
DEFAULT_CONTRACT_SECTION_ORDER = (
    "figma",
    "api",
    "state_ownership",
    "route",
    "reused_widgets",
    "widget_tree",
    "theme",
    "events",
    "view_models",
    "models",
    "bff_api",
)
API_NONE = "NONE"
API_BFF = "BFF"
API_BFF_JSON = "BFF-JSON"
API_BFF_PROTO = "BFF-PROTO"
EXPORT_PROTO = "proto"
EXPORT_JSON5 = "json5"
ARTIFACT_JSON = "JSON"
ARTIFACT_PROTO = "PROTO"
MODEL_PRESET_STATE = "state"
MODEL_PRESET_STATE_JSON = "state_json"
MODEL_PRESET_PLAIN = "plain"
SKIP_DIRS = {".dart_tool", ".git", ".idea", ".vscode", "build", "ios/Pods"}


class SpecError(ValueError):
    """Raised when the page spec is invalid."""


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / "melos.yaml").exists():
            return candidate
    for candidate in (current, *current.parents):
        if (candidate / "pubspec.yaml").exists():
            return candidate
    return current


def path_is_skipped(path: Path) -> bool:
    parts = set(path.parts)
    if parts.intersection(SKIP_DIRS):
        return True
    return "Pods" in parts and "ios" in parts


def page_root_from_path(path: Path) -> Path | None:
    parts = path.parts
    for index, part in enumerate(parts):
        if part != "lib":
            continue
        if index + 1 < len(parts) and parts[index + 1] == "page":
            return Path(*parts[: index + 2])
        if (
            index + 2 < len(parts)
            and parts[index + 1] == "src"
            and parts[index + 2] == "page"
        ):
            return Path(*parts[: index + 3])
    return None


def contract_page_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.dart"):
        if not path.is_file() or path_is_skipped(path):
            continue
        if not path.name.endswith(("_page.dart", "_view.dart")):
            continue
        if path.name.endswith(".v.dart") or path.name.endswith(".vm.dart"):
            continue
        if page_root_from_path(path) is None:
            continue
        files.append(path)
    return files


def infer_page_root(project_root: Path) -> Path:
    lib_page = project_root / "lib/page"
    lib_src_page = project_root / "lib/src/page"

    counts: Counter[Path] = Counter()
    for path in contract_page_files(project_root):
        page_root = page_root_from_path(path)
        if page_root is not None:
            counts[page_root] += 1

    if counts:
        return sorted(
            counts,
            key=lambda path: (
                -counts[path],
                0 if path == lib_page else 1 if path == lib_src_page else 2,
                len(path.parts),
                str(path),
            ),
        )[0]

    if lib_src_page.exists() and not lib_page.exists():
        return lib_src_page

    return lib_page


def resolve_relative_to_root(path: Path, project_root: Path) -> Path:
    return path if path.is_absolute() else project_root / path


def ensure_relative(path: Path, option: str) -> Path:
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{option} must be a relative path below the page root")
    return path


def display_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def tokenize_name(value: str) -> list[str]:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value.strip())
    parts = [part.lower() for part in re.findall(r"[A-Za-z0-9]+", normalized)]
    if not parts:
        raise ValueError("name must contain at least one letter or number")
    return parts


def pascal_from_parts(parts: list[str]) -> str:
    return "".join(part[:1].upper() + part[1:] for part in parts)


def snake_from_parts(parts: list[str]) -> str:
    return "_".join(parts)


def normalize_entry_kind(value: Any, path: str) -> str | None:
    if value is None:
        return None
    kind = require_str(value, path).lower()
    if kind not in ENTRY_KINDS:
        allowed = ", ".join(ENTRY_KINDS)
        raise SpecError(f"{path} must be one of: {allowed}")
    return kind


def split_name_parts(value: str, *, kind: str | None = None) -> tuple[list[str], str]:
    if kind is not None and kind not in ENTRY_KINDS:
        allowed = ", ".join(ENTRY_KINDS)
        raise ValueError(f"kind must be one of: {allowed}")
    parts = tokenize_name(value)
    inferred_kind = parts[-1] if parts[-1] in ENTRY_KINDS else None
    base_parts = parts[:-1] if inferred_kind is not None else parts
    if not base_parts:
        raise ValueError("name must contain at least one segment before the suffix")
    return base_parts, kind or inferred_kind or DEFAULT_ENTRY_KIND


def build_page_naming(value: str, *, kind: str | None = None) -> dict[str, str]:
    base_parts, resolved_kind = split_name_parts(value, kind=kind)
    base_name = pascal_from_parts(base_parts)
    widget_name = pascal_from_parts([*base_parts, resolved_kind])
    file_name = snake_from_parts([*base_parts, resolved_kind])

    if resolved_kind == "page":
        primary_model_name = f"{widget_name}Model"
        primary_vm_name = f"{widget_name}ViewModel"
        event_base_name = f"{widget_name}Event"
        theme_name = f"{widget_name}Theme"
        entry_widget_name = f"_{widget_name}View"
    else:
        primary_model_name = f"{base_name}Model"
        primary_vm_name = f"{base_name}ViewModel"
        event_base_name = f"{base_name}Event"
        theme_name = f"{base_name}Theme"
        entry_widget_name = f"_{widget_name}Body"

    return {
        "kind": resolved_kind,
        "base_name": base_name,
        "name": widget_name,
        "file_name": file_name,
        "primary_model_name": primary_model_name,
        "primary_vm_name": primary_vm_name,
        "event_base_name": event_base_name,
        "theme_name": theme_name,
        "entry_widget_name": entry_widget_name,
    }


def snake_name(value: str, *, kind: str | None = None) -> str:
    return build_page_naming(value, kind=kind)["file_name"]


def pascal_name(value: str, *, kind: str | None = None) -> str:
    return build_page_naming(value, kind=kind)["name"]


def indent_block(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else "" for line in text.splitlines())


def doc_comment(text: str | None, spaces: int = 0) -> str:
    if not text or not text.strip():
        return ""
    prefix = " " * spaces
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(f"{prefix}/// {line}" if line else f"{prefix}///" for line in lines)


def clean_code(text: str, path: str) -> str:
    value = text.strip("\n")
    if not value.strip():
        raise SpecError(f"{path} must not be empty")
    return value


def require_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SpecError(f"{path} must be an object")
    return value


def require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise SpecError(f"{path} must be an array")
    return value


def require_str(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SpecError(f"{path} must be a non-empty string")
    return value.strip()


def optional_str(value: Any, path: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SpecError(f"{path} must be a string")
    stripped = value.strip()
    return stripped or None


def optional_code(value: Any, path: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise SpecError(f"{path} must be a string")
    return clean_code(value, path)


def optional_bool(value: Any, path: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise SpecError(f"{path} must be a boolean")
    return value


def parse_api_reference(value: Any, path: str) -> dict[str, str | None]:
    reference = require_str(value, path)
    upper = reference.upper()
    if upper == API_NONE:
        return {"api_reference": API_NONE, "artifact_type": None}
    if upper == API_BFF:
        return {"api_reference": API_BFF, "artifact_type": None}
    if upper == API_BFF_JSON:
        return {"api_reference": API_BFF, "artifact_type": ARTIFACT_JSON}
    if upper == API_BFF_PROTO:
        return {"api_reference": API_BFF, "artifact_type": ARTIFACT_PROTO}
    return {"api_reference": reference, "artifact_type": None}


def parse_export_format(value: Any, path: str) -> str | None:
    if value is None:
        return None
    artifact_type = require_str(value, path).upper()
    if artifact_type not in (ARTIFACT_JSON, ARTIFACT_PROTO):
        raise SpecError(f"{path} must be `JSON` or `PROTO`")
    return artifact_type


def cli_format_for_artifact_type(artifact_type: str) -> str:
    if artifact_type == ARTIFACT_JSON:
        return EXPORT_JSON5
    if artifact_type == ARTIFACT_PROTO:
        return EXPORT_PROTO
    raise SpecError(f"unsupported artifact type `{artifact_type}`")


def compose_inline_section(primary: str, extra: str | list[str] | None) -> str:
    values = [primary]
    if isinstance(extra, str):
        if extra and extra != primary:
            values.append(extra)
    elif extra:
        values.extend(item for item in extra if item and item != primary)
    return " | ".join(values)


def require_identifier(value: Any, path: str) -> str:
    identifier = require_str(value, path)
    if not re.fullmatch(r"[A-Za-z_]\w*", identifier):
        raise SpecError(f"{path} must be a valid Dart identifier")
    return identifier


def normalize_imports(value: Any) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = [{"uri": uri} for uri in DEFAULT_IMPORTS]
    if value is None:
        return entries

    seen: set[tuple[Any, ...]] = {
        ("uri", item["uri"], None, (), ()) for item in entries
    }
    for index, item in enumerate(require_list(value, "page.imports")):
        path = f"page.imports[{index}]"
        if isinstance(item, str):
            entry = {"uri": require_str(item, path)}
        elif isinstance(item, dict):
            data = require_dict(item, path)
            show_items = data.get("show")
            hide_items = data.get("hide")
            if show_items is not None and hide_items is not None:
                raise SpecError(f"{path} cannot define both show and hide")
            show = (
                [require_identifier(name, f"{path}.show[{i}]") for i, name in enumerate(require_list(show_items, f"{path}.show"))]
                if show_items is not None
                else []
            )
            hide = (
                [require_identifier(name, f"{path}.hide[{i}]") for i, name in enumerate(require_list(hide_items, f"{path}.hide"))]
                if hide_items is not None
                else []
            )
            entry = {
                "uri": require_str(data.get("uri"), f"{path}.uri"),
                "as": optional_str(data.get("as"), f"{path}.as"),
                "show": show,
                "hide": hide,
            }
        else:
            raise SpecError(f"{path} must be a string or object")

        key = (
            "uri",
            entry["uri"],
            entry.get("as"),
            tuple(entry.get("show", [])),
            tuple(entry.get("hide", [])),
        )
        if key in seen:
            continue
        seen.add(key)
        entries.append(entry)
    return entries


def render_import(entry: dict[str, Any]) -> str:
    line = f"import '{entry['uri']}'"
    if entry.get("as"):
        line += f" as {entry['as']}"
    if entry.get("show"):
        line += " show " + ", ".join(entry["show"])
    if entry.get("hide"):
        line += " hide " + ", ".join(entry["hide"])
    return line + ";"


def parse_line_list(value: Any, path: str) -> list[str]:
    return [require_str(item, f"{path}[{index}]") for index, item in enumerate(require_list(value, path))]


def parse_optional_text_block(value: Any, path: str) -> str | list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return optional_str(value, path)
    return parse_line_list(value, path)


def parse_state_ownership(value: Any) -> str | list[str]:
    if value is None:
        return "none"
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise SpecError("page.state_ownership must not be empty")
        return stripped
    return parse_line_list(value, "page.state_ownership")


def parse_refs(value: Any, path: str) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for index, item in enumerate(require_list(value, path)):
        entry = require_dict(item, f"{path}[{index}]")
        refs.append(
            {
                "name": require_identifier(entry.get("name"), f"{path}[{index}].name"),
                "description": require_str(
                    entry.get("description"),
                    f"{path}[{index}].description",
                ),
            }
        )
    return refs


def parse_field(item: Any, path: str, *, allow_named: bool = False) -> dict[str, Any]:
    data = require_dict(item, path)
    default = optional_str(data.get("default"), f"{path}.default")
    required = data.get("required")
    if required is None:
        required_value = default is None
    elif isinstance(required, bool):
        required_value = required
    else:
        raise SpecError(f"{path}.required must be a boolean")
    named = data.get("named", False)
    if not isinstance(named, bool):
        raise SpecError(f"{path}.named must be a boolean")
    if named and not allow_named:
        raise SpecError(f"{path}.named is only supported for event fields")
    if default is not None and required_value:
        raise SpecError(f"{path} cannot be required when a default is provided")
    return {
        "name": require_identifier(data.get("name"), f"{path}.name"),
        "type": require_str(data.get("type"), f"{path}.type"),
        "default": default,
        "required": required_value,
        "named": named,
    }


def parse_fields(value: Any, path: str, *, allow_named: bool = False) -> list[dict[str, Any]]:
    return [
        parse_field(item, f"{path}[{index}]", allow_named=allow_named)
        for index, item in enumerate(require_list(value, path))
    ]


def parse_members(value: Any, path: str) -> list[str]:
    return [clean_code(item, f"{path}[{index}]") for index, item in enumerate(require_list(value, path))]


def parse_code_list(value: Any, path: str) -> list[str]:
    return [
        clean_code(require_str(item, f"{path}[{index}]"), f"{path}[{index}]")
        for index, item in enumerate(require_list(value, path))
    ]


def parse_field_annotation(value: Any, path: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return optional_str(value, path)
    annotations = parse_code_list(value, path)
    return "\n".join(annotations) if annotations else None


def parse_string_map(value: Any, path: str) -> dict[str, str]:
    if value is None:
        return {}
    data = require_dict(value, path)
    return {str(key): require_str(item, f"{path}.{key}") for key, item in data.items()}


def parse_optional_bool_alias(
    data: dict[str, Any],
    snake_name: str,
    camel_name: str,
    path: str,
) -> bool | None:
    snake_value = data.get(snake_name)
    camel_value = data.get(camel_name)
    if snake_value is not None and camel_value is not None and snake_value != camel_value:
        raise SpecError(f"{path}.{snake_name} conflicts with {path}.{camel_name}")
    return optional_bool(
        snake_value if snake_value is not None else camel_value,
        f"{path}.{snake_name}",
    )


def reject_members(value: Any, path: str, target: str) -> None:
    """Reject helper members that must live in the VM file instead."""

    members = require_list(value, path)
    if members:
        raise SpecError(
            f"{path} is not supported; move {target} helper methods into "
            "`view_model.members` or `view_model.methods` so they render in `.vm.dart`"
        )


def parse_theme(value: Any, theme_name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    data = require_dict(value, "page.theme")
    fields = parse_fields(data.get("fields", []), "page.theme.fields")
    return {
        "name": theme_name,
        "doc": optional_str(data.get("doc"), "page.theme.doc"),
        "declaration": optional_code(
            data.get("declaration"),
            "page.theme.declaration",
        ),
        "fields": fields,
        "members": parse_members(data.get("members", []), "page.theme.members"),
    }


def parse_contract_section(item: Any, path: str) -> dict[str, Any]:
    data = require_dict(item, path)
    section_id = optional_str(data.get("id"), f"{path}.id")
    label = optional_str(data.get("label"), f"{path}.label")
    lines = parse_optional_text_block(data.get("lines"), f"{path}.lines")
    style = optional_str(data.get("style"), f"{path}.style") or "raw"
    if style not in {"raw", "list"}:
        raise SpecError(f"{path}.style must be `raw` or `list`")
    placement = optional_str(data.get("placement"), f"{path}.placement")
    if placement is not None and placement not in CONTRACT_SECTION_PLACEMENTS:
        allowed = ", ".join(sorted(CONTRACT_SECTION_PLACEMENTS))
        raise SpecError(f"{path}.placement must be one of: {allowed}")
    if section_id is None and label is None:
        raise SpecError(f"{path} must define either id or label")
    if lines is None and label is not None and section_id is None:
        raise SpecError(f"{path}.lines is required for custom contract sections")
    return {
        "id": section_id,
        "label": label,
        "lines": lines,
        "placement": placement,
        "style": style,
    }


def parse_contract(value: Any) -> dict[str, Any]:
    data = require_dict(value or {}, "page.contract")
    section_order = data.get("sectionOrder", data.get("section_order"))
    disabled_sections = data.get("disabledSections", data.get("disabled_sections"))
    return {
        "section_labels": parse_string_map(
            data.get("sectionLabels", data.get("section_labels")),
            "page.contract.sectionLabels",
        ),
        "section_order": (
            parse_line_list(section_order, "page.contract.sectionOrder")
            if section_order is not None
            else list(DEFAULT_CONTRACT_SECTION_ORDER)
        ),
        "disabled_sections": set(
            parse_line_list(disabled_sections, "page.contract.disabledSections")
            if disabled_sections is not None
            else []
        ),
        "sections": [
            parse_contract_section(item, f"page.contract.sections[{index}]")
            for index, item in enumerate(
                require_list(data.get("sections", []), "page.contract.sections")
            )
        ],
        "root_annotations": parse_code_list(
            data.get("rootAnnotations", data.get("root_annotations", [])),
            "page.contract.rootAnnotations",
        ),
        "extra_declarations": parse_code_list(
            data.get("extraDeclarations", data.get("extra_declarations", [])),
            "page.contract.extraDeclarations",
        ),
    }


def parse_model_preset(value: Any, path: str) -> str:
    if value is None:
        return MODEL_PRESET_STATE
    preset = require_str(value, path).lower()
    if preset not in (
        MODEL_PRESET_STATE,
        MODEL_PRESET_STATE_JSON,
        MODEL_PRESET_PLAIN,
    ):
        raise SpecError(f"{path} must be `state`, `state_json`, or `plain`")
    return preset


def parse_models(value: Any, primary_model_name: str) -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    raw_models = value
    if raw_models is None:
        raw_models = [
            {
                "name": primary_model_name,
                "description": "primary page state",
                "fields": [],
            }
        ]
    for index, item in enumerate(require_list(raw_models, "models")):
        path = f"models[{index}]"
        data = require_dict(item, path)
        reject_members(data.get("members", []), f"{path}.members", "model")
        from_json = parse_optional_bool_alias(data, "from_json", "fromJson", path)
        models.append(
            {
                "name": require_identifier(data.get("name"), f"{path}.name"),
                "doc": optional_str(data.get("doc"), f"{path}.doc"),
                "description": require_str(
                    data.get("description"),
                    f"{path}.description",
                ),
                "preset": parse_model_preset(data.get("preset"), f"{path}.preset"),
                "fields": parse_fields(data.get("fields", []), f"{path}.fields"),
                "annotations": parse_code_list(
                    data.get("annotations", []),
                    f"{path}.annotations",
                ),
                "field_annotations": [
                    parse_field_annotation(
                        require_dict(field, f"{path}.fields[{field_index}]").get(
                            "annotation",
                            require_dict(field, f"{path}.fields[{field_index}]").get(
                                "annotations"
                            ),
                        ),
                        f"{path}.fields[{field_index}].annotation",
                    )
                    for field_index, field in enumerate(
                        require_list(data.get("fields", []), f"{path}.fields")
                    )
                ],
                "from_json": bool(from_json),
                "members": [],
            }
        )
    if not models:
        raise SpecError("models must contain at least one model")
    if primary_model_name not in {model["name"] for model in models}:
        raise SpecError(
            f"models must include the primary page model `{primary_model_name}`"
        )
    return models


def parse_events(value: Any, event_base_name: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    raw_events = value
    if raw_events is None:
        raw_events = [
            {
                "name": event_base_name.removesuffix("Event") + "Started",
                "description": "bootstrap the page",
            }
        ]
    for index, item in enumerate(require_list(raw_events, "events")):
        path = f"events[{index}]"
        data = require_dict(item, path)
        items.append(
            {
                "name": require_identifier(data.get("name"), f"{path}.name"),
                "doc": optional_str(data.get("doc"), f"{path}.doc"),
                "description": require_str(
                    data.get("description"),
                    f"{path}.description",
                ),
                "fields": parse_fields(
                    data.get("fields", []),
                    f"{path}.fields",
                    allow_named=True,
                ),
            }
        )
    if not items:
        raise SpecError("events must contain at least one event")
    return {"base_name": event_base_name, "items": items}


def parse_view_model(
    value: Any,
    primary_vm_name: str,
    primary_model_name: str,
) -> dict[str, Any]:
    data = require_dict(value or {}, "view_model")
    dependencies = parse_fields(data.get("dependencies", []), "view_model.dependencies")
    handlers: list[dict[str, str]] = []
    for index, item in enumerate(require_list(data.get("event_handlers", []), "view_model.event_handlers")):
        path = f"view_model.event_handlers[{index}]"
        entry = require_dict(item, path)
        is_async = entry.get("is_async", False)
        if not isinstance(is_async, bool):
            raise SpecError(f"{path}.is_async must be a boolean")
        handlers.append(
            {
                "event": require_identifier(entry.get("event"), f"{path}.event"),
                "body": clean_code(require_str(entry.get("body"), f"{path}.body"), f"{path}.body"),
                "is_async": is_async,
            }
        )
    methods: list[dict[str, str | None]] = []
    for index, item in enumerate(require_list(data.get("methods", []), "view_model.methods")):
        path = f"view_model.methods[{index}]"
        entry = require_dict(item, path)
        methods.append(
            {
                "signature": require_str(entry.get("signature"), f"{path}.signature"),
                "doc": optional_str(entry.get("doc"), f"{path}.doc"),
                "body": clean_code(require_str(entry.get("body"), f"{path}.body"), f"{path}.body"),
            }
        )
    return {
        "name": primary_vm_name,
        "description": optional_str(data.get("description"), "view_model.description")
        or "primary page view model",
        "doc": optional_str(data.get("doc"), "view_model.doc"),
        "dependencies": dependencies,
        "initial_state": optional_str(data.get("initial_state"), "view_model.initial_state")
        or f"const {primary_model_name}()",
        "event_handlers": handlers,
        "members": parse_members(data.get("members", []), "view_model.members"),
        "methods": methods,
    }


def parse_widget(item: Any, path: str) -> dict[str, Any]:
    data = require_dict(item, path)
    base_class = optional_str(data.get("base_class"), f"{path}.base_class") or "StatelessWidget"
    if base_class != "StatelessWidget":
        raise SpecError(f"{path}.base_class currently only supports StatelessWidget")
    reject_members(data.get("members", []), f"{path}.members", "view")
    return {
        "name": require_identifier(data.get("name"), f"{path}.name"),
        "doc": optional_str(data.get("doc"), f"{path}.doc"),
        "fields": parse_fields(data.get("fields", []), f"{path}.fields"),
        "members": [],
        "build": clean_code(require_str(data.get("build"), f"{path}.build"), f"{path}.build"),
        "include_key": optional_bool(data.get("include_key"), f"{path}.include_key"),
    }


def parse_view(value: Any, entry_widget_name: str) -> dict[str, Any]:
    data = require_dict(value or {}, "view")
    entry = require_dict(
        data.get("entry", {"build": "return const SizedBox.shrink();"}),
        "view.entry",
    )
    widgets = [parse_widget(item, f"view.widgets[{index}]") for index, item in enumerate(require_list(data.get("widgets", []), "view.widgets"))]
    return {
        "entry_widget_name": entry_widget_name,
        "entry_doc": optional_str(entry.get("doc"), "view.entry.doc"),
        "entry_build": clean_code(
            require_str(entry.get("build"), "view.entry.build"),
            "view.entry.build",
        ),
        "widgets": widgets,
    }


def parse_page(value: Any) -> dict[str, Any]:
    data = require_dict(value, "page")
    try:
        page_naming = build_page_naming(
            require_str(data.get("name"), "page.name"),
            kind=normalize_entry_kind(data.get("kind"), "page.kind"),
        )
    except ValueError as error:
        raise SpecError(f"page.name {error}") from error
    provider = require_dict(data.get("provider", {}), "page.provider")
    figma_url = require_str(data.get("figmaUrl"), "page.figmaUrl")
    figma_notes = parse_optional_text_block(data.get("figma"), "page.figma")
    api_info = parse_api_reference(data.get("api"), "page.api")
    api_reference = api_info["api_reference"]
    raw_api_contract = data.get("apiContract")
    api_contract = (
        parse_optional_text_block(raw_api_contract, "page.apiContract")
        if raw_api_contract is not None
        else None
    )
    if api_reference == API_BFF and (
        api_contract is None or (isinstance(api_contract, list) and not api_contract)
    ):
        raise SpecError(
            "page.apiContract is required when page.api resolves to BFF"
        )
    artifact_type = parse_export_format(
        data.get("exportFormat"),
        "page.exportFormat",
    )
    api_artifact_type = api_info["artifact_type"]
    if (
        api_artifact_type is not None
        and artifact_type is not None
        and artifact_type != api_artifact_type
    ):
        raise SpecError(
            "page.exportFormat conflicts with the shorthand embedded in page.api"
        )
    if api_reference != API_BFF and artifact_type is not None:
        raise SpecError("page.exportFormat is only valid when page.api is BFF")
    resolved_artifact_type = (
        artifact_type
        or api_artifact_type
        or (ARTIFACT_JSON if api_reference == API_BFF else None)
    )
    rendered_api = api_contract
    if rendered_api is None and api_reference != API_NONE:
        rendered_api = api_reference

    return {
        **page_naming,
        "figma_url": figma_url,
        "figma": compose_inline_section(figma_url, figma_notes),
        "api_reference": api_reference,
        "api": rendered_api,
        "artifact_type": resolved_artifact_type,
        "export_format": (
            cli_format_for_artifact_type(resolved_artifact_type)
            if resolved_artifact_type is not None
            else None
        ),
        "route": optional_str(data.get("route"), "page.route"),
        "imports": normalize_imports(data.get("imports")),
        "provider": {
            "create": optional_str(provider.get("create"), "page.provider.create"),
            "lazy": optional_bool(provider.get("lazy"), "page.provider.lazy"),
            "on_created": optional_str(
                provider.get("on_created"),
                "page.provider.on_created",
            ),
        },
        "state_ownership": parse_state_ownership(data.get("state_ownership")),
        "reused_widgets": parse_line_list(
            data.get("reused_widgets", []),
            "page.reused_widgets",
        ),
        "widget_tree": (
            parse_line_list(data.get("widget_tree"), "page.widget_tree")
            if data.get("widget_tree") is not None
            else [f"[{page_naming['name']}]", f"[{page_naming['entry_widget_name']}]"]
        ),
        "external_view_models": parse_refs(
            data.get("external_view_models", []),
            "page.external_view_models",
        ),
        "external_models": parse_refs(
            data.get("external_models", []),
            "page.external_models",
        ),
        "theme": parse_theme(data.get("theme"), page_naming["theme_name"]),
        "contract": parse_contract(data.get("contract")),
    }


def load_spec(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise SystemExit(f"{path} does not exist") from error
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid JSON in {path}: {error}") from error
    spec = require_dict(data, "spec")
    page = parse_page(spec.get("page"))
    return {
        "page": page,
        "models": parse_models(spec.get("models"), page["primary_model_name"]),
        "events": parse_events(spec.get("events"), page["event_base_name"]),
        "view_model": parse_view_model(
            spec.get("view_model"),
            page["primary_vm_name"],
            page["primary_model_name"],
        ),
        "view": parse_view(spec.get("view"), page["entry_widget_name"]),
    }


def section_lines(label: str, value: str | list[str] | None) -> list[str]:
    if value is None:
        return [f"/// {label}: none"]
    if isinstance(value, str):
        return [f"/// {label}: {value}" if value else f"/// {label}: none"]
    if not value:
        return [f"/// {label}: none"]
    lines = [f"/// {label}:"]
    for block in value:
        entries = [line.rstrip() for line in block.splitlines() if line.strip()]
        if not entries:
            continue
        first_entry = entries[0]
        if label == "BFF-API":
            first_entry = re.sub(
                r"(<BASE>/\S+)",
                r"`\1`",
                first_entry,
            )
        lines.append(f"/// - {first_entry}")
        lines.extend(f"///   {entry}" for entry in entries[1:])
    return lines


def state_ownership_lines(value: str | list[str]) -> list[str]:
    if isinstance(value, str):
        if value.strip().lower() == "none":
            return ["/// State Ownership: none"]
        return ["/// State Ownership:", f"/// - {value.strip()}"]
    if not value:
        return ["/// State Ownership: none"]
    return ["/// State Ownership:", *(f"/// - {line}" for line in value)]


def list_section_lines(label: str, items: list[str]) -> list[str]:
    if not items:
        return [f"/// {label}: none"]
    return [f"/// {label}:", *(f"/// - {item}" for item in items)]


def ref_section_lines(label: str, refs: list[dict[str, str]]) -> list[str]:
    if not refs:
        return [f"/// {label}: none"]
    return [
        f"/// {label}:",
        *(f"/// - [{ref['name']}]: {ref['description']}" for ref in refs),
    ]


def event_section_lines(events: dict[str, Any]) -> list[str]:
    return [
        f"/// Events: [{events['base_name']}]",
        *(
            f"/// - [{item['name']}]: {item['description']}"
            for item in events["items"]
        ),
    ]


def render_named_constructor(
    class_name: str,
    fields: list[dict[str, Any]],
    *,
    include_key: bool = False,
) -> str:
    params: list[str] = []
    for field in fields:
        if field["default"] is not None:
            params.append(f"this.{field['name']} = {field['default']}")
        elif field["required"]:
            params.append(f"required this.{field['name']}")
        else:
            params.append(f"this.{field['name']}")
    if include_key:
        params.append("super.key")
    if not params:
        return f"const {class_name}();"
    if len(params) == 1 and not include_key:
        return f"const {class_name}({{{params[0]}}});"
    body = ",\n".join(f"    {param}" for param in params)
    return f"const {class_name}({{\n{body},\n  }});"


def render_event_constructor(class_name: str, fields: list[dict[str, Any]]) -> str:
    positional = [
        field
        for field in fields
        if not field["named"]
    ]
    named = [field for field in fields if field["named"]]
    params: list[str] = []
    params.extend(f"this.{field['name']}" for field in positional)
    if named:
        named_params: list[str] = []
        for field in named:
            if field["default"] is not None:
                named_params.append(f"this.{field['name']} = {field['default']}")
            elif field["required"]:
                named_params.append(f"required this.{field['name']}")
            else:
                named_params.append(f"this.{field['name']}")
        params.append("{")
        params.extend(named_params)
        params.append("}")
    if not params:
        return f"const {class_name}();"
    if "{" not in params and len(params) == 1:
        return f"const {class_name}({params[0]});"

    lines: list[str] = []
    index = 0
    while index < len(params):
        token = params[index]
        if token == "{":
            lines.append("    {")
            index += 1
            while index < len(params) and params[index] != "}":
                lines.append(f"      {params[index]},")
                index += 1
            lines.append("    }")
        else:
            lines.append(f"    {token},")
        index += 1
    body = "\n".join(lines)
    return f"const {class_name}(\n{body}\n  );"


def render_view_model_constructor(
    class_name: str,
    dependencies: list[dict[str, Any]],
    initial_state: str,
) -> str:
    if not dependencies:
        return f"{class_name}() : super({initial_state}) {{"

    params: list[str] = []
    for field in dependencies:
        if field["default"] is not None:
            params.append(f"this.{field['name']} = {field['default']}")
        elif field["required"]:
            params.append(f"required this.{field['name']}")
        else:
            params.append(f"this.{field['name']}")
    body = ",\n".join(f"    {param}" for param in params)
    return (
        f"{class_name}({{\n"
        f"{body},\n"
        f"  }}) : super({initial_state}) {{"
    )


def render_page_class(page: dict[str, Any]) -> str:
    create_expr = page["provider"]["create"] or f"{page['primary_vm_name']}()"
    lazy = page["provider"]["lazy"]
    on_created = page["provider"]["on_created"]

    provider_lines = [
        "return FrProvider(",
        f"  (context) => {create_expr},",
    ]
    if lazy is not None:
        provider_lines.append(f"  lazy: {'true' if lazy else 'false'},")
    if on_created:
        provider_lines.append("  onCreated: (context, vm) {")
        provider_lines.append(indent_block(on_created, 4))
        provider_lines.append("  },")
    provider_lines.append(f"  child: const {page['entry_widget_name']}(),")
    provider_lines.append(");")
    build_body = indent_block("\n".join(provider_lines), 4)

    return "\n".join(
        (
            f"class {page['name']} extends StatelessWidget {{",
            f"  const {page['name']}({{super.key}});",
            "",
            "  @override",
            "  Widget build(BuildContext context) {",
            build_body,
            "  }",
            "}",
        )
    )


def render_theme_class(theme: dict[str, Any]) -> str:
    parts: list[str] = []
    if comment := doc_comment(theme["doc"]):
        parts.append(comment)
    if declaration := theme["declaration"]:
        declaration_lines = [
            line.rstrip() for line in declaration.splitlines() if line.strip()
        ]
        if not declaration_lines[-1].rstrip().endswith("{"):
            declaration_lines[-1] = declaration_lines[-1].rstrip() + " {"
        parts.extend(declaration_lines)
    else:
        parts.append(f"class {theme['name']} {{")
    if theme["fields"]:
        parts.extend(f"  final {field['type']} {field['name']};" for field in theme["fields"])
        parts.append("")
    parts.append(indent_block(render_named_constructor(theme["name"], theme["fields"]), 2))
    for member in theme["members"]:
        parts.append("")
        parts.append(indent_block(member, 2))
    parts.append("}")
    return "\n".join(parts)


def is_nullable_type(type_name: str) -> bool:
    return type_name.rstrip().endswith("?")


def render_freezed_model_fields(model: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    field_annotations = model.get("field_annotations", [])
    for index, field in enumerate(model["fields"]):
        if index < len(field_annotations) and field_annotations[index]:
            for annotation_line in str(field_annotations[index]).splitlines():
                if annotation_line.strip():
                    lines.append(f"    {annotation_line.rstrip()}")
        if field["default"] is not None:
            if field["default"] == "null":
                if not is_nullable_type(field["type"]):
                    raise SpecError(
                        f"model field `{model['name']}.{field['name']}` uses `default: null` "
                        "but the type is not nullable"
                    )
                lines.append(f"    {field['type']} {field['name']},")
                continue
            lines.append(
                f"    @Default({field['default']}) {field['type']} {field['name']},"
            )
            continue
        if field["required"]:
            lines.append(f"    required {field['type']} {field['name']},")
            continue
        if not is_nullable_type(field["type"]):
            raise SpecError(
                f"model field `{model['name']}.{field['name']}` must be required, "
                "nullable, or define a default when generated with `@Freezed(...)`"
            )
        lines.append(f"    {field['type']} {field['name']},")
    return lines


def render_model_class(model: dict[str, Any]) -> str:
    parts: list[str] = []
    if comment := doc_comment(model["doc"]):
        parts.append(comment)
    if model.get("annotations"):
        parts.extend(model["annotations"])
    elif model["preset"] == MODEL_PRESET_STATE:
        parts.append("@FrState")
    elif model["preset"] == MODEL_PRESET_STATE_JSON:
        parts.append("@FrStateJson")
    else:
        parts.append("@Freezed(")
        parts.append("  copyWith: true,")
        parts.append("  equal: true,")
        parts.append("  toStringOverride: true,")
        parts.append("  fromJson: false,")
        parts.append("  toJson: false,")
        parts.append(")")
    parts.append(f"class {model['name']} with _${model['name']} {{")
    parts.append(f"  const {model['name']}._();")
    parts.append("")
    if model["preset"] == MODEL_PRESET_STATE_JSON or model.get("from_json"):
        parts.append(
            f"  factory {model['name']}.fromJson(Map<String, dynamic> json) => "
            f"_${model['name']}FromJson(json);"
        )
        parts.append("")
    if model["fields"]:
        parts.append(f"  const factory {model['name']}({{")
        parts.extend(render_freezed_model_fields(model))
        parts.append(f"  }}) = _{model['name']};")
    else:
        parts.append(f"  const factory {model['name']}() = _{model['name']};")
    for member in model["members"]:
        parts.append("")
        parts.append(indent_block(member, 2))
    parts.append("}")
    return "\n".join(parts)


def render_event_class(event: dict[str, Any], event_base_name: str) -> str:
    parts: list[str] = []
    if comment := doc_comment(event["doc"]):
        parts.append(comment)
    parts.append(f"class {event['name']} extends {event_base_name} {{")
    if event["fields"]:
        parts.extend(f"  final {field['type']} {field['name']};" for field in event["fields"])
        parts.append("")
    parts.append(indent_block(render_event_constructor(event["name"], event["fields"]), 2))
    parts.append("}")
    return "\n".join(parts)


def render_view_model_class(
    page: dict[str, Any],
    view_model: dict[str, Any],
    events: dict[str, Any],
) -> str:
    parts: list[str] = []
    if comment := doc_comment(view_model["doc"]):
        parts.append(comment)
    parts.append(
        f"class {view_model['name']} "
        f"extends FrBlocViewModel<{events['base_name']}, {page['primary_model_name']}> {{"
    )
    if view_model["dependencies"]:
        parts.extend(
            f"  final {field['type']} {field['name']};"
            for field in view_model["dependencies"]
        )
        parts.append("")
    constructor = render_view_model_constructor(
        view_model["name"],
        view_model["dependencies"],
        view_model["initial_state"],
    )
    parts.append(indent_block(constructor, 2))
    for handler in view_model["event_handlers"]:
        async_modifier = " async" if handler["is_async"] else ""
        parts.append(
            f"    on<{handler['event']}>((event, emit){async_modifier} {{"
        )
        parts.append(indent_block(handler["body"], 6))
        parts.append("    });")
    parts.append("  }")
    for member in view_model["members"]:
        parts.append("")
        parts.append(indent_block(member, 2))
    for method in view_model["methods"]:
        parts.append("")
        if comment := doc_comment(method["doc"], 2):
            parts.append(comment)
        parts.append(f"  {method['signature']} {{")
        parts.append(indent_block(str(method["body"]), 4))
        parts.append("  }")
    parts.append("}")
    return "\n".join(parts)


def render_widget_class(widget: dict[str, Any]) -> str:
    parts: list[str] = []
    if comment := doc_comment(widget["doc"]):
        parts.append(comment)
    parts.append(f"class {widget['name']} extends StatelessWidget {{")
    if widget["fields"]:
        parts.extend(f"  final {field['type']} {field['name']};" for field in widget["fields"])
        parts.append("")
    include_key = widget["include_key"]
    if include_key is None:
        include_key = not widget["name"].startswith("_")
    parts.append(
        indent_block(
            render_named_constructor(
                widget["name"],
                widget["fields"],
                include_key=include_key,
            ),
            2,
        )
    )
    for member in widget["members"]:
        parts.append("")
        parts.append(indent_block(member, 2))
    parts.append("")
    parts.append("  @override")
    parts.append("  Widget build(BuildContext context) {")
    parts.append(indent_block(widget["build"], 4))
    parts.append("  }")
    parts.append("}")
    return "\n".join(parts)


def render_view_file(page: dict[str, Any], view: dict[str, Any]) -> str:
    entry_widget = {
        "name": view["entry_widget_name"],
        "doc": view["entry_doc"],
        "fields": [],
        "members": [],
        "build": view["entry_build"],
        "include_key": False,
    }
    widgets = [entry_widget, *view["widgets"]]
    sections = [f"part of '{page['file_name']}.dart';"]
    sections.extend(f"\n{render_widget_class(widget)}" for widget in widgets)
    return "\n".join(sections) + "\n"


def render_vm_file(
    page: dict[str, Any],
    events: dict[str, Any],
    view_model: dict[str, Any],
) -> str:
    sections = [
        f"part of '{page['file_name']}.dart';",
        "",
        f"sealed class {events['base_name']} {{",
        f"  const {events['base_name']}();",
        "}",
    ]
    for event in events["items"]:
        sections.append("")
        sections.append(render_event_class(event, events["base_name"]))
    sections.append("")
    sections.append(render_view_model_class(page, view_model, events))
    return "\n".join(sections) + "\n"


def code_uses_generated_part(code: str | None) -> bool:
    if not code:
        return False
    if "@JsonSerializable" in code:
        return True
    return re.search(r"_\$[A-Za-z_]\w*(FromJson|ToJson)\b", code) is not None


def theme_uses_generated_part(theme: dict[str, Any] | None) -> bool:
    if theme is None:
        return False
    if code_uses_generated_part(theme.get("declaration")):
        return True
    return any(code_uses_generated_part(member) for member in theme["members"])


def model_uses_generated_part(model: dict[str, Any]) -> bool:
    if model["preset"] in (MODEL_PRESET_STATE, MODEL_PRESET_STATE_JSON):
        return True
    if model.get("from_json"):
        return True
    if any(code_uses_generated_part(annotation) for annotation in model.get("annotations", [])):
        return True
    if any(
        code_uses_generated_part(annotation)
        for annotation in model.get("field_annotations", [])
        if annotation
    ):
        return True
    return any(code_uses_generated_part(member) for member in model["members"])


def custom_section_lines(label: str, value: str | list[str] | None) -> list[str]:
    if value is None:
        return [f"/// {label}: none"]
    if isinstance(value, str):
        lines = [line.rstrip() for line in value.splitlines() if line.strip()]
    else:
        lines = []
        for item in value:
            lines.extend(line.rstrip() for line in item.splitlines() if line.strip())
    if not lines:
        return [f"/// {label}: none"]
    return [f"/// {label}:", *(f"/// {line}" for line in lines)]


def normalize_contract_list_item(line: str) -> str:
    return re.sub(r"^\s*[-*]\s*", "", line.strip())


def custom_list_section_lines(label: str, value: str | list[str] | None) -> list[str]:
    if value is None:
        return [f"/// {label}: none"]
    if isinstance(value, str):
        lines = [line.rstrip() for line in value.splitlines() if line.strip()]
    else:
        lines = []
        for item in value:
            lines.extend(line.rstrip() for line in item.splitlines() if line.strip())
    if not lines:
        return [f"/// {label}: none"]
    return [
        f"/// {label}:",
        *(f"/// - {normalize_contract_list_item(line)}" for line in lines),
    ]


def render_custom_section(section: dict[str, Any], fallback_id: str) -> list[str]:
    label = section.get("label") or fallback_id
    if section.get("style") == "list":
        return custom_list_section_lines(label, section.get("lines"))
    return custom_section_lines(label, section.get("lines"))


def builtin_contract_sections(
    page: dict[str, Any],
    models: list[dict[str, Any]],
    events: dict[str, Any],
    view_model: dict[str, Any],
) -> dict[str, list[str]]:
    labels = {
        "api": "API",
        "bff_api": "BFF-API",
        "reused_widgets": "Reused Widgets",
        **page["contract"]["section_labels"],
    }
    view_model_refs = [
        {
            "name": view_model["name"],
            "description": view_model["description"],
        },
        *page["external_view_models"],
    ]
    model_refs = [
        {
            "name": model["name"],
            "description": model["description"],
        }
        for model in models
    ]
    model_refs.extend(page["external_models"])

    sections: dict[str, list[str]] = {
        "figma": section_lines("Figma", page["figma"]),
        "state_ownership": state_ownership_lines(page["state_ownership"]),
        "route": section_lines("Route", page["route"]),
        "reused_widgets": list_section_lines(
            labels["reused_widgets"],
            page["reused_widgets"],
        ),
        "widget_tree": [
            "/// Widget Tree:",
            *(f"/// {line}" for line in page["widget_tree"]),
        ],
        "theme": [
            "/// Theme: none"
            if page["theme"] is None
            else f"/// Theme: [{page['theme']['name']}]"
        ],
        "events": event_section_lines(events),
        "view_models": ref_section_lines("ViewModels", view_model_refs),
        "models": ref_section_lines("Models", model_refs),
    }
    if page["api_reference"] == API_BFF:
        sections["bff_api"] = section_lines(labels["bff_api"], page["api"])
        sections["api"] = []
    else:
        sections["api"] = section_lines(labels["api"], page["api"])
        sections["bff_api"] = []
    return sections


def section_entries_by_id(page: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for index, section in enumerate(page["contract"]["sections"]):
        section_id = section["id"] or f"custom_{index}"
        entries[section_id] = section
    return entries


def render_contract_sections(
    page: dict[str, Any],
    models: list[dict[str, Any]],
    events: dict[str, Any],
    view_model: dict[str, Any],
) -> list[str]:
    builtins = builtin_contract_sections(page, models, events, view_model)
    entries = section_entries_by_id(page)
    disabled = page["contract"]["disabled_sections"]
    rendered: list[str] = []
    emitted_custom: set[str] = set()

    for section_id in page["contract"]["section_order"]:
        if section_id in disabled:
            continue
        override = entries.get(section_id)
        if override is not None and override.get("lines") is not None:
            rendered.extend(render_custom_section(override, section_id))
            emitted_custom.add(section_id)
            continue
        if section_id in builtins:
            lines = builtins[section_id]
            if override is not None and override.get("label") and lines:
                original_label = lines[0].removeprefix("/// ").split(":", 1)[0]
                replacement = override["label"]
                lines = [
                    line.replace(f"/// {original_label}:", f"/// {replacement}:", 1)
                    if index == 0
                    else line
                    for index, line in enumerate(lines)
                ]
            rendered.extend(lines)
            if override is not None:
                emitted_custom.add(section_id)

    placement_markers = {
        "after_figma": "figma",
        "after_api": "api",
        "after_route": "route",
        "after_widget_tree": "widget_tree",
        "after_models": "models",
    }
    for section_id, section in entries.items():
        if section_id in emitted_custom or section_id in disabled:
            continue
        lines = render_custom_section(section, section_id)
        placement = section.get("placement")
        if placement is None:
            rendered.extend(lines)
            continue
        marker = placement_markers[placement]
        insert_after = -1
        marker_lines = builtins.get(marker, [])
        for index, rendered_line in enumerate(rendered):
            if marker_lines and rendered_line == marker_lines[-1]:
                insert_after = index
        if insert_after < 0:
            rendered.extend(lines)
        else:
            rendered[insert_after + 1 : insert_after + 1] = lines
    return rendered


def render_contract_file(
    page: dict[str, Any],
    models: list[dict[str, Any]],
    events: dict[str, Any],
    view_model: dict[str, Any],
) -> str:
    lines: list[str] = []
    lines.extend(render_import(entry) for entry in page["imports"])
    lines.append("")
    lines.append(f"part '{page['file_name']}.freezed.dart';")
    if theme_uses_generated_part(page["theme"]) or any(
        model_uses_generated_part(model) for model in models
    ):
        lines.append(f"part '{page['file_name']}.g.dart';")
    lines.append(f"part '{page['file_name']}.v.dart';")
    lines.append(f"part '{page['file_name']}.vm.dart';")
    lines.append("")

    lines.extend(render_contract_sections(page, models, events, view_model))
    lines.extend(page["contract"]["root_annotations"])
    lines.append(render_page_class(page))

    if page["contract"]["extra_declarations"]:
        lines.append("")
        lines.append("\n\n".join(page["contract"]["extra_declarations"]))

    if page["theme"] is not None:
        lines.append("")
        lines.append(render_theme_class(page["theme"]))

    for model in models:
        lines.append("")
        lines.append(render_model_class(model))

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spec-file",
        type=Path,
        required=True,
        help=(
            "Temporary JSON spec that describes the page contract, view, and "
            "view model before the generated contract dart becomes the "
            "long-lived source of truth."
        ),
    )
    parser.add_argument(
        "--page-root",
        type=Path,
        help=(
            "Page root such as lib/page or lib/src/page. Defaults to the "
            "project's existing page layout."
        ),
    )
    parser.add_argument(
        "--parent",
        type=Path,
        help=(
            "Optional middle directory below the page root, for example "
            "account/settings."
        ),
    )
    parser.add_argument(
        "--dir",
        type=Path,
        help=(
            "Full output directory. Overrides --page-root and --parent; "
            "default is <detected-page-root>/<name>_page."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite files when they already exist.",
    )
    return parser.parse_args()


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; pass --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    project_root = find_repo_root(Path.cwd())
    try:
        spec = load_spec(resolve_relative_to_root(args.spec_file, project_root))
    except SpecError as error:
        raise SystemExit(f"invalid page spec: {error}") from error

    page = spec["page"]
    if args.dir:
        output_dir = resolve_relative_to_root(args.dir, project_root)
    else:
        page_root = (
            resolve_relative_to_root(args.page_root, project_root)
            if args.page_root
            else infer_page_root(project_root)
        )
        try:
            parent = ensure_relative(args.parent, "--parent") if args.parent else None
        except ValueError as error:
            raise SystemExit(str(error)) from error
        output_dir = page_root / parent / page["file_name"] if parent else page_root / page["file_name"]

    contract_path = output_dir / f"{page['file_name']}.dart"
    view_path = output_dir / f"{page['file_name']}.v.dart"
    vm_path = output_dir / f"{page['file_name']}.vm.dart"

    try:
        write_file(
            contract_path,
            render_contract_file(
                page,
                spec["models"],
                spec["events"],
                spec["view_model"],
            ),
            args.force,
        )
        write_file(view_path, render_view_file(page, spec["view"]), args.force)
        write_file(
            vm_path,
            render_vm_file(page, spec["events"], spec["view_model"]),
            args.force,
        )
    except FileExistsError as error:
        raise SystemExit(str(error)) from error

    print(f"wrote {display_path(contract_path, project_root)}")
    print(f"wrote {display_path(view_path, project_root)}")
    print(f"wrote {display_path(vm_path, project_root)}")
    print(
        "next: fvm dart format "
        f"{display_path(contract_path, project_root)} "
        f"{display_path(view_path, project_root)} "
        f"{display_path(vm_path, project_root)}"
    )
    print("next: fvm dart run build_runner build --delete-conflicting-outputs")
    if page["api_reference"] == API_BFF:
        export_format = page["export_format"]
        print(
            "next: fvm dart run fr_acdd:extract_bff "
            f"--format {export_format} "
            f"--input {display_path(contract_path, project_root)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

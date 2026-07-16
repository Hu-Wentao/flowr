"""Parse the page-support and component-contract source pair."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from contract_core import (
    ContractError,
    bracket_refs,
    class_names,
    doc_sections,
    relative_import_uri,
    require_file,
)


@dataclass(frozen=True)
class ComponentContract:
    component_file: str
    contract_file: str
    imports: list[str]
    parts: list[str]
    view: str
    component_input: str | None
    events: list[str]
    view_models: list[str]
    models: list[str]
    sections: dict[str, list[str]]


@dataclass(frozen=True)
class PageContract:
    page_file: str
    page_class: str
    page_args: str
    primary_view: str
    sections: dict[str, list[str]]
    component: ComponentContract


def parse_component(component_file: Path) -> ComponentContract:
    source = require_file(component_file, "component library")
    part_names = re.findall(r"\bpart\s+['\"]([^'\"]+)['\"]\s*;", source)
    contract_name = f"{component_file.stem}.c.dart"
    if contract_name not in part_names:
        raise ContractError(f"component shell must declare `part '{contract_name}';`")
    contract_file = component_file.with_name(contract_name)
    contract_source = require_file(contract_file, "component contract")
    expected_part_of = f"part of '{component_file.name}';"
    if expected_part_of not in contract_source:
        raise ContractError(f"component contract must begin with `{expected_part_of}`")
    if re.search(r"^\s*(?:import|export|library)\b", contract_source, re.MULTILINE):
        raise ContractError(
            "component contract part must not declare import, export, or library directives"
        )

    sections = doc_sections(contract_source)
    events = bracket_refs(sections.get("Events", []))
    view_models = bracket_refs(sections.get("ViewModels", []))
    models = bracket_refs(sections.get("Models", []))
    names = class_names(contract_source)
    views = [name for name in names if name.endswith("View")]
    if len(views) != 1:
        raise ContractError(
            "component contract must declare exactly one public XxxView class"
        )
    page_args = [name for name in names if name.endswith("PageArgs")]
    if page_args:
        raise ContractError(
            "component contract must not declare *PageArgs; declare component-owned "
            "XxxArgs or XxxConfig instead"
        )
    inputs = [name for name in names if name.endswith(("Args", "Config"))]
    imports = re.findall(r"^\s*import\s+['\"]([^'\"]+)['\"]", source, re.MULTILINE)
    return ComponentContract(
        component_file=str(component_file),
        contract_file=str(contract_file),
        imports=imports,
        parts=part_names,
        view=views[0],
        component_input=inputs[0] if inputs else None,
        events=events,
        view_models=view_models,
        models=models,
        sections=sections,
    )


def parse_page(page_file: Path) -> PageContract:
    if not page_file.name.endswith(".page.dart"):
        raise ContractError("page file must use the `.page.dart` suffix")
    source = require_file(page_file, "page support")
    component_file = page_file.with_name(
        page_file.name.removesuffix(".page.dart") + ".dart"
    )
    if not relative_import_uri(source, component_file.name):
        raise ContractError(
            f"page support must import its sibling component library `{component_file.name}`"
        )
    sections = doc_sections(source)
    primary_refs = bracket_refs(sections.get("Component", []))
    if len(primary_refs) != 1:
        raise ContractError(
            "page support must declare exactly one `/// Component: [XxxView]` marker"
        )
    names = class_names(source)
    page_classes = [name for name in names if name.endswith("Page")]
    if len(page_classes) != 1:
        raise ContractError(
            "page support must declare exactly one public XxxPage class"
        )
    page_args = [name for name in names if name.endswith("PageArgs")]
    if len(page_args) != 1:
        raise ContractError(
            "page support must declare exactly one route-owned XxxPageArgs class"
        )
    expected_page_args = f"{page_classes[0].removesuffix('Page')}PageArgs"
    if page_args[0] != expected_page_args:
        raise ContractError(
            f"page argument `{page_args[0]}` must match page class as "
            f"`{expected_page_args}`"
        )
    component = parse_component(component_file)
    if primary_refs[0] != component.view:
        raise ContractError(
            f"page primary view `{primary_refs[0]}` does not match component view `{component.view}`"
        )
    return PageContract(
        page_file=str(page_file),
        page_class=page_classes[0],
        page_args=page_args[0],
        primary_view=primary_refs[0],
        sections=sections,
        component=component,
    )


def to_dict(contract: PageContract | ComponentContract) -> dict[str, object]:
    return asdict(contract)

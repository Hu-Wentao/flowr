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
from frontend_semantics import (
    EndpointBehavior,
    EndpointRequestSources,
    FrontendEndpoint,
    InteractionFlow,
    parse_frontend_semantics,
)


@dataclass(frozen=True)
class ComponentContract:
    component_file: str
    contract_file: str
    imports: list[str]
    parts: list[str]
    views: list[str]
    events: list[str]
    view_models: list[str]
    models: list[str]
    state_ownership: str
    state_view_model: str | None
    endpoints: tuple[FrontendEndpoint, ...]
    behaviors: tuple[EndpointBehavior, ...]
    request_sources: tuple[EndpointRequestSources, ...]
    interactions: tuple[InteractionFlow, ...]
    bff_service: str | None
    theme_mode: str
    theme_type: str | None
    theme_ownership: str | None
    theme_warning: str | None
    sections: dict[str, list[str]]

    @property
    def view(self) -> str:
        """Return the first public View for legacy single-View consumers."""

        return self.views[0]


@dataclass(frozen=True)
class PageContract:
    page_file: str
    page_class: str
    page_classes: list[str]
    routes: dict[str, str]
    primary_view: str
    sections: dict[str, list[str]]
    component: ComponentContract


STRUCTURED_THEME = re.compile(
    r"^(app-shared|component)\s+\[([A-Za-z_][A-Za-z0-9_]*)\]$"
)
STRUCTURED_STATE_OWNERSHIP = re.compile(
    r"^(none|app-owned|page-owned|component-owned)"
    r"(?:\s+\[([A-Za-z_][A-Za-z0-9_]*)\])?$"
)


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


def dart_class_body(source: str, class_name: str) -> str:
    """Return one Dart class body for page-source inspection."""

    match = re.search(rf"\bclass\s+{re.escape(class_name)}\b[^{{]*{{", source)
    if match is None:
        raise ContractError(f"page support must declare typed route {class_name}")
    opening = source.find("{", match.start())
    closing = matching_delimiter(source, opening, "{", "}")
    return source[opening + 1 : closing]


def typed_route_path(source: str, page_class: str) -> str:
    """Read a typed Page route path directly from its annotation."""

    annotations = list(
        re.finditer(
            rf"@TypedGoRoute\s*<\s*{re.escape(page_class)}\s*>\s*\(",
            source,
        )
    )
    if len(annotations) != 1:
        raise ContractError(
            f"page support must annotate {page_class} with exactly one @TypedGoRoute"
        )
    opening = source.find("(", annotations[0].start())
    closing = matching_delimiter(source, opening, "(", ")")
    arguments = source[opening + 1 : closing]
    path = re.search(
        r"\bpath\s*:\s*r?(['\"])(.*?)\1",
        arguments,
        re.DOTALL,
    )
    if path is None:
        raise ContractError(
            f"@TypedGoRoute<{page_class}> must declare a string-literal path"
        )
    return path.group(2)


def direct_build_view(source: str, page_class: str) -> str:
    """Infer the primary View constructed inside a typed Page build method."""

    body = dart_class_body(source, page_class)
    builds = list(re.finditer(r"\bWidget\s+build\s*\(", body))
    if len(builds) != 1:
        raise ContractError(
            f"typed route {page_class} must declare exactly one Widget build method"
        )
    parameters_opening = body.find("(", builds[0].start())
    parameters_closing = matching_delimiter(
        body, parameters_opening, "(", ")"
    )
    implementation = body[parameters_closing + 1 :].lstrip()
    view_pattern = r"(?:const\s+)?([A-Za-z_][A-Za-z0-9_]*View)\s*\("
    if implementation.startswith("=>"):
        semicolon = implementation.find(";")
        method_body = implementation[2:semicolon if semicolon >= 0 else None]
    elif implementation.startswith("{"):
        closing = matching_delimiter(implementation, 0, "{", "}")
        method_body = implementation[1:closing]
    else:
        method_body = ""
    views = re.findall(view_pattern, method_body)
    unique_views = list(dict.fromkeys(views))
    if len(unique_views) == 1:
        return unique_views[0]
    raise ContractError(
        f"typed route {page_class} build must construct one primary XxxView"
    )


def is_api_less_bff(component: ComponentContract) -> bool:
    """Return whether a BFF contract explicitly has no UI HTTP endpoint."""

    return component.sections.get("BFF-API") == ["-"]


def parse_theme(
    sections: dict[str, list[str]],
) -> tuple[str, str | None, str | None, str | None]:
    """Parse the versioned theme contract while preserving legacy readability."""

    theme_lines = sections.get("Theme", [])
    raw_theme = " ".join(theme_lines).strip()
    ownership_lines = sections.get("Theme Ownership", [])
    if ownership_lines:
        display = raw_theme or "missing"
        return (
            "legacy",
            None,
            None,
            "legacy Theme declaration "
            f"`{display}` with a separate `Theme Ownership` section; migrate "
            "to app-shared [ThemeType] or component [ThemeType]",
        )
    if raw_theme in {"none", "material"}:
        return raw_theme, None, None, None
    match = STRUCTURED_THEME.fullmatch(raw_theme)
    if match:
        return "fr-mvvm-theme", match.group(2), match.group(1), None
    display = raw_theme or "missing"
    return (
        "legacy",
        None,
        None,
        "legacy Theme declaration "
        f"`{display}`; migrate to none, material, or "
        "app-shared [ThemeType] or component [ThemeType] before validation or "
        "generation",
    )


def parse_state_ownership(
    sections: dict[str, list[str]],
) -> tuple[str, str | None]:
    """Parse Provider lifecycle ownership from the component contract."""

    raw = " ".join(sections.get("State Ownership", [])).strip()
    match = STRUCTURED_STATE_OWNERSHIP.fullmatch(raw)
    if not match:
        display = raw or "missing"
        raise ContractError(
            "State Ownership must be `none`, `app-owned [ViewModel]`, "
            "`page-owned [ViewModel]`, or `component-owned [ViewModel]`; "
            f"found `{display}`"
        )
    ownership, declared_view_model = match.groups()
    if ownership == "none":
        if declared_view_model:
            raise ContractError("State Ownership `none` must not reference a ViewModel")
        return ownership, None
    if not declared_view_model:
        raise ContractError(
            f"State Ownership `{ownership}` must reference exactly one ViewModel"
        )
    return ownership, declared_view_model


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
    if "/*" in contract_source:
        raise ContractError(
            "component contract sections must use consecutive `///` documentation "
            "comments; `/* ... */` contract blocks are not allowed"
        )

    sections = doc_sections(contract_source)
    if not sections:
        raise ContractError(
            "component contract must declare its sections with consecutive `///` "
            "documentation comments"
        )
    events = bracket_refs(sections.get("Events", []))
    view_models = bracket_refs(sections.get("ViewModels", []))
    models = bracket_refs(sections.get("Models", []))
    state_ownership, state_view_model = parse_state_ownership(sections)
    if "BFF-API" in sections or "FrAcddMode.bff" in contract_source:
        frontend = parse_frontend_semantics(sections)
    else:
        # Explicit API and local components keep their existing semantic grammar;
        # the breaking v9 endpoint/interaction model applies to BFF contracts.
        frontend = parse_frontend_semantics({"Interactions": ["none"]})
    bff_service = " ".join(sections.get("BFF Service", [])).strip() or None
    theme_mode, theme_type, theme_ownership, theme_warning = parse_theme(sections)
    names = class_names(contract_source)
    library_sources = [source]
    for part_name in part_names:
        part_file = component_file.parent / part_name
        if part_file.is_file():
            library_sources.append(require_file(part_file, "component part"))
    public_view_symbols = list(
        dict.fromkeys(
            name
            for library_source in library_sources
            for name in class_names(library_source)
            if name.endswith("View") and not name.startswith("_")
        )
    )
    declared_views = bracket_refs(sections.get("Public Views", []))
    if declared_views:
        if len(declared_views) != len(set(declared_views)):
            raise ContractError("Public Views must not contain duplicate references")
        invalid_views = [
            name
            for name in declared_views
            if not name.endswith("View") or name.startswith("_")
        ]
        if invalid_views:
            raise ContractError(
                "Public Views must reference public *View classes: "
                + ", ".join(invalid_views)
            )
        missing_views = [
            name for name in declared_views if name not in public_view_symbols
        ]
        if missing_views:
            raise ContractError(
                "Public Views references classes not declared by the component "
                "library: " + ", ".join(missing_views)
            )
        unlisted_views = [
            name for name in public_view_symbols if name not in declared_views
        ]
        if unlisted_views:
            raise ContractError(
                "component library exposes public Views missing from `Public Views:`: "
                + ", ".join(unlisted_views)
            )
        views = declared_views
    else:
        if len(public_view_symbols) != 1:
            raise ContractError(
                "component contract must declare `Public Views:` when the component "
                "library exposes zero or multiple public View classes"
            )
        views = public_view_symbols
    page_args = [name for name in names if name.endswith("PageArgs")]
    if page_args:
        raise ContractError(
            "component contract must not declare *PageArgs; keep route inputs "
            "as typed Page fields and expose ordinary View fields"
        )
    inputs = [name for name in names if name.endswith(("Args", "Config"))]
    if inputs:
        raise ContractError(
            "component contract must expose ordinary View constructor fields instead "
            "of component input wrappers: " + ", ".join(inputs)
        )
    imports = re.findall(r"^\s*import\s+['\"]([^'\"]+)['\"]", source, re.MULTILINE)
    return ComponentContract(
        component_file=str(component_file),
        contract_file=str(contract_file),
        imports=imports,
        parts=part_names,
        views=views,
        events=events,
        view_models=view_models,
        models=models,
        state_ownership=state_ownership,
        state_view_model=state_view_model,
        endpoints=frontend.endpoints,
        behaviors=frontend.behaviors,
        request_sources=frontend.request_sources,
        interactions=frontend.interactions,
        bff_service=bff_service,
        theme_mode=theme_mode,
        theme_type=theme_type,
        theme_ownership=theme_ownership,
        theme_warning=theme_warning,
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
    names = class_names(source)
    page_classes = [name for name in names if name.endswith("Page")]
    if not page_classes:
        raise ContractError(
            "page support must declare at least one public XxxPage class"
        )
    page_args = [name for name in names if name.endswith("PageArgs")]
    if page_args:
        raise ContractError(
            "typed page support must not declare XxxPageArgs; declare route inputs "
            "as fields on XxxPage extends GoRouteData"
        )
    expected_page_class = (
        "".join(
            part.capitalize()
            for part in page_file.name.removesuffix(".page.dart").split("_")
        )
        + "Page"
    )
    if expected_page_class not in page_classes:
        raise ContractError(
            f"page support must declare primary page class {expected_page_class}"
        )
    for page_class in page_classes:
        if not re.search(
            rf"\bclass\s+{re.escape(page_class)}\s+extends\s+GoRouteData\s+"
            rf"with\s+\${re.escape(page_class)}\b",
            source,
            re.DOTALL,
        ):
            raise ContractError(
                f"page support must declare `{page_class} extends GoRouteData "
                f"with ${page_class}`"
            )
    routes = {
        page_class: typed_route_path(source, page_class)
        for page_class in page_classes
    }
    page_views = {
        page_class: direct_build_view(source, page_class) for page_class in page_classes
    }
    primary_views = set(page_views.values())
    if len(primary_views) != 1:
        mappings = ", ".join(
            f"{page_class} -> {view}" for page_class, view in page_views.items()
        )
        raise ContractError(
            "page support variants must build one shared primary View: "
            + mappings
        )
    primary_view = next(iter(primary_views))
    generated_part = page_file.name.removesuffix(".dart") + ".g.dart"
    if not re.search(
        rf"\bpart\s+['\"]{re.escape(generated_part)}['\"]\s*;", source
    ):
        raise ContractError(
            f"page support must declare `part '{generated_part}';`"
        )
    component = parse_component(component_file)
    if primary_view not in component.views:
        raise ContractError(
            f"page primary view `{primary_view}` is not declared by component "
            f"Public Views: {', '.join(component.views)}"
        )
    return PageContract(
        page_file=str(page_file),
        page_class=expected_page_class,
        page_classes=page_classes,
        routes=routes,
        primary_view=primary_view,
        sections=sections,
        component=component,
    )


def to_dict(contract: PageContract | ComponentContract) -> dict[str, object]:
    return asdict(contract)

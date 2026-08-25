#!/usr/bin/env python3
"""Validate typed route refactors and cross-page module data flow."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from contract_core import ContractError


IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
PAGE_CLASS = re.compile(rf"\bclass\s+({IDENTIFIER}Page)\s+extends\s+GoRouteData\b")
TYPED_ROUTE = re.compile(
    rf"@TypedGoRoute<({IDENTIFIER}Page)>\s*\(\s*path\s*:\s*(['\"])(.+?)\2",
    re.DOTALL,
)
PAGE_EXTRA_CLASS = re.compile(rf"\b(?:final\s+)?class\s+({IDENTIFIER}PageExtra)\b")
FREEZED_JSON_EXTRA = re.compile(
    rf"@FrAcddFreezedJSON\s+(?:sealed|abstract)\s+class\s+"
    rf"({IDENTIFIER}PageExtra)\s+with\s+_\$\1\b",
    re.DOTALL,
)
FLOW_LINE = re.compile(
    rf"^///\s*-\s*\[({IDENTIFIER}Page)\]\s*->\s*"
    rf"\[({IDENTIFIER}Page)\]\s+via\s+\[({IDENTIFIER}PageExtra)\]\s*:"
    r"\s*(.+?)\s*$"
)
RAW_LITERAL_NAVIGATION = re.compile(
    r"\bcontext\.(go|push|replace)(?:<[^>]+>)?\s*\(\s*(['\"])(.*?)\2",
    re.DOTALL,
)
APP_ROUTES_NAVIGATION = re.compile(
    rf"\bcontext\.(go|push|replace)(?:<[^>]+>)?\s*\(\s*AppRoutes\.({IDENTIFIER})\b"
)
CONTEXT_NAVIGATION_CALL = re.compile(
    r"(?:(?:\b(?:context|ctx)\s*[?!]?\s*\.\s*)|"
    r"(?:\bGoRouter\s*\.\s*of\s*\(\s*(?:context|ctx)\s*[?!]?\s*\)"
    r"\s*[?!]?\s*\.\s*))"
    r"(?P<method>go|push|replace)(?:\s*<[^()<>]+>)?\s*\("
)
NEXT_ROUTE_TOKEN = re.compile(r"\bnextRoute\b")
APP_ROUTE_CONSTANT = re.compile(
    rf"\bstatic\s+const\s+(?:String\s+)?({IDENTIFIER})\s*=\s*(['\"])(.+?)\2\s*;"
)
COMPATIBILITY_BOUNDARY = re.compile(
    r"//\s*fr-route:\s*compatibility-boundary\s+(\S.+?)\s*$"
)


@dataclass(frozen=True)
class Flow:
    source: str
    target: str
    extra: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class TypedRoute:
    page: str
    path: str


def infer_project_root(module_file: Path) -> Path:
    """Find the Flutter project that owns a cross-page module."""

    for parent in (module_file.parent, *module_file.parents):
        if (parent / "pubspec.yaml").is_file():
            return parent
        if parent.name == "lib":
            return parent.parent
    raise ContractError(f"cannot infer project root from {module_file}")


def typed_routes(project_root: Path) -> tuple[TypedRoute, ...]:
    """Index literal paths declared by typed Page adapters."""

    routes: list[TypedRoute] = []
    for page_file in sorted((project_root / "lib").rglob("*.page.dart")):
        source = page_file.read_text(encoding="utf-8")
        routes.extend(
            TypedRoute(page, path) for page, _, path in TYPED_ROUTE.findall(source)
        )
    return tuple(routes)


def route_pattern(path: str) -> re.Pattern[str]:
    """Convert a go_router path template into an anchored matcher."""

    segments = path.split("/")
    pattern = "/".join(
        r"[^/]+" if segment.startswith(":") else re.escape(segment)
        for segment in segments
    )
    return re.compile(rf"^{pattern}$")


def matching_typed_page(uri: str, routes: tuple[TypedRoute, ...]) -> str | None:
    """Return the typed Page matching a fixed internal URI."""

    path = uri.split("?", 1)[0].split("#", 1)[0]
    for route in routes:
        if route_pattern(route.path).fullmatch(path):
            return route.page
    return None


def is_external_uri(uri: str) -> bool:
    """Recognize absolute external URI literals."""

    return bool(re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", uri)) or uri.startswith("//")


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


def _real_line_comments(source: str) -> tuple[tuple[int, int], ...]:
    """Locate real Dart `//` comments while ignoring comment text in strings."""

    comments: list[tuple[int, int]] = []
    index = 0
    while index < len(source):
        if source[index] in {"'", '"'}:
            index, _ = _dart_string_extent(source, index)
            continue
        if source.startswith("//", index):
            end = source.find("\n", index)
            end = len(source) if end < 0 else end
            comments.append((index, end))
            index = end
            continue
        if source.startswith("/*", index):
            depth = 1
            index += 2
            while index < len(source) and depth:
                if source.startswith("/*", index):
                    depth += 1
                    index += 2
                elif source.startswith("*/", index):
                    depth -= 1
                    index += 2
                else:
                    index += 1
            continue
        index += 1
    return tuple(comments)


def has_compatibility_boundary(source: str, offset: int) -> bool:
    """Allow a raw call only beside a real, reasoned legacy line comment."""

    line_start = source.rfind("\n", 0, offset) + 1
    previous_end = max(0, line_start - 1)
    previous_start = source.rfind("\n", 0, previous_end) + 1
    allowed_line_starts = {line_start, previous_start}
    for comment_start, comment_end in _real_line_comments(source):
        comment_line_start = source.rfind("\n", 0, comment_start) + 1
        if comment_line_start not in allowed_line_starts:
            continue
        if COMPATIBILITY_BOUNDARY.search(source[comment_start:comment_end]):
            return True
    return False


def mask_comments_and_strings(source: str) -> str:
    """Mask inert Dart text but retain executable `${...}` interpolation code."""

    cleaned = list(source)
    index = 0
    while index < len(source):
        if source[index] in {"'", '"'}:
            start = index
            end, interpolations = _dart_string_extent(source, start)
            for offset in range(start, min(end, len(cleaned))):
                if cleaned[offset] not in {"\r", "\n"}:
                    cleaned[offset] = " "
            for expression_start, expression_end in interpolations:
                expression = mask_comments_and_strings(
                    source[expression_start:expression_end]
                )
                cleaned[expression_start:expression_end] = expression
            index = end
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


def matching_parenthesis(source: str, opening: int) -> int:
    """Return a matching parenthesis in source whose strings are already masked."""

    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "(":
            depth += 1
        elif source[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    raise ContractError("unterminated raw context navigation call")


def first_argument(value: str) -> str:
    """Return the first top-level argument from one masked call body."""

    stack: list[str] = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    for index, char in enumerate(value):
        if char in pairs:
            stack.append(pairs[char])
        elif stack and char == stack[-1]:
            stack.pop()
        elif char == "," and not stack:
            return value[:index].strip()
    return value.strip()


def next_route_navigation_calls(source: str) -> tuple[tuple[int, str, str], ...]:
    """Return raw navigation calls whose first argument contains nextRoute."""

    masked = mask_comments_and_strings(source)
    calls: list[tuple[int, str, str]] = []
    for match in CONTEXT_NAVIGATION_CALL.finditer(masked):
        opening = match.end() - 1
        closing = matching_parenthesis(masked, opening)
        expression = first_argument(masked[opening + 1 : closing])
        if NEXT_ROUTE_TOKEN.search(expression):
            calls.append((match.start(), match.group("method"), expression))
    return tuple(calls)


def handwritten_component_sources(project_root: Path) -> tuple[Path, ...]:
    """Return component shells and handwritten component parts."""

    lib = project_root / "lib"
    sources: set[Path] = set()
    for contract in lib.rglob("*.c.dart"):
        stem = contract.name.removesuffix(".c.dart")
        candidates = [contract.with_name(f"{stem}.dart")]
        candidates.extend(
            contract.with_name(f"{stem}.{suffix}.dart")
            for suffix in ("c", "v", "vm", "srv")
        )
        sources.update(path for path in candidates if path.is_file())
    return tuple(sorted(sources))


def app_route_constants(project_root: Path) -> dict[str, str]:
    """Read compatibility AppRoutes constants when present."""

    constants: dict[str, str] = {}
    for dart_file in (project_root / "lib").rglob("*.dart"):
        source = dart_file.read_text(encoding="utf-8")
        if not re.search(r"\bclass\s+AppRoutes\b", source):
            continue
        body = class_body(source, "AppRoutes")
        constants.update(
            (name, value) for name, _, value in APP_ROUTE_CONSTANT.findall(body)
        )
    return constants


def navigation_error(
    source_file: Path,
    source: str,
    offset: int,
    method: str,
    expression: str,
    page: str,
) -> ContractError:
    """Build an actionable typed-navigation failure."""

    line = source.count("\n", 0, offset) + 1
    return ContractError(
        f"{source_file}:{line}: context.{method}({expression}) targets typed "
        f"{page}; use {page}(...).{method}(context). Typed internal navigation "
        "must use XxxPage(...).go/push/replace(context)"
    )


def validate_component_navigation(project_root: Path) -> None:
    """Reject raw fixed navigation when a typed destination is known."""

    routes = typed_routes(project_root)
    constants = app_route_constants(project_root)
    for source_file in handwritten_component_sources(project_root):
        source = source_file.read_text(encoding="utf-8")
        for offset, method, expression in next_route_navigation_calls(source):
            if has_compatibility_boundary(source, offset):
                continue
            line = source.count("\n", 0, offset) + 1
            raise ContractError(
                f"{source_file}:{line}: raw {method}({expression}) must not route "
                "from backend nextRoute data; use a semantic nullable enum "
                "signal and typed Page navigation, or retain the one reasoned "
                "legacy fr-route compatibility-boundary marker exception"
            )
        for match in RAW_LITERAL_NAVIGATION.finditer(source):
            method, _, uri = match.groups()
            if "$" in uri or is_external_uri(uri):
                continue
            page = matching_typed_page(uri, routes)
            if page is None or has_compatibility_boundary(source, match.start()):
                continue
            raise navigation_error(
                source_file, source, match.start(), method, repr(uri), page
            )
        for match in APP_ROUTES_NAVIGATION.finditer(source):
            method, name = match.groups()
            uri = constants.get(name)
            page = matching_typed_page(uri, routes) if uri is not None else None
            if page is None or has_compatibility_boundary(source, match.start()):
                continue
            raise navigation_error(
                source_file,
                source,
                match.start(),
                method,
                f"AppRoutes.{name}",
                page,
            )


def strip_comments(source: str) -> str:
    """Remove comments before checking component type dependencies."""

    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"//.*", "", source)


def class_body(source: str, class_name: str) -> str:
    """Return the body of a simple Dart class declaration."""

    match = re.search(rf"\bclass\s+{re.escape(class_name)}\b", source)
    if not match:
        match = re.search(rf"\bfinal\s+class\s+{re.escape(class_name)}\b", source)
    if not match:
        raise ContractError(f"missing class {class_name}")
    opening = source.find("{", match.end())
    if opening < 0:
        raise ContractError(f"class {class_name} has no body")
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1 : index]
    raise ContractError(f"class {class_name} has an unterminated body")


def parse_module_contract(source: str) -> tuple[tuple[str, ...], tuple[Flow, ...]]:
    """Parse the Page inventory and data-flow documentation."""

    pages_line = next(
        (line for line in source.splitlines() if line.startswith("/// Pages:")),
        None,
    )
    if pages_line is None:
        raise ContractError("cross-page module must declare `/// Pages:`")
    pages = tuple(re.findall(rf"\[({IDENTIFIER}Page)\]", pages_line))
    if not pages:
        raise ContractError("`/// Pages:` must list typed Page references")
    if len(pages) != len(set(pages)):
        raise ContractError("`/// Pages:` must not contain duplicates")

    lines = source.splitlines()
    try:
        flow_index = next(
            index
            for index, line in enumerate(lines)
            if line.strip() == "/// Page Data Flow:"
        )
    except StopIteration as error:
        raise ContractError(
            "cross-page module must declare `/// Page Data Flow:`"
        ) from error

    flows: list[Flow] = []
    for line in lines[flow_index + 1 :]:
        if not line.startswith("///"):
            break
        if not line.startswith("/// -"):
            continue
        match = FLOW_LINE.match(line)
        if not match:
            raise ContractError(f"invalid Page Data Flow entry: {line}")
        fields = tuple(field.strip() for field in match.group(4).split(","))
        if not fields or any(not re.fullmatch(IDENTIFIER, field) for field in fields):
            raise ContractError(f"invalid Page Data Flow field list: {line}")
        flows.append(Flow(match.group(1), match.group(2), match.group(3), fields))
    if not flows:
        raise ContractError("`/// Page Data Flow:` must declare at least one flow")
    return pages, tuple(flows)


def component_sources(page_file: Path) -> tuple[Path, ...]:
    """Return handwritten component sources owned by one Page adapter."""

    stem = page_file.name.removesuffix(".page.dart")
    candidates = [page_file.with_name(f"{stem}.dart")]
    candidates.extend(
        page_file.with_name(f"{stem}.{suffix}.dart")
        for suffix in ("c", "v", "vm", "srv")
    )
    return tuple(path for path in candidates if path.is_file())


def split_parameters(parameters: str) -> tuple[str, ...]:
    """Split a Freezed factory parameter list without breaking generic types."""

    parts: list[str] = []
    start = 0
    depth = 0
    for index, character in enumerate(parameters):
        if character in "([{<":
            depth += 1
        elif character in ")]}>":
            depth -= 1
        elif character == "," and depth == 0:
            parts.append(parameters[start:index])
            start = index + 1
    parts.append(parameters[start:])
    return tuple(part.strip() for part in parts if part.strip())


def validate_freezed_page_extra(
    page_file: Path,
    source: str,
    extra_name: str,
) -> tuple[str, ...]:
    """Validate the generated JSON shape and return factory field names."""

    if extra_name not in FREEZED_JSON_EXTRA.findall(source):
        raise ContractError(
            f"{extra_name} must use `@FrAcddFreezedJSON` and declare "
            f"`sealed class {extra_name} with _${extra_name}`"
        )

    expected_freezed_part = (
        f"part '{page_file.name.removesuffix('.dart')}.freezed.dart';"
    )
    expected_json_part = f"part '{page_file.name.removesuffix('.dart')}.g.dart';"
    if expected_freezed_part not in source:
        raise ContractError(
            f"{extra_name} must declare generated part {expected_freezed_part}"
        )
    if expected_json_part not in source:
        raise ContractError(
            f"{extra_name} must retain generated part {expected_json_part}"
        )

    body = class_body(source, extra_name)
    factory = re.search(
        rf"\bconst\s+factory\s+{re.escape(extra_name)}\s*\((.*?)\)\s*="
        rf"\s*_{re.escape(extra_name)}\s*;",
        body,
        re.DOTALL,
    )
    if factory is None:
        raise ContractError(
            f"{extra_name} must declare one redirecting `const factory`"
        )

    fields: list[str] = []
    for parameter in split_parameters(factory.group(1).strip().strip("{}[]")):
        declaration = parameter.split("=", 1)[0]
        identifiers = re.findall(IDENTIFIER, declaration)
        if not identifiers:
            raise ContractError(
                f"{extra_name} contains an unsupported factory parameter: {parameter}"
            )
        fields.append(identifiers[-1])
    if not fields:
        raise ContractError(f"{extra_name} must declare transported fields")
    if len(fields) != len(set(fields)):
        raise ContractError(f"{extra_name} factory fields must be unique")

    from_json = re.search(
        rf"\bfactory\s+{re.escape(extra_name)}\.fromJson\s*\("
        rf"\s*Map\s*<\s*String\s*,\s*dynamic\s*>\s+{IDENTIFIER}\s*,?\s*\)"
        rf"\s*=>\s*_\${re.escape(extra_name)}FromJson\s*\(",
        body,
        re.DOTALL,
    )
    if from_json is None:
        raise ContractError(
            f"{extra_name} must declare generated `factory "
            f"{extra_name}.fromJson(...)`"
        )

    return tuple(fields)


def validate_route_extra_codec(project_root: Path, extras: set[str]) -> None:
    """Require tagged application codec coverage for every transported extra."""

    if not extras:
        return
    handwritten_sources: list[str] = []
    for dart_file in sorted((project_root / "lib").rglob("*.dart")):
        if dart_file.name.endswith((".g.dart", ".freezed.dart")):
            continue
        handwritten_sources.append(dart_file.read_text(encoding="utf-8"))
    source = "\n".join(handwritten_sources)
    if not re.search(r"\bextraCodec\s*:", source):
        raise ContractError(
            "GoRouter must configure one application-owned `extraCodec` when "
            "PageExtra transport is present"
        )
    for extra_name in sorted(extras):
        encoder_case = re.search(
            rf"(?:\bcase\s+{re.escape(extra_name)}\b|"
            rf"\b{re.escape(extra_name)}\s+{IDENTIFIER}\s*=>)",
            source,
        )
        if encoder_case is None:
            raise ContractError(
                f"route extra codec encoder must cover {extra_name}"
            )
        if not re.search(
            rf"\b{re.escape(extra_name)}\.fromJson\s*\(",
            source,
        ):
            raise ContractError(
                f"route extra codec decoder must restore {extra_name}.fromJson"
            )


def validate_module(module_file: Path) -> None:
    """Validate a cross-page module and all route transport boundaries."""

    module_file = module_file.resolve()
    if not module_file.is_file():
        raise ContractError(f"module export not found: {module_file}")
    if module_file.stem != module_file.parent.name:
        raise ContractError(
            "cross-page module export filename must match its directory name"
        )

    module_source = module_file.read_text(encoding="utf-8")
    documented_pages, flows = parse_module_contract(module_source)
    page_files = sorted(module_file.parent.rglob("*.page.dart"))
    if not page_files:
        raise ContractError("cross-page module contains no typed Page adapters")

    pages: dict[str, Path] = {}
    page_sources: dict[Path, str] = {}
    for page_file in page_files:
        source = page_file.read_text(encoding="utf-8")
        page_sources[page_file] = source
        for page_name in PAGE_CLASS.findall(source):
            if page_name in pages:
                raise ContractError(f"duplicate typed Page {page_name}")
            pages[page_name] = page_file

    actual_pages = set(pages)
    documented_set = set(documented_pages)
    if documented_set != actual_pages:
        missing = sorted(actual_pages - documented_set)
        unknown = sorted(documented_set - actual_pages)
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if unknown:
            details.append(f"unknown {', '.join(unknown)}")
        raise ContractError(f"`/// Pages:` inventory mismatch: {'; '.join(details)}")

    extra_locations: dict[str, Path] = {}
    for dart_file in module_file.parent.rglob("*.dart"):
        if dart_file.name.endswith((".g.dart", ".freezed.dart")):
            continue
        source = dart_file.read_text(encoding="utf-8")
        for extra_name in PAGE_EXTRA_CLASS.findall(source):
            if not dart_file.name.endswith(".page.dart"):
                raise ContractError(
                    f"{extra_name} is a route transport model and must be declared "
                    "directly in its target .page.dart"
                )
            if extra_name in extra_locations:
                raise ContractError(f"duplicate PageExtra {extra_name}")
            extra_locations[extra_name] = dart_file

    listed = set(documented_pages)
    for flow in flows:
        if flow.source not in listed or flow.target not in listed:
            raise ContractError(
                f"Page Data Flow references unlisted Page {flow.source} or {flow.target}"
            )
        expected_extra = f"{flow.target}Extra"
        if flow.extra != expected_extra:
            raise ContractError(
                f"flow into {flow.target} must use target-owned {expected_extra}"
            )
        target_file = pages[flow.target]
        if extra_locations.get(flow.extra) != target_file:
            raise ContractError(
                f"{flow.extra} must be declared in target adapter {target_file.name}"
            )
        target_source = page_sources[target_file]
        extra_fields = validate_freezed_page_extra(
            target_file,
            target_source,
            flow.extra,
        )
        if flow.fields != extra_fields:
            raise ContractError(
                f"flow fields for {flow.extra} must be {', '.join(extra_fields)}"
            )
        target_body = class_body(target_source, flow.target)
        if not re.search(
            rf"\bfinal\s+{re.escape(flow.extra)}\??\s+\$extra\s*;",
            target_body,
        ):
            raise ContractError(f"{flow.target} must declare `$extra` as {flow.extra}")
        for field in extra_fields:
            if not re.search(
                rf"\b{re.escape(field)}\s*:\s*\$extra[?!]?\.{re.escape(field)}\b",
                target_body,
            ):
                raise ContractError(
                    f"{flow.target} must expand $extra.{field} into an ordinary "
                    "View field"
                )
        for component_file in component_sources(target_file):
            component_source = strip_comments(
                component_file.read_text(encoding="utf-8")
            )
            if re.search(rf"\b{re.escape(flow.extra)}\b", component_source):
                raise ContractError(
                    f"{component_file.name} must not use its sibling {flow.extra}; "
                    "Page must expand route transport into ordinary View fields"
                )
    project_root = infer_project_root(module_file)
    validate_route_extra_codec(project_root, {flow.extra for flow in flows})
    validate_component_navigation(project_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module-file", required=True, type=Path)
    args = parser.parse_args()
    try:
        validate_module(args.module_file)
    except ContractError as error:
        print(f"route contract error: {error}", file=sys.stderr)
        return 2
    print("route refactor validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

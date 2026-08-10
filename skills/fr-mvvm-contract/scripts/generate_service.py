#!/usr/bin/env python3
"""Preserve and validate a component SDK-adapter service."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from contract_core import ContractError, bracket_refs, require_file
from contract_parser import ComponentContract, is_api_less_bff, parse_component, parse_page
from resolve import RequestDataEnvelopeProfile, load_request_data_envelope_profile

SERVICE_PATTERN = re.compile(r"^\[([A-Za-z_][A-Za-z0-9_]*)\]$")
ENDPOINT_PATTERN = re.compile(
    r"^#{3,4}\s+(GET|POST|PUT|PATCH|DELETE)\s+(\S+)\s*$", re.MULTILINE
)
SDK_IMPORT_PATTERN = re.compile(
    r"import\s+['\"][^'\"]*api/gen/[^'\"]+['\"](?:\s+as\s+\w+)?\s*;"
)


@dataclass(frozen=True)
class RequestField:
    name: str
    dart_type: str


@dataclass(frozen=True)
class BffEndpoint:
    method: str
    path: str
    request_type: str
    response_type: str
    request_fields: tuple[RequestField, ...] = ()


def parse_bff_markdown(content: str) -> tuple[BffEndpoint, ...]:
    """Parse frontend UI endpoints without reading the backend-owned section."""

    marker = "## BFF-UI-API"
    if marker not in content:
        raise ContractError("BFF Markdown must contain a `## BFF-UI-API` section")
    frontend = content.split(marker, 1)[1]
    matches = list(ENDPOINT_PATTERN.finditer(frontend))
    if not matches:
        raise ContractError("service integration requires at least one UI endpoint")
    endpoints: list[BffEndpoint] = []
    for index, match in enumerate(matches):
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(frontend)
        )
        block = frontend[match.end() : end]
        request = re.search(r"^- Request DTOs:\s*(.+)$", block, re.MULTILINE)
        response = re.search(r"^- Response DTOs:\s*(.+)$", block, re.MULTILINE)
        request_refs = bracket_refs([request.group(1)]) if request else []
        response_refs = bracket_refs([response.group(1)]) if response else []
        if len(request_refs) != 1 or len(response_refs) != 1:
            raise ContractError(
                "each UI endpoint requires exactly one request DTO and one response DTO"
            )
        request_block = re.search(
            r"#### Request JSON5\s*```json5\s*([\s\S]*?)```", block
        )
        fields: list[RequestField] = []
        if request_block:
            lines = request_block.group(1).splitlines()
            for line_index, line in enumerate(lines[:-1]):
                type_match = re.match(r"^  // Dart type:\s*(.+?)\s*$", line)
                if not type_match:
                    continue
                field_match = re.match(
                    r"^  ([A-Za-z_][A-Za-z0-9_]*):", lines[line_index + 1]
                )
                if field_match:
                    fields.append(
                        RequestField(field_match.group(1), type_match.group(1))
                    )
        endpoints.append(
            BffEndpoint(
                match.group(1),
                match.group(2),
                request_refs[0],
                response_refs[0],
                tuple(fields),
            )
        )
    return tuple(endpoints)


def contract_endpoints(component: ComponentContract) -> tuple[BffEndpoint, ...]:
    """Read ordered frontend endpoint identities from the approved contract."""

    endpoints: list[BffEndpoint] = []
    current: re.Match[str] | None = None
    refs: list[str] = []

    def append_current() -> None:
        if current is None:
            return
        if len(refs) != 2:
            raise ContractError("each UI endpoint requires one approved Req/Rsp pair")
        endpoints.append(
            BffEndpoint(current.group(1), current.group(2), refs[0], refs[1])
        )

    for line in component.sections.get("BFF-UI-API", []):
        match = re.match(r"^-?\s*(GET|POST|PUT|PATCH|DELETE)\s+(\S+)\s*$", line)
        if match:
            append_current()
            current = match
            refs = []
        elif current is not None:
            refs.extend(bracket_refs([line]))
    append_current()
    if not endpoints:
        raise ContractError("component service requires at least one UI endpoint")
    return tuple(endpoints)


def operation_name(service_type: str, request_type: str) -> str:
    """Derive the stable semantic method name used by runtime validation."""

    request_stem = request_type
    for suffix in ("BffReq", "RequestDto", "Req"):
        if request_stem.endswith(suffix):
            request_stem = request_stem.removesuffix(suffix)
            break
    else:
        raise ContractError(
            f"request DTO {request_type} must end in BffReq or RequestDto"
        )
    service_stem = service_type.removesuffix("Service")
    if request_stem.startswith(service_stem) and request_stem != service_stem:
        request_stem = request_stem.removeprefix(service_stem)
    if not request_stem:
        request_stem = service_stem
    return request_stem[0].lower() + request_stem[1:]


def uses_request_data_envelope(
    endpoint: BffEndpoint,
    profile: RequestDataEnvelopeProfile | None,
) -> bool:
    return (
        profile is not None
        and endpoint.method != "GET"
        and endpoint.request_type.endswith("RequestDto")
    )


def add_import(source: str, directive: str) -> str:
    if directive in source:
        return source
    imports = list(
        re.finditer(
            r"^\s*import\s+['\"][^'\"]+['\"](?:\s+as\s+\w+)?\s*;\s*$",
            source,
            re.MULTILINE,
        )
    )
    if imports:
        index = imports[-1].end()
        return source[:index] + "\n" + directive + source[index:]
    return directive + "\n" + source


def plan_service(
    component: ComponentContract,
    bff_content: bytes,
    *,
    shell_content: bytes | None = None,
) -> tuple[dict[Path, bytes], Path | None]:
    """Plan only a shell import; never generate or overwrite adapter logic."""

    if component.bff_service is None:
        return {}, None
    declaration = SERVICE_PATTERN.fullmatch(component.bff_service)
    if declaration is None:
        raise ContractError("BFF Service must directly reference one Dart class")
    service_type = declaration.group(1)
    if not is_api_less_bff(component):
        parsed = parse_bff_markdown(bff_content.decode("utf-8"))
        approved = contract_endpoints(component)
        if tuple(
            (e.method, e.path, e.request_type, e.response_type) for e in parsed
        ) != tuple(
            (e.method, e.path, e.request_type, e.response_type) for e in approved
        ):
            raise ContractError(
                "BFF artifact UI endpoints do not match the approved contract"
            )

    shell = Path(component.component_file)
    service_file = shell.with_name(f"{shell.stem}.srv.dart")
    if not service_file.is_file():
        return {}, service_file
    source = service_file.read_text(encoding="utf-8")
    if not re.search(rf"\bclass\s+{re.escape(service_type)}\b", source):
        raise ContractError(
            f"existing BFF service {service_file} does not declare {service_type}"
        )
    if "@RestApi" in source:
        raise ContractError(
            f"{service_file} must be an SDK adapter, not a frontend Retrofit API"
        )
    if SDK_IMPORT_PATTERN.search(source) is None:
        raise ContractError(
            f"{service_file} must import at least one generated SDK from lib/api/gen"
        )
    shell_source = (
        shell_content.decode("utf-8")
        if shell_content is not None
        else require_file(shell, "component library")
    )
    updated = add_import(shell_source, f"import '{service_file.name}';")
    return (
        {shell: updated.encode("utf-8")} if updated != shell_source else {},
        service_file,
    )


def generate_service(component: ComponentContract, *, check: bool) -> Path | None:
    """Preserve and verify the backend-SDK adapter service."""

    bff_file = Path(component.component_file).with_suffix(".bff.md")
    if not bff_file.is_file():
        raise ContractError(f"BFF artifact does not exist: {bff_file}")
    updates, service_file = plan_service(component, bff_file.read_bytes())
    if service_file is None:
        return None
    if not service_file.is_file():
        if check:
            raise ContractError(
                f"SDK adapter service does not exist: {service_file}; implement it "
                "from the backend-owned BFF flow using lib/api/gen"
            )
        return None
    if check and updates:
        raise ContractError(
            f"generated BFF service is stale: {next(iter(updates))}"
        )
    for path, content in updates.items():
        path.write_bytes(content)
    return service_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--page-file", type=Path)
    group.add_argument("--component-file", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        component = (
            parse_page(args.page_file.resolve()).component
            if args.page_file
            else parse_component(args.component_file.resolve())
        )
        service = generate_service(component, check=args.check)
    except (ContractError, OSError, UnicodeError) as error:
        print(f"contract error: {error}", file=sys.stderr)
        return 2
    print(
        "BFF service: backend-owned implementation required"
        if service is None
        else f"BFF service {'current' if args.check else 'preserved'}: {service}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate or check one YAML-front-matter Business/UI BFF artifact."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from contract_core import (
    ContractError,
    find_package_pubspec,
    has_direct_dependency,
    require_file,
)
from contract_parser import (
    ComponentContract,
    is_api_less_bff,
    matching_delimiter,
    parse_component,
    parse_page,
)
from generate_service import (
    contract_endpoints,
    generate_service,
    operation_name,
    parse_bff_markdown,
    uses_request_data_envelope,
)
from openapi_refs import (
    GeneratedSdkOperation,
    backend_markdown_section,
    generated_sdk_operations,
    parse_business_apis,
    validate_bff_business_apis,
)
from resolve import load_request_data_envelope_profile


BFF_META_SCHEMA = "bff-md-meta/v9"
REQUEST_JSON5_BLOCK = re.compile(
    r"(#### Request JSON5\s*```json5\s*\n)([\s\S]*?)(\n?```)",
    re.MULTILINE,
)


@dataclass(frozen=True)
class ApiQueryRecord:
    """One flat API or API-disposition record exposed through mdq."""

    api_id: str
    namespace: str
    api_type: str
    operation: str
    method: str
    path: str
    contract_status: str
    integration_status: str
    authority: str
    verification: str


def yaml_scalar(value: str) -> str:
    """Render one deterministic YAML string scalar without adding dependencies."""

    return json.dumps(value, ensure_ascii=False)


def bff_identity(contract: str) -> tuple[str, int]:
    """Read the stable namespace and version from the FrAcddPage annotation."""

    annotations = list(re.finditer(r"@FrAcddPage\s*\(", contract))
    if len(annotations) != 1:
        raise ContractError(
            "BFF contract must declare exactly one @FrAcddPage annotation"
        )
    opening = contract.find("(", annotations[0].start())
    closing = matching_delimiter(contract, opening, "(", ")")
    arguments = contract[opening + 1 : closing]
    namespace = re.search(
        r"\bnamespace\s*:\s*r?(['\"])(.*?)\1",
        arguments,
        re.DOTALL,
    )
    if namespace is None:
        raise ContractError("@FrAcddPage must declare a string-literal namespace")
    version = re.search(r"\bversion\s*:\s*(\d+)", arguments)
    return namespace.group(2), int(version.group(1)) if version else 1


def mdq_metadata() -> list[str]:
    """Return the persistent API-record query contract for one BFF artifact."""

    columns = (
        "[API ID, Namespace, API Type, Operation, Method, Path, Contract Status, "
        "Integration Status, Authority, Verification]"
    )
    projection = (
        "[namespace, api_type, operation, method, path, contract_status, "
        "integration_status, authority, verification]"
    )
    return [
        "mdq:",
        "  version: 2",
        "  dialect: gfm",
        "  actors:",
        "    read: mixed",
        "    write: machine",
        "  records:",
        "    boundary:",
        "      source: table-row",
        "      under_heading: API Query Records",
        f"      columns: {columns}",
        "    key:",
        "      source: column",
        "      column: API ID",
        "  fields:",
        "    namespace: {source: column, column: Namespace}",
        "    api_type: {source: column, column: API Type}",
        "    operation: {source: column, column: Operation}",
        "    method: {source: column, column: Method}",
        "    path: {source: column, column: Path}",
        "    contract_status: {source: column, column: Contract Status}",
        "    integration_status: {source: column, column: Integration Status}",
        "    authority: {source: column, column: Authority}",
        "    verification: {source: column, column: Verification}",
        "  queries:",
        "    api_by_id:",
        "      match: {source: key, operator: eq}",
        f"      select: {projection}",
        "      expect: {max_matches: 1, max_record_lines: 1, max_record_bytes: 4096, structured: true}",
        "    apis_by_type:",
        "      match: {source: field, field: api_type, operator: eq}",
        f"      select: {projection}",
        "      expect: {max_matches: 256, max_record_lines: 1, max_total_bytes: 262144, structured: true}",
        "    apis_by_integration_status:",
        "      match: {source: field, field: integration_status, operator: eq}",
        f"      select: {projection}",
        "      expect: {max_matches: 256, max_record_lines: 1, max_total_bytes: 262144, structured: true}",
        "    apis_by_path:",
        "      match: {source: field, field: path, operator: eq}",
        f"      select: {projection}",
        "      expect: {max_matches: 32, max_record_lines: 1, max_total_bytes: 131072, structured: true}",
        "  tolerance:",
        "    incomplete: false",
    ]


def _gfm_cell(value: str) -> str:
    """Keep one generated table value on one unambiguous GFM row."""

    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _service_sdk_operations(
    component_file: Path,
) -> tuple[GeneratedSdkOperation, ...]:
    """Return generated SDK operations called by this component's service."""

    service_file = component_file.with_name(f"{component_file.stem}.srv.dart")
    if not service_file.is_file():
        return ()
    service_source = service_file.read_text(encoding="utf-8")
    return tuple(
        operation
        for operation in generated_sdk_operations(component_file)
        if re.search(
            rf"\.\s*{re.escape(operation.operation)}\s*\(", service_source
        )
    )


def _ui_endpoint_integrated(
    component: ComponentContract, service_type: str, request_type: str
) -> bool:
    """Return whether Service and ViewModel contain the final UI API call path."""

    component_file = Path(component.component_file)
    service_file = component_file.with_name(f"{component_file.stem}.srv.dart")
    vm_file = component_file.with_name(f"{component_file.stem}.vm.dart")
    if not service_file.is_file() or not vm_file.is_file():
        return False
    operation = operation_name(service_type, request_type)
    service_source = service_file.read_text(encoding="utf-8")
    vm_source = vm_file.read_text(encoding="utf-8")
    return bool(
        re.search(rf"\b{re.escape(operation)}\s*\(", service_source)
        and re.search(
            rf"\bawait\s+(?:this\.)?[A-Za-z_][A-Za-z0-9_]*"
            rf"\s*\.\s*{re.escape(operation)}\s*\(",
            vm_source,
        )
    )


def api_query_records(
    component: ComponentContract, namespace: str, backend: str
) -> tuple[ApiQueryRecord, ...]:
    """Derive query records without granting the index domain API authority."""

    component_file = Path(component.component_file)
    service_file = component_file.with_name(f"{component_file.stem}.srv.dart")
    service_evidence = service_file.name
    declared_calls, _ = parse_business_apis(
        backend + "## BFF-UI-API\n"
    )
    sdk_operations = generated_sdk_operations(component_file)
    called_operations = _service_sdk_operations(component_file)
    called_names = {operation.operation for operation in called_operations}
    by_endpoint: dict[tuple[str, str], list[GeneratedSdkOperation]] = {}
    for operation in sdk_operations:
        by_endpoint.setdefault((operation.method, operation.path), []).append(operation)

    records: list[ApiQueryRecord] = []
    declared_endpoints: set[tuple[str, str]] = set()
    for call in declared_calls:
        endpoint = (call.method, call.path)
        declared_endpoints.add(endpoint)
        candidates = by_endpoint.get(endpoint, [])
        selected = next(
            (candidate for candidate in candidates if candidate.operation in called_names),
            candidates[0] if candidates else None,
        )
        integrated = selected is not None and selected.operation in called_names
        operation = selected.operation if selected is not None else call.call_id
        records.append(
            ApiQueryRecord(
                api_id=f"backend:{namespace}:{call.call_id}",
                namespace=namespace,
                api_type="BFF-BZ-API",
                operation=operation,
                method=call.method,
                path=call.path,
                contract_status="declared",
                integration_status="integrated" if integrated else "unconfirmed",
                authority="Backend",
                verification=(
                    f"{service_evidence}:{operation}"
                    if integrated
                    else "backend BFF declaration"
                ),
            )
        )

    for operation in sorted(
        called_operations, key=lambda item: (item.method, item.path, item.operation)
    ):
        if (operation.method, operation.path) in declared_endpoints:
            continue
        records.append(
            ApiQueryRecord(
                api_id=f"backend:{namespace}:runtime:{operation.operation}",
                namespace=namespace,
                api_type="BFF-BZ-API",
                operation=operation.operation,
                method=operation.method,
                path=operation.path,
                contract_status="missing_backend_contract",
                integration_status="integrated",
                authority="Code/Test Fact",
                verification=f"{service_evidence}:{operation.operation}",
            )
        )

    if not declared_calls and not called_operations:
        records.append(
            ApiQueryRecord(
                api_id=f"backend:{namespace}:none",
                namespace=namespace,
                api_type="BFF-BZ-API",
                operation="none",
                method="-",
                path="-",
                contract_status="api_less",
                integration_status="not_required",
                authority="Backend",
                verification="BFF disposition",
            )
        )

    if is_api_less_bff(component):
        records.append(
            ApiQueryRecord(
                api_id=f"ui:{namespace}:none",
                namespace=namespace,
                api_type="BFF-UI-API",
                operation="none",
                method="-",
                path="-",
                contract_status="api_less",
                integration_status="not_required",
                authority="Frontend",
                verification="BFF disposition",
            )
        )
    else:
        service = re.fullmatch(r"\[([A-Za-z_][A-Za-z0-9_]*)\]", component.bff_service or "")
        service_type = service.group(1) if service else component.view.removesuffix("View") + "Service"
        vm_file = component_file.with_name(f"{component_file.stem}.vm.dart")
        for endpoint in contract_endpoints(component):
            operation = operation_name(service_type, endpoint.request_type)
            integrated = _ui_endpoint_integrated(
                component, service_type, endpoint.request_type
            )
            records.append(
                ApiQueryRecord(
                    api_id=(
                        f"ui:{namespace}:{endpoint.method.lower()}:"
                        f"{endpoint.path}"
                    ),
                    namespace=namespace,
                    api_type="BFF-UI-API",
                    operation=operation,
                    method=endpoint.method,
                    path=endpoint.path,
                    contract_status="declared",
                    integration_status=(
                        "integrated" if integrated else "unconfirmed"
                    ),
                    authority="Frontend",
                    verification=(
                        f"{service_evidence} + {vm_file.name}"
                        if integrated
                        else "frontend BFF declaration"
                    ),
                )
            )
    return tuple(records)


def api_query_table(records: tuple[ApiQueryRecord, ...]) -> str:
    """Render the flat verification matrix consumed by the mdq contract."""

    header = (
        "| API ID | Namespace | API Type | Operation | Method | Path | "
        "Contract Status | Integration Status | Authority | Verification |"
    )
    delimiter = "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    rows = [header, delimiter]
    for record in records:
        values = (
            record.api_id,
            record.namespace,
            record.api_type,
            record.operation,
            record.method,
            record.path,
            record.contract_status,
            record.integration_status,
            record.authority,
            record.verification,
        )
        rows.append("| " + " | ".join(_gfm_cell(value) for value in values) + " |")
    return "\n".join(
        [
            "## API Query Records",
            "",
            "> Authority: Verification projection. Generated from the BFF contract, "
            "generated SDK symbols, and component runtime call sites; it never "
            "redefines backend or frontend API semantics.",
            "",
            *rows,
        ]
    )


def split_top_level_parameters(source: str) -> list[str]:
    """Split Dart constructor parameters while preserving nested defaults/types."""

    parameters: list[str] = []
    start = 0
    depths = {"(": 0, "[": 0, "{": 0, "<": 0}
    closing = {")": "(", "]": "[", "}": "{", ">": "<"}
    quote: str | None = None
    escaped = False
    for index, char in enumerate(source):
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
        elif char in depths:
            depths[char] += 1
        elif char in closing:
            depths[closing[char]] = max(0, depths[closing[char]] - 1)
        elif char == "," and not any(depths.values()):
            value = source[start:index].strip()
            if value:
                parameters.append(value)
            start = index + 1
    value = source[start:].strip()
    if value:
        parameters.append(value)
    return parameters


def strip_leading_annotation(parameter: str) -> str:
    """Remove Dart parameter annotations such as @Default(...) or @JsonKey(...)."""

    value = parameter.lstrip()
    while value.startswith("@"):
        match = re.match(r"@[A-Za-z_][A-Za-z0-9_.]*", value)
        if match is None:
            break
        end = match.end()
        if end < len(value) and value[end] == "(":
            depth = 0
            quote: str | None = None
            escaped = False
            for index in range(end, len(value)):
                char = value[index]
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
                elif char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        end = index + 1
                        break
        value = value[end:].lstrip()
    return value


def ui_model_fields(contract: str, models: list[str]) -> list[tuple[str, str, str]]:
    """Read frontend-owned Freezed factory fields for the UI Contract section."""

    fields: list[tuple[str, str, str]] = []
    for model in models:
        factory = re.search(
            rf"const\s+factory\s+{re.escape(model)}\s*\(\s*\{{([\s\S]*?)\}}\s*\)",
            contract,
        )
        if factory is None:
            continue
        for raw in split_top_level_parameters(factory.group(1)):
            parameter = strip_leading_annotation(raw)
            parameter = re.sub(r"^required\s+", "", parameter).strip()
            parameter = re.sub(r"\s*=\s*[\s\S]*$", "", parameter).strip()
            match = re.match(r"(.+?)\s+([A-Za-z_][A-Za-z0-9_]*)$", parameter)
            if match:
                fields.append((model, match.group(2), match.group(1).strip()))
    return fields


def json5_example_for_dart_type(dart_type: str) -> str:
    """Render a concise, valid JSON5 example value for a UI state type."""

    if dart_type.endswith("?"):
        return "null"
    normalized = dart_type.rstrip("?").strip()
    if normalized == "bool":
        return "false"
    if normalized in {"int", "double", "num"}:
        return "0"
    if normalized.startswith("List<") or normalized.startswith("Set<"):
        return "[]"
    if normalized.startswith("Map<"):
        return "{}"
    if normalized == "String":
        return "'string'"
    return "{}"


def ui_state_json5(fields: list[tuple[str, str, str]]) -> list[str]:
    """Render frontend state as JSON5 rather than a Markdown field table."""

    if not fields:
        return ["- none"]
    lines = ["```json5", "{"]
    for model, field, dart_type in fields:
        lines.extend(
            [
                f"  // Model: {model}",
                f"  // Dart type: {dart_type}",
                "  // Authority: Frontend",
                f"  {field}: {json5_example_for_dart_type(dart_type)},",
            ]
        )
    return [*lines, "}", "```"]


def markdown_section(title: str, lines: list[str]) -> str:
    """Render one readable contract subsection from source contract lines."""

    content = "\n".join(lines).strip()
    return f"### {title}\n\n{content or '- none'}\n"


def wrap_request_data_blocks(
    extracted_text: str,
    component: ComponentContract,
) -> str:
    """Render interceptor-owned request envelopes in the published BFF artifact."""

    if is_api_less_bff(component):
        return extracted_text
    profile = load_request_data_envelope_profile(Path(component.component_file))
    if profile is None:
        return extracted_text
    endpoints = parse_bff_markdown(extracted_text)
    block_index = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal block_index
        if block_index >= len(endpoints):
            raise ContractError("BFF extractor emitted unmatched request JSON5 blocks")
        endpoint = endpoints[block_index]
        block_index += 1
        if not uses_request_data_envelope(endpoint, profile):
            return match.group(0)
        payload = match.group(2).strip()
        if not (payload.startswith("{") and payload.endswith("}")):
            raise ContractError(
                "request-data-envelope profile requires object-shaped Request JSON5"
            )
        inner = payload[1:-1].strip()
        indented_inner = "\n".join(
            f"    {line}" if line else "" for line in inner.splitlines()
        )
        wrapped = "{\n  // Added by the project request-data-envelope interceptor.\n"
        wrapped += "  data: {\n"
        if indented_inner:
            wrapped += indented_inner + "\n"
        wrapped += "  },\n}"
        return match.group(1) + wrapped + match.group(3)

    rendered = REQUEST_JSON5_BLOCK.sub(replace, extracted_text)
    if block_index != len(endpoints):
        raise ContractError("BFF extractor omitted request JSON5 blocks")
    return rendered


def default_backend_section() -> str:
    """Create the backend-owned placeholder for a new BFF artifact."""

    return "\n".join(
        [
            "## BFF-BZ-API",
            "",
            "> Authority: Backend. This business-logic API cannot be inferred "
            "from Figma/UI requirements. Backend developers provide its business "
            "flow and configured .openapi.json evidence; frontend tooling must "
            "preserve this entire section byte-for-byte.",
            "",
            "### BFF-BZ-API",
            "",
            "- none",
            "",
            "### 业务流程",
            "",
            "- none",
            "",
        ]
    )


def render_dual_authority_bff(
    component: ComponentContract,
    extracted: bytes,
    *,
    existing: str | None = None,
) -> bytes:
    """Render frontend-owned content while preserving backend-owned Markdown."""

    extracted_text = wrap_request_data_blocks(extracted.decode("utf-8"), component)
    contract_path = Path(component.contract_file)
    contract = require_file(contract_path, "component contract")
    view_path = Path(component.component_file).with_name(
        f"{Path(component.component_file).stem}.v.dart"
    )
    view_source = (
        require_file(view_path, "component View source") if view_path.is_file() else ""
    )
    namespace, contract_version = bff_identity(contract + "\n" + view_source)
    figma = next(
        (
            line.removeprefix("- Node:").strip()
            for line in component.sections.get("Figma", [])
            if line.startswith("- Node:")
        ),
        "",
    )
    metadata = [
        "---",
        "bff_meta:",
        f"  schema: {yaml_scalar(BFF_META_SCHEMA)}",
        f"  namespace: {yaml_scalar(namespace)}",
        f"  contract_version: {contract_version}",
    ]
    if figma:
        metadata.extend(
            [
                "  ui_source:",
                "    type: figma",
                f"    url: {yaml_scalar(figma)}",
            ]
        )
    metadata.extend(mdq_metadata())
    metadata.extend(["---", ""])

    business_start = extracted_text.find("## BFF-UI-API")
    if business_start < 0:
        raise ContractError("BFF extractor output must contain `## BFF-UI-API`")
    ui_api = extracted_text[business_start:].strip()
    ui_api = re.sub(r"^## BFF-UI-API\s*$", "### 接口描述", ui_api, flags=re.MULTILINE)
    ui_api = re.sub(
        r"^### (GET|POST|PUT|PATCH|DELETE) ", r"#### \1 ", ui_api, flags=re.MULTILINE
    )
    state_fields = ui_model_fields(contract, component.models)
    state_rows = ui_state_json5(state_fields)

    ui_sections = [
        "## UI Contract",
        "",
        "> Authority: Frontend. These fields are local presentation/state data and are not HTTP DTO fields.",
        "",
        "### UI State",
        "",
        *state_rows,
        "",
        markdown_section("UI Behavior", component.sections.get("Behavior", [])).strip(),
        markdown_section(
            "UI Structure", component.sections.get("Widget Tree", [])
        ).strip(),
        "",
        "## Integration Mapping",
        "",
        "> Authority: Frontend integration. Mapping may transform values but cannot redefine backend field meaning.",
        "",
        *(component.sections.get("Request Field Sources", []) or ["- none"]),
    ]
    backend = (
        backend_markdown_section(existing)
        if existing is not None
        else default_backend_section()
    )
    query_table = api_query_table(api_query_records(component, namespace, backend))
    output = (
        "\n".join(metadata)
        + f"# {component.view} BFF Contract\n\n"
        + backend
        + "## BFF-UI-API\n\n"
        + "> Authority: Frontend. AI derives this UI data-request API and its DTOs from approved Figma/UI requirements; it must remain separate from BFF-BZ-API business logic and OpenAPI DTOs.\n\n"
        + ui_api
        + "\n\n"
        + "\n".join(ui_sections).rstrip()
        + "\n\n"
        + query_table
        + "\n"
    )
    return output.encode("utf-8")


def is_bff_mode(component: ComponentContract) -> bool:
    """Return whether the contract explicitly declares BFF ownership."""

    contract = require_file(Path(component.contract_file), "component contract")
    return "BFF-UI-API" in component.sections or "FrAcddMode.bff" in contract


def extractor_command(input_file: Path, output_file: Path) -> list[str]:
    return [
        os.environ.get("FR_MVVM_FVM", "fvm"),
        "dart",
        "run",
        "fr_acdd:extract_bff",
        "--format",
        "json5",
        "--input",
        str(input_file),
        "--output",
        str(output_file),
    ]


def run_extractor_preflight(package_root: Path) -> None:
    fvm = os.environ.get("FR_MVVM_FVM", "fvm")
    if not shutil.which(fvm):
        raise ContractError(
            f"BFF extractor preflight failed: `{fvm}` is not executable; "
            "install/configure FVM before generating BFF artifacts"
        )
    result = subprocess.run(
        [fvm, "dart", "run", "fr_acdd:extract_bff", "--help"],
        cwd=package_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise ContractError(
            "BFF extractor preflight failed. Verify that fr_acdd is compatible "
            f"with the resolved analyzer version.\n{detail}"
        )


def preflight_bff(component: ComponentContract) -> tuple[Path, Path, Path] | None:
    """Validate BFF ownership and extractor availability without writing files."""

    if not is_bff_mode(component):
        return None
    component_file = Path(component.component_file)
    contract_file = Path(component.contract_file)
    output_file = component_file.with_suffix(".bff.md")
    pubspec = find_package_pubspec(component_file)
    if not has_direct_dependency(pubspec, "fr_acdd", section="dependencies"):
        raise ContractError(
            f"{pubspec} must directly declare fr_acdd under dependencies in BFF-JSON mode"
        )
    if not is_api_less_bff(component):
        run_extractor_preflight(pubspec.parent)
    return contract_file, output_file, pubspec.parent


def render_bff(component: ComponentContract) -> tuple[Path, bytes] | None:
    """Render a BFF artifact to memory without changing the component directory."""

    preflight = preflight_bff(component)
    if preflight is None:
        return None
    contract_file, output_file, package_root = preflight
    existing = output_file.read_text(encoding="utf-8") if output_file.is_file() else None
    if existing is not None:
        validate_bff_business_apis(existing, Path(component.component_file))
    if is_api_less_bff(component):
        return output_file, render_dual_authority_bff(
            component, b"## BFF-UI-API\n\n-\n", existing=existing
        )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_file.stem}.", suffix=".md", dir=output_file.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    temporary.unlink()
    try:
        result = subprocess.run(
            extractor_command(contract_file, temporary),
            cwd=package_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode or not temporary.is_file():
            detail = (result.stderr or result.stdout).strip()
            raise ContractError(
                "BFF extraction failed; no artifact was replaced. Verify fr_acdd/analyzer "
                f"compatibility and the contract annotations.\n{detail}"
            )
        extracted = temporary.read_bytes()
        return output_file, render_dual_authority_bff(
            component, extracted, existing=existing
        )
    finally:
        temporary.unlink(missing_ok=True)


def generate_bff(component: ComponentContract, *, check: bool) -> Path | None:
    """Generate atomically, or compare the current artifact with fresh output."""

    expected = Path(component.component_file).with_suffix(".bff.md")
    if check and is_bff_mode(component) and not expected.is_file():
        raise ContractError(f"required BFF artifact does not exist: {expected}")
    output = render_bff(component)
    if output is None:
        return None
    output_file, content = output
    if check:
        if output_file.read_bytes() != content:
            raise ContractError(
                f"BFF artifact is stale: {output_file}; regenerate it with "
                "generate_bff.py"
            )
        generate_service(component, check=True)
        return output_file

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_file.stem}.",
        suffix=output_file.suffix,
        dir=output_file.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_bytes(content)
        mode = (
            stat.S_IMODE(output_file.stat().st_mode) if output_file.exists() else 0o644
        )
        temporary.chmod(mode)
        temporary.replace(output_file)
    finally:
        temporary.unlink(missing_ok=True)
    generate_service(component, check=False)
    return output_file


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
        output = generate_bff(component, check=args.check)
    except ContractError as error:
        print(f"contract error: {error}", file=sys.stderr)
        return 2
    if output is None:
        print("BFF artifact: not required in explicit API mode")
    else:
        action = "current" if args.check else "generated"
        print(f"BFF artifact {action}: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate or check one Markdown Business/UI BFF artifact."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
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
    parse_component,
    parse_page,
)
from generate_service import (
    generate_service,
    parse_bff_markdown,
    uses_request_data_envelope,
)
from openapi_refs import validate_backend_calls
from resolve import load_request_data_envelope_profile


REQUEST_JSON5_BLOCK = re.compile(
    r"(#### Request JSON5\s*```json5\s*\n)([\s\S]*?)(\n?```)",
    re.MULTILINE,
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


def render_dual_authority_bff(component: ComponentContract, extracted: bytes) -> bytes:
    """Render UI API DTOs, backend OpenAPI calls, and frontend UI state."""

    extracted_text = wrap_request_data_blocks(extracted.decode("utf-8"), component)
    endpoints = (
        [] if is_api_less_bff(component) else parse_bff_markdown(extracted_text)
    )
    backend_calls = validate_backend_calls(component)
    contract_path = Path(component.contract_file)
    contract = require_file(contract_path, "component contract")

    business_start = extracted_text.find("## BFF-API")
    if business_start < 0:
        raise ContractError("BFF extractor output must contain `## BFF-API`")
    ui_api = extracted_text[business_start:].strip()
    ui_api = re.sub(r"^## BFF-API\s*$", "### 接口描述", ui_api, flags=re.MULTILINE)
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
    if backend_calls:
        backend_documents = sorted({call.location for call in backend_calls})
        backend_api_list = [
            f"- [{call.call_id}] `{call.method} {call.path}` @ `{call.location}`"
            for call in backend_calls
        ]
        backend_usage = component.sections.get("Backend Call Flow", [])
        backend_sequence = [
            f"{index}. {item.lstrip('- ').strip()}"
            for index, item in enumerate(backend_usage, start=1)
        ]
    else:
        backend_documents = ["- none"]
        backend_api_list = ["- none"]
        backend_usage = ["- none"]
        backend_sequence = ["- none"]
    backend_document_lines = (
        backend_documents
        if backend_documents == ["- none"]
        else [f"- `{document}`" for document in backend_documents]
    )
    backend_sections = [
        "## 后端逻辑流程接口",
        "",
        "> Authority: Backend. API and DTO definitions are created and maintained only by backend developers in the referenced OpenAPI documents; this BFF never creates or redefines them.",
        "",
        "### .openapi.json 文档引用",
        "",
        *backend_document_lines,
        "",
        "### 本 BFF 使用的 API 列表",
        "",
        *backend_api_list,
        "",
        "### API 使用场景",
        "",
        *backend_usage,
        "",
        "### 调用时序",
        "",
        *backend_sequence,
        "",
    ]
    output = (
        f"# {component.view} BFF Contract\n\n"
        + "\n".join(backend_sections)
        + "## 前端 UI 数据接口\n\n"
        + "> Authority: Frontend. AI may derive UI-facing BFF paths and DTOs from approved Figma/UI requirements; they must remain separate from backend APIs and DTOs.\n\n"
        + ui_api
        + "\n\n"
        + "\n".join(ui_sections).rstrip()
        + "\n"
    )
    return output.encode("utf-8")


def is_bff_mode(component: ComponentContract) -> bool:
    """Resolve the contract mode, defaulting to BFF unless API is explicit."""

    contract = require_file(Path(component.contract_file), "component contract")
    if "BFF-API" in component.sections or "FrAcddMode.bff" in contract:
        return True
    return "API" not in component.sections


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
    if is_api_less_bff(component):
        return output_file, render_dual_authority_bff(
            component, b"## BFF-API\n\n-\n"
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
            component, extracted
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

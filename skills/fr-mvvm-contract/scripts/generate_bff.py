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
from pathlib import Path

from contract_core import (
    ContractError,
    find_package_pubspec,
    has_direct_dependency,
    require_file,
)
from contract_parser import ComponentContract, parse_component, parse_page
from generate_service import generate_service, parse_bff_markdown


BFF_META_SCHEMA = "bff-md-meta/v4"


def yaml_scalar(value: str) -> str:
    """Render one deterministic YAML string scalar without adding dependencies."""

    return json.dumps(value, ensure_ascii=False)


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


def markdown_section(title: str, lines: list[str]) -> str:
    """Render one readable contract subsection from source contract lines."""

    content = "\n".join(lines).strip()
    return f"### {title}\n\n{content or '- none'}\n"


def render_dual_authority_bff(
    component: ComponentContract, extracted: bytes, package_root: Path
) -> bytes:
    """Wrap the backend DTO artifact with YAML metadata and frontend UI state."""

    extracted_text = extracted.decode("utf-8")
    endpoints = parse_bff_markdown(extracted_text)
    contract_path = Path(component.contract_file)
    contract = require_file(contract_path, "component contract")
    try:
        relative_contract = contract_path.relative_to(package_root).as_posix()
    except ValueError:
        relative_contract = contract_path.name
    figma = " ".join(component.sections.get("Figma", [])).strip()
    metadata = [
        "---",
        "bff_meta:",
        f"  schema: {yaml_scalar(BFF_META_SCHEMA)}",
        '  contract_version: "1.0.0"',
        '  ui_revision: "1.0.0"',
        "  mode: BFF-JSON",
        f"  contract_file: {yaml_scalar(relative_contract)}",
        "  authorities:",
        "    business:",
        "      owner: backend",
        "    ui:",
        "      owner: frontend",
    ]
    if figma:
        metadata.extend(
            [
                "      source:",
                "        type: figma",
                f"        url: {yaml_scalar(figma)}",
            ]
        )
    metadata.append("  apis:")
    for endpoint in endpoints:
        metadata.extend(
            [
                f"    - method: {endpoint.method}",
                f"      route: {yaml_scalar(endpoint.path)}",
                f"      request: {endpoint.request_type}",
                f"      response: {endpoint.response_type}",
                f"      behavior: {component.api_kind or 'unknown'}",
            ]
        )
    metadata.extend(["---", ""])

    business_start = extracted_text.find("## BFF-API")
    if business_start < 0:
        raise ContractError("BFF extractor output must contain `## BFF-API`")
    business = extracted_text[business_start:].strip()
    state_fields = ui_model_fields(contract, component.models)
    if state_fields:
        state_rows = [
            "| Model | UI Field | Dart Type | Authority |",
            "| --- | --- | --- | --- |",
            *(
                f"| `{model}` | `{field}` | `{dart_type}` | Frontend |"
                for model, field, dart_type in state_fields
            ),
        ]
    else:
        state_rows = ["- none"]

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
        markdown_section("UI Structure", component.sections.get("Widget Tree", [])).strip(),
        "",
        "## Integration Mapping",
        "",
        "> Authority: Frontend integration. Mapping may transform values but cannot redefine backend field meaning.",
        "",
        *(
            component.sections.get("Request Field Sources", [])
            or ["- none"]
        ),
    ]
    output = (
        "\n".join(metadata)
        + f"# {component.view} BFF Contract\n\n"
        + "## Business Contract\n\n"
        + "> Authority: Backend. Request, response, error, and business-rule fields must come from backend definitions.\n\n"
        + business
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
    run_extractor_preflight(pubspec.parent)
    return contract_file, output_file, pubspec.parent


def render_bff(component: ComponentContract) -> tuple[Path, bytes] | None:
    """Render a BFF artifact to memory without changing the component directory."""

    preflight = preflight_bff(component)
    if preflight is None:
        return None
    contract_file, output_file, package_root = preflight
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
            component, extracted, package_root
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

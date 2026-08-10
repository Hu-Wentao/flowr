"""Validate backend-owned BFF API annotations against OpenAPI and generated SDKs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from contract_core import ContractError
from resolve import ResolveError, load_backend_openapi_profile

HTTP_METHODS = "GET|POST|PUT|PATCH|DELETE"
BACKEND_CALL_PATTERN = re.compile(
    rf"^-\s*([A-Za-z_][A-Za-z0-9_]*)\s*<-\s*(.+?)\s*\|\s*"
    rf"({HTTP_METHODS})\s+(\S+)\s*$"
)
SDK_CALL_PATTERN = re.compile(
    r"^-\s*([A-Za-z_][A-Za-z0-9_]*)\s*<-\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*$"
)
BUSINESS_API_PATTERN = re.compile(
    rf"^-\s*\[([A-Za-z_][A-Za-z0-9_]*)\]\s+({HTTP_METHODS})\s+(\S+)\s*\|\s*"
    r"Parameters:\s*(.+?)\s*\|\s*Response:\s*(.+?)\s*$"
)
MAX_OPENAPI_BYTES = 8 * 1024 * 1024
NETWORK_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class BackendCall:
    """One BFF-to-backend call resolved by OpenAPI document and operation path."""

    call_id: str
    location: str
    method: str
    path: str


@dataclass(frozen=True)
class SdkCall:
    """One BFF-to-SDK call, identified only by its generated Dart symbol."""

    call_id: str
    client: str
    operation: str


@dataclass(frozen=True)
class BusinessApi:
    """One backend-owned business API annotation from a BFF Markdown file."""

    call_id: str
    method: str
    path: str
    parameters: str
    response_type: str


@dataclass(frozen=True)
class GeneratedSdkOperation:
    """One generated Retrofit operation available to a component service."""

    method: str
    path: str
    operation: str
    source: Path


def is_network_location(location: str) -> bool:
    return urlsplit(location).scheme.lower() in {"http", "https"}


def validate_openapi_location_name(location: str) -> None:
    parsed = urlsplit(location)
    if parsed.username is not None or parsed.password is not None:
        raise ContractError(
            "backend OpenAPI URLs must not embed credentials: " + location
        )
    path = parsed.path if parsed.scheme else location
    if not path.lower().endswith(".openapi.json"):
        raise ContractError(
            "backend OpenAPI locations must end with `.openapi.json`: " + location
        )


def parse_backend_calls(component: object) -> tuple[BackendCall, ...]:
    """Parse `id <- location | METHOD /path` entries from a component contract."""

    lines = component.sections.get("Backend Calls", [])
    if not lines:
        return ()
    if len(lines) == 1 and lines[0].strip() == "- none":
        return ()
    calls: list[BackendCall] = []
    seen: set[str] = set()
    for line in lines:
        match = BACKEND_CALL_PATTERN.fullmatch(line.strip())
        if match is None:
            raise ContractError(
                "Backend Calls entries must use "
                "`- id <- <local-root-relative path|http(s) URL> | METHOD /path`"
            )
        call_id, location, method, path = (value.strip() for value in match.groups())
        if call_id in seen:
            raise ContractError(f"Backend Calls contains duplicate id `{call_id}`")
        if not path.startswith("/"):
            raise ContractError(
                f"backend call `{call_id}` API request path must begin with `/`"
            )
        validate_openapi_location_name(location)
        seen.add(call_id)
        calls.append(BackendCall(call_id, location, method, path))
    return tuple(calls)


def parse_sdk_calls(component: object) -> tuple[SdkCall, ...]:
    """Parse `id <- GeneratedApi.operation` entries without HTTP details."""

    lines = component.sections.get("SDK Calls", [])
    if not lines or (len(lines) == 1 and lines[0].strip() == "- none"):
        return ()
    calls: list[SdkCall] = []
    seen: set[str] = set()
    for line in lines:
        match = SDK_CALL_PATTERN.fullmatch(line.strip())
        if match is None:
            raise ContractError(
                "SDK Calls entries must use `- id <- GeneratedApi.operation`; "
                "BFF contracts must not declare SDK HTTP paths or parameters"
            )
        call_id, client, operation = match.groups()
        if call_id in seen:
            raise ContractError(f"SDK Calls contains duplicate id `{call_id}`")
        seen.add(call_id)
        calls.append(SdkCall(call_id, client, operation))
    return tuple(calls)


def generated_sdk_symbols(component_file: Path) -> set[tuple[str, str]]:
    """Read generated SDK client operation symbols without interpreting wire DTOs."""

    root = find_project_root(component_file)
    source_root = root / "lib/api/gen"
    symbols: set[tuple[str, str]] = set()
    for source in source_root.glob("*_api.dart") if source_root.is_dir() else ():
        text = source.read_text(encoding="utf-8")
        clients = re.findall(r"abstract\s+class\s+([A-Za-z_][A-Za-z0-9_]*)", text)
        operations = re.findall(r"Future<\S+>\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text)
        symbols.update(
            (client, operation) for client in clients for operation in operations
        )
    return symbols


def validate_sdk_calls(component: object) -> tuple[SdkCall, ...]:
    """Validate SDK identifiers and their orchestration-only flow."""

    has_calls = "SDK Calls" in component.sections
    has_flow = "SDK Call Flow" in component.sections
    if has_calls != has_flow:
        raise ContractError("SDK Calls and SDK Call Flow must be declared together")
    calls = parse_sdk_calls(component)
    flow = component.sections.get("SDK Call Flow", [])
    if not calls:
        if has_calls and flow != ["- none"]:
            raise ContractError("SDK Calls and SDK Call Flow must both be `- none`")
        return ()
    symbols = generated_sdk_symbols(Path(component.component_file))
    for call in calls:
        if (call.client, call.operation) not in symbols:
            raise ContractError(
                f"SDK call `{call.call_id}` does not exist in lib/api/gen: "
                f"{call.client}.{call.operation}"
            )
        if f"[{call.call_id}]" not in "\n".join(flow):
            raise ContractError(f"SDK Call Flow must reference `[{call.call_id}]`")
    return calls


def find_project_root(component_file: Path) -> Path:
    """Find the nearest project root used by the generic fallback."""

    start = component_file.resolve().parent
    nearest_pubspec: Path | None = None
    for candidate in (start, *start.parents):
        if nearest_pubspec is None and (candidate / "pubspec.yaml").is_file():
            nearest_pubspec = candidate
        if (candidate / ".git").exists():
            return candidate
    return nearest_pubspec or start


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def resolve_local_openapi(location: str, component_file: Path) -> Path:
    """Resolve a contained path against the configured OpenAPI reference root."""

    raw = Path(location)
    if raw.is_absolute():
        raise ContractError(
            "local backend OpenAPI locations must be relative: " + location
        )
    project_root = find_project_root(component_file).resolve()
    try:
        profile = load_backend_openapi_profile(component_file)
    except ResolveError as error:
        raise ContractError(
            f"invalid backend OpenAPI project config: {error}"
        ) from error
    root = profile.local_root if profile is not None else project_root
    target = (root / raw).resolve()
    if not is_relative_to(target, root):
        raise ContractError(
            "backend OpenAPI location escapes its configured local root: " + location
        )
    if not target.is_file():
        root_label = profile.configured_root if profile is not None else "project root"
        raise ContractError(
            "backend OpenAPI document does not exist under "
            + root_label
            + ": "
            + location
        )
    return target


def read_network_openapi(location: str) -> bytes:
    """Read a bounded public HTTP(S) OpenAPI document."""

    request = Request(
        location,
        headers={
            "Accept": "application/json, application/openapi+json",
            "User-Agent": "fr-mvvm-contract-openapi-validator/1",
        },
    )
    try:
        with urlopen(request, timeout=NETWORK_TIMEOUT_SECONDS) as response:
            final_url = response.geturl()
            if urlsplit(final_url).scheme.lower() not in {"http", "https"}:
                raise ContractError(
                    "backend OpenAPI URL redirected outside HTTP(S): " + final_url
                )
            payload = response.read(MAX_OPENAPI_BYTES + 1)
    except ContractError:
        raise
    except (HTTPError, URLError, OSError) as error:
        raise ContractError(
            f"failed to read backend OpenAPI URL {location}: {error}"
        ) from error
    if len(payload) > MAX_OPENAPI_BYTES:
        raise ContractError(
            f"backend OpenAPI URL exceeds {MAX_OPENAPI_BYTES} bytes: {location}"
        )
    return payload


def load_openapi(call: BackendCall, component_file: Path) -> dict[str, Any]:
    """Load one local or HTTP(S) OpenAPI JSON document."""

    if is_network_location(call.location):
        payload = read_network_openapi(call.location)
    else:
        parsed = urlsplit(call.location)
        if parsed.scheme:
            raise ContractError(
                "backend OpenAPI network locations must use http or https: "
                + call.location
            )
        payload = resolve_local_openapi(call.location, component_file).read_bytes()
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(
            f"backend OpenAPI document is not valid JSON for `{call.call_id}`: {error}"
        ) from error
    if not isinstance(document, dict) or not isinstance(document.get("openapi"), str):
        raise ContractError(
            f"backend OpenAPI document for `{call.call_id}` must declare `openapi`"
        )
    return document


def validate_backend_calls(component: object) -> tuple[SdkCall, ...]:
    """Reject backend-owned API definitions from the frontend source contract."""

    if (
        "Backend Calls" in component.sections
        or "Backend Call Flow" in component.sections
        or "SDK Calls" in component.sections
        or "SDK Call Flow" in component.sections
    ):
        raise ContractError(
            "backend business APIs and flow are backend-owned; edit only the "
            "`后端业务流程与业务逻辑 API` section in the generated BFF Markdown"
        )
    return ()


def backend_markdown_section(content: str) -> str:
    """Return the exact backend-owned Markdown region."""

    start = content.find("## 后端业务流程与业务逻辑 API")
    end = content.find("## 前端 UI 数据接口")
    if start < 0 or end < 0 or end <= start:
        raise ContractError(
            "BFF Markdown must contain the ordered backend and frontend authority sections"
        )
    return content[start:end]


def parse_business_apis(content: str) -> tuple[tuple[BusinessApi, ...], tuple[str, ...]]:
    """Parse backend-owned API annotations and flow without reading DTO fields."""

    section = backend_markdown_section(content)
    if "```" in section or re.search(r"(?m)^\s*[\{\}]\s*,?\s*$", section):
        raise ContractError(
            "backend BFF section must not contain DTO fields or JSON/code blocks"
        )
    api_match = re.search(
        r"### 业务逻辑 API\s*\n([\s\S]*?)(?=\n### 业务流程\s*\n)", section
    )
    flow_match = re.search(r"### 业务流程\s*\n([\s\S]*)$", section)
    if api_match is None or flow_match is None:
        raise ContractError(
            "backend BFF section must contain `### 业务逻辑 API` and `### 业务流程`"
        )
    api_lines = [
        line.strip() for line in api_match.group(1).splitlines() if line.strip()
    ]
    flow = tuple(
        line.strip() for line in flow_match.group(1).splitlines() if line.strip()
    )
    if api_lines == ["- none"]:
        if flow != ("- none",):
            raise ContractError(
                "backend business API and flow must both be `- none`"
            )
        return (), flow
    calls: list[BusinessApi] = []
    seen: set[str] = set()
    for line in api_lines:
        match = BUSINESS_API_PATTERN.fullmatch(line)
        if match is None:
            raise ContractError(
                "business API entries must use `- [id] METHOD /path | "
                "Parameters: name Type[, ...] | Response: Type`"
            )
        call_id, method, path, parameters, response_type = match.groups()
        if call_id in seen:
            raise ContractError(f"business API contains duplicate id `{call_id}`")
        if not path.startswith("/"):
            raise ContractError(
                f"business API `{call_id}` request path must begin with `/`"
            )
        seen.add(call_id)
        calls.append(
            BusinessApi(call_id, method, path, parameters, response_type)
        )
    flow_text = "\n".join(flow)
    for call in calls:
        if f"[{call.call_id}]" not in flow_text:
            raise ContractError(f"business flow must reference `[{call.call_id}]`")
    return tuple(calls), flow


def _openapi_root(component_file: Path) -> Path:
    try:
        profile = load_backend_openapi_profile(component_file)
    except ResolveError as error:
        raise ContractError(
            f"invalid backend OpenAPI project config: {error}"
        ) from error
    return profile.local_root if profile is not None else find_project_root(component_file)


def _generated_sdk_types(component_file: Path) -> set[str]:
    source_root = find_project_root(component_file) / "lib/api/gen"
    types: set[str] = set()
    for source in source_root.glob("*.dart") if source_root.is_dir() else ():
        text = source.read_text(encoding="utf-8")
        types.update(
            re.findall(
                r"\b(?:class|enum|typedef)\s+([A-Za-z_][A-Za-z0-9_]*)", text
            )
        )
    return types


def generated_sdk_operations(
    component_file: Path,
) -> tuple[GeneratedSdkOperation, ...]:
    """Read generated Retrofit method/path-to-symbol mappings deterministically."""

    source_root = find_project_root(component_file) / "lib/api/gen"
    operations: list[GeneratedSdkOperation] = []
    annotation = re.compile(
        rf'^\s*@({HTTP_METHODS})\(\s*["\']([^"\']+)["\']\s*\)\s*$'
    )
    declaration = re.compile(
        r"^\s*Future\s*<.+?>\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        re.DOTALL,
    )
    for source in sorted(source_root.glob("*_api.dart")) if source_root.is_dir() else ():
        if source.name.endswith("_api.g.dart"):
            continue
        pending: tuple[str, str] | None = None
        declaration_lines: list[str] = []
        for line in source.read_text(encoding="utf-8").splitlines():
            api_annotation = annotation.match(line)
            if api_annotation is not None:
                pending = (api_annotation.group(1), api_annotation.group(2))
                declaration_lines = []
                continue
            if pending is None:
                continue
            declaration_lines.append(line)
            method_declaration = declaration.match("\n".join(declaration_lines))
            if method_declaration is not None:
                operations.append(
                    GeneratedSdkOperation(
                        method=pending[0],
                        path=pending[1],
                        operation=method_declaration.group(1),
                        source=source,
                    )
                )
                pending = None
                declaration_lines = []
                continue
            stripped = line.strip()
            if stripped.startswith(("@", "class ", "abstract class ", "}")):
                pending = None
                declaration_lines = []
    return tuple(operations)


def validate_bff_business_apis(
    content: str, component_file: Path
) -> tuple[BusinessApi, ...]:
    """Validate backend annotations without modifying their Markdown."""

    calls, _ = parse_business_apis(content)
    if not calls:
        return ()
    root = _openapi_root(component_file)
    documents: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.openapi.json")) if root.is_dir() else ():
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ContractError(f"invalid backend OpenAPI document {path}: {error}") from error
        if isinstance(document, dict):
            documents.append(document)
    sdk_types = _generated_sdk_types(component_file)
    builtins = {
        "String", "Object", "dynamic", "void", "bool", "int", "double", "num",
        "Void", "List", "Map", "Set", "Future", "DateTime",
    }
    for call in calls:
        matches = 0
        for document in documents:
            paths = document.get("paths")
            operation = paths.get(call.path) if isinstance(paths, dict) else None
            if isinstance(operation, dict) and isinstance(
                operation.get(call.method.lower()), dict
            ):
                matches += 1
        if matches != 1:
            raise ContractError(
                f"business API `{call.call_id}` must match exactly one OpenAPI "
                f"operation: {call.method} {call.path}; found {matches}"
            )
        type_text = f"{call.parameters} {call.response_type}"
        # Backend-owned annotations may append prose after the declared type.
        # Ignore those notes when resolving generated SDK symbols while keeping
        # the original Markdown and parsed values byte-for-byte intact.
        type_text = re.sub(r"（[^）]*）|\([^)]*\)", "", type_text)
        referenced = {
            name
            for name in re.findall(r"\b[A-Z][A-Za-z0-9_]*\b", type_text)
            if name not in builtins
        }
        missing = sorted(referenced.difference(sdk_types))
        if missing:
            raise ContractError(
                f"business API `{call.call_id}` references types missing from "
                "lib/api/gen: " + ", ".join(missing)
            )
    return calls


def validate_legacy_backend_calls(component: object) -> tuple[BackendCall, ...]:
    """Validate historical OpenAPI operation references outside the BFF contract."""
    has_calls_section = "Backend Calls" in component.sections
    has_flow_section = "Backend Call Flow" in component.sections
    if has_calls_section != has_flow_section:
        raise ContractError(
            "Backend Calls and Backend Call Flow must be declared together"
        )
    calls = parse_backend_calls(component)
    flow = component.sections.get("Backend Call Flow", [])
    if not calls:
        if has_calls_section and flow != ["- none"]:
            raise ContractError(
                "Backend Calls and Backend Call Flow must both be `- none` "
                "when no backend call exists"
            )
        return ()
    if not flow or flow == ["- none"]:
        raise ContractError(
            "Backend Call Flow must describe every declared backend call"
        )
    flow_text = "\n".join(flow)
    documents: dict[str, dict[str, Any]] = {}
    for call in calls:
        if f"[{call.call_id}]" not in flow_text:
            raise ContractError(f"Backend Call Flow must reference `[{call.call_id}]`")
        document = documents.get(call.location)
        if document is None:
            document = load_openapi(call, Path(component.component_file))
            documents[call.location] = document
        paths = document.get("paths")
        operation = paths.get(call.path) if isinstance(paths, dict) else None
        if not isinstance(operation, dict) or not isinstance(
            operation.get(call.method.lower()), dict
        ):
            raise ContractError(
                f"backend call `{call.call_id}` operation does not exist in "
                f"{call.location}: {call.method} {call.path}"
            )
    return calls

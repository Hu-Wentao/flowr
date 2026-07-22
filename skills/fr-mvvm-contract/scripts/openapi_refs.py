"""Parse and validate backend OpenAPI operation references from BFF contracts."""

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
MAX_OPENAPI_BYTES = 8 * 1024 * 1024
NETWORK_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class BackendCall:
    """One BFF-to-backend call resolved by OpenAPI document and operation path."""

    call_id: str
    location: str
    method: str
    path: str


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


def validate_backend_calls(component: object) -> tuple[BackendCall, ...]:
    """Validate referenced documents, operations, and the authored call flow."""

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

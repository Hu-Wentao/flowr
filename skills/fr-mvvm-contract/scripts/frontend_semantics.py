"""Parse the versioned frontend endpoint, behavior, and interaction grammar."""

from __future__ import annotations

import re
from dataclasses import dataclass

from contract_core import ContractError

IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
ENDPOINT_LINE = re.compile(r"^-?\s*(GET|POST|PUT|PATCH|DELETE)\s+(\S+)\s*$")
PENDING_ENDPOINT_LINE = re.compile(r"^<PENDING_METHOD>\s+(<PENDING_PATH>)$")
REFERENCE_PAIR = re.compile(rf"^\[({IDENTIFIER})\]\s*,\s*\[({IDENTIFIER})\]\s*$")
ENDPOINT_RECORD = re.compile(rf"^-\s*Endpoint:\s*\[({IDENTIFIER})\]\s*$")
FLOW_RECORD = re.compile(r"^-\s*Flow:\s*([a-z][a-z0-9]*(?:-[a-z0-9]+)*)\s*$")
NAMED_FIELD = re.compile(r"^(?:-\s*)?([A-Za-z][A-Za-z /-]*):\s*(.*)$")
SOURCE_ENTRY = re.compile(rf"^-\s*({IDENTIFIER})\s*<-\s*(.+?)\s*\|\s*(.+)\s*$")
EXACT_REFERENCE = re.compile(rf"^\[({IDENTIFIER})\]$")
USES_REFERENCE = re.compile(rf"^ui-api\s+\[({IDENTIFIER})\]$")
STATE_REFERENCE = re.compile(rf"^\[({IDENTIFIER})\]\.({IDENTIFIER})$")
STATE_GUARD = re.compile(
    rf"^\[({IDENTIFIER})\]\.({IDENTIFIER})\s*==\s*(true|false)$"
)
STATE_MUTATION = re.compile(
    rf"^(\[({IDENTIFIER})\]\.({IDENTIFIER}))\s*(=|<-)\s*(.+)$"
)
TRIGGER = re.compile(
    rf"^(?:startup|reactivation|"
    rf"widget\s+\[({IDENTIFIER})\]\.(tap|change|submit|refresh|retry|select|dismiss)|"
    rf"external\s+([a-z][a-z0-9]*(?:-[a-z0-9]+)*))$"
)
CONCURRENCY_VALUES = {
    "ignore-while-active",
    "latest-wins",
    "queue",
    "allow-parallel",
    "not-applicable",
}
NAVIGATION_VALUES = {"none", "app-on-success"}

QUERY_BEHAVIOR_FIELDS = ("UI Data", "Source", "Loading/Refresh", "Empty/Error")
COMMAND_BEHAVIOR_FIELDS = ("Effect", "Success", "Failure", "Navigation")
INTERACTION_FIELDS = (
    "Trigger",
    "Event",
    "Uses",
    "Guard",
    "Pending State",
    "Success State",
    "Failure State",
    "Concurrency",
    "Navigation",
)


@dataclass(frozen=True)
class FrontendEndpoint:
    """One UI-facing endpoint, identified by its request boundary type."""

    method: str
    path: str
    request_type: str
    response_type: str


@dataclass(frozen=True)
class EndpointBehavior:
    """One endpoint-scoped query or command semantic contract."""

    endpoint: str
    kind: str
    ui_data: str | None = None
    source: str | None = None
    loading_refresh: str | None = None
    empty_error: str | None = None
    effect: str | None = None
    success: str | None = None
    failure: str | None = None
    navigation: str | None = None

    def ordered_fields(self) -> tuple[tuple[str, str], ...]:
        names = (
            QUERY_BEHAVIOR_FIELDS if self.kind == "query" else COMMAND_BEHAVIOR_FIELDS
        )
        values = {
            "UI Data": self.ui_data,
            "Source": self.source,
            "Loading/Refresh": self.loading_refresh,
            "Empty/Error": self.empty_error,
            "Effect": self.effect,
            "Success": self.success,
            "Failure": self.failure,
            "Navigation": self.navigation,
        }
        return tuple((name, values[name] or "") for name in names)


@dataclass(frozen=True)
class RequestFieldSource:
    """Provenance and purpose for one request field."""

    field: str
    source: str
    purpose: str


@dataclass(frozen=True)
class EndpointRequestSources:
    """Request-field provenance scoped to one endpoint identity."""

    endpoint: str
    fields: tuple[RequestFieldSource, ...]


@dataclass(frozen=True)
class StateReference:
    """One `[Type].field` reference in an interaction contract."""

    type_name: str
    field: str


@dataclass(frozen=True)
class StateGuard:
    """One supported boolean guard over frontend state."""

    reference: StateReference
    expected: bool


@dataclass(frozen=True)
class StateMutation:
    """One frontend state assignment or response/error mapping."""

    target: StateReference
    operator: str
    value: str
    source: StateReference | None


@dataclass(frozen=True)
class InteractionFlow:
    """One frontend trigger-to-state interaction flow."""

    flow: str
    trigger: str
    trigger_widget: str | None
    event: str
    uses: str
    endpoint: str | None
    guard: str
    guard_value: StateGuard | None
    pending_state: str
    pending_mutations: tuple[StateMutation, ...]
    success_state: str
    success_mutations: tuple[StateMutation, ...]
    failure_state: str
    failure_mutations: tuple[StateMutation, ...]
    concurrency: str
    navigation: str


@dataclass(frozen=True)
class FrontendSemantics:
    """Typed frontend semantics parsed from a component contract."""

    endpoints: tuple[FrontendEndpoint, ...]
    behaviors: tuple[EndpointBehavior, ...]
    request_sources: tuple[EndpointRequestSources, ...]
    interactions: tuple[InteractionFlow, ...]


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates


def parse_endpoints(lines: list[str]) -> tuple[FrontendEndpoint, ...]:
    """Parse ordered BFF-UI-API blocks and reject ambiguous endpoint identities."""

    if not lines or lines == ["-"]:
        return ()
    endpoints: list[FrontendEndpoint] = []
    index = 0
    while index < len(lines):
        method_path = ENDPOINT_LINE.fullmatch(lines[index])
        pending = PENDING_ENDPOINT_LINE.fullmatch(lines[index])
        if method_path is None and pending is None:
            raise ContractError(
                "BFF-UI-API entries must use `METHOD /path` followed by "
                "`[XxxBffReq], [XxxBffRsp]`; found "
                f"`{lines[index]}`"
            )
        if index + 1 >= len(lines):
            raise ContractError(
                "BFF-UI-API endpoint is missing its request/response pair"
            )
        pair = REFERENCE_PAIR.fullmatch(lines[index + 1])
        if pair is None:
            raise ContractError(
                "BFF-UI-API request/response entries must use exactly "
                "`[XxxBffReq], [XxxBffRsp]`; found "
                f"`{lines[index + 1]}`"
            )
        endpoints.append(
            FrontendEndpoint(
                method=method_path.group(1) if method_path else "PENDING",
                path=method_path.group(2) if method_path else pending.group(1),
                request_type=pair.group(1),
                response_type=pair.group(2),
            )
        )
        index += 2

    duplicate_requests = _duplicates([endpoint.request_type for endpoint in endpoints])
    if duplicate_requests:
        raise ContractError(
            "BFF-UI-API request types are endpoint identities and must be unique: "
            + ", ".join(duplicate_requests)
        )
    return tuple(endpoints)


def _record_fields(
    section: str,
    endpoint: str,
    lines: list[str],
) -> dict[str, str]:
    fields: dict[str, str] = {}
    current: str | None = None
    for line in lines:
        match = NAMED_FIELD.fullmatch(line)
        if match is None:
            if current is not None and not line.startswith("-"):
                fields[current] = f"{fields[current]} {line}".strip()
                continue
            raise ContractError(
                f"{section} endpoint [{endpoint}] fields must use `- Field: value`; "
                f"found `{line}`"
            )
        name, value = match.groups()
        name = name.strip()
        value = value.strip()
        if name in fields:
            raise ContractError(
                f"{section} endpoint [{endpoint}] contains duplicate `{name}`"
            )
        if not value:
            raise ContractError(
                f"{section} endpoint [{endpoint}] `{name}` must not be empty"
            )
        fields[name] = value
        current = name
    return fields


def _endpoint_records(section: str, lines: list[str]) -> list[tuple[str, list[str]]]:
    records: list[tuple[str, list[str]]] = []
    endpoint: str | None = None
    record_lines: list[str] = []
    for line in lines:
        start = ENDPOINT_RECORD.fullmatch(line)
        if start:
            if endpoint is not None:
                records.append((endpoint, record_lines))
            endpoint = start.group(1)
            record_lines = []
            continue
        if endpoint is None:
            raise ContractError(
                f"{section} must begin each record with `- Endpoint: [XxxBffReq]`"
            )
        record_lines.append(line)
    if endpoint is not None:
        records.append((endpoint, record_lines))
    return records


def _require_endpoint_coverage(
    section: str,
    record_endpoints: list[str],
    endpoints: tuple[FrontendEndpoint, ...],
) -> None:
    duplicate = _duplicates(record_endpoints)
    if duplicate:
        raise ContractError(
            f"{section} contains duplicate endpoint records: " + ", ".join(duplicate)
        )
    expected = {endpoint.request_type for endpoint in endpoints}
    actual = set(record_endpoints)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        raise ContractError(
            f"{section} is missing endpoint records: " + ", ".join(missing)
        )
    if unknown:
        raise ContractError(
            f"{section} references unknown endpoint identities: " + ", ".join(unknown)
        )


def parse_behaviors(
    lines: list[str], endpoints: tuple[FrontendEndpoint, ...]
) -> tuple[EndpointBehavior, ...]:
    """Parse exactly one complete query or command behavior per endpoint."""

    if not endpoints:
        if lines:
            raise ContractError("Behaviors must be omitted for API-less BFF contracts")
        return ()
    if not lines:
        raise ContractError("BFF contracts must declare endpoint-scoped `Behaviors:`")
    records = _endpoint_records("Behaviors", lines)
    _require_endpoint_coverage(
        "Behaviors", [endpoint for endpoint, _ in records], endpoints
    )
    parsed: list[EndpointBehavior] = []
    for endpoint, record_lines in records:
        fields = _record_fields("Behaviors", endpoint, record_lines)
        field_names = set(fields)
        query = set(QUERY_BEHAVIOR_FIELDS)
        command = set(COMMAND_BEHAVIOR_FIELDS)
        if field_names == query:
            parsed.append(
                EndpointBehavior(
                    endpoint=endpoint,
                    kind="query",
                    ui_data=fields["UI Data"],
                    source=fields["Source"],
                    loading_refresh=fields["Loading/Refresh"],
                    empty_error=fields["Empty/Error"],
                )
            )
        elif field_names == command:
            parsed.append(
                EndpointBehavior(
                    endpoint=endpoint,
                    kind="command",
                    effect=fields["Effect"],
                    success=fields["Success"],
                    failure=fields["Failure"],
                    navigation=fields["Navigation"],
                )
            )
        else:
            supported = (
                ", ".join(QUERY_BEHAVIOR_FIELDS)
                + " or "
                + ", ".join(COMMAND_BEHAVIOR_FIELDS)
            )
            raise ContractError(
                f"Behaviors endpoint [{endpoint}] must contain exactly the query "
                f"or command field set ({supported}); found "
                + ", ".join(sorted(field_names))
            )
    return tuple(parsed)


def parse_request_sources(
    lines: list[str], endpoints: tuple[FrontendEndpoint, ...]
) -> tuple[EndpointRequestSources, ...]:
    """Parse one endpoint-scoped request provenance record per endpoint."""

    if not endpoints:
        if lines:
            raise ContractError(
                "Request Field Sources must be omitted for API-less BFF contracts"
            )
        return ()
    if not lines:
        raise ContractError(
            "BFF contracts must declare endpoint-scoped `Request Field Sources:`"
        )
    records = _endpoint_records("Request Field Sources", lines)
    _require_endpoint_coverage(
        "Request Field Sources", [endpoint for endpoint, _ in records], endpoints
    )
    parsed: list[EndpointRequestSources] = []
    for endpoint, record_lines in records:
        if record_lines == ["none"] or record_lines == ["- none"]:
            parsed.append(EndpointRequestSources(endpoint=endpoint, fields=()))
            continue
        entries: list[str] = []
        for line in record_lines:
            if line.startswith("-"):
                entries.append(line)
            elif entries:
                entries[-1] = f"{entries[-1]} {line}".strip()
            else:
                raise ContractError(
                    "Request Field Sources entries must begin with `- field <-`; "
                    f"found `{line}` for [{endpoint}]"
                )
        fields: list[RequestFieldSource] = []
        for entry in entries:
            match = SOURCE_ENTRY.fullmatch(entry)
            if match is None:
                raise ContractError(
                    "Request Field Sources entries must use "
                    "`- field <- authoritative source | UI API purpose`; found "
                    f"`{entry}` for [{endpoint}]"
                )
            field, source, purpose = (part.strip() for part in match.groups())
            if not source or not purpose:
                raise ContractError(
                    f"request field `{field}` in [{endpoint}] needs source and purpose"
                )
            fields.append(RequestFieldSource(field, source, purpose))
        duplicate_fields = _duplicates([field.field for field in fields])
        if duplicate_fields:
            raise ContractError(
                f"Request Field Sources endpoint [{endpoint}] contains duplicate "
                "fields: " + ", ".join(duplicate_fields)
            )
        parsed.append(EndpointRequestSources(endpoint, tuple(fields)))
    return tuple(parsed)


def parse_state_reference(value: str) -> StateReference | None:
    """Parse one exact `[Type].field` reference."""

    match = STATE_REFERENCE.fullmatch(value.strip())
    return StateReference(match.group(1), match.group(2)) if match else None


def parse_state_mutations(
    section: str, flow: str, value: str
) -> tuple[StateMutation, ...]:
    """Parse semicolon-separated state writes from one interaction phase."""

    if value == "none":
        return ()
    mutations: list[StateMutation] = []
    for raw in value.split(";"):
        entry = raw.strip()
        match = STATE_MUTATION.fullmatch(entry)
        if match is None:
            raise ContractError(
                f"Interactions Flow `{flow}` {section} must use semicolon-separated "
                "`[Model].field = value` or `[Model].field <- source` entries; "
                f"found `{entry}`"
            )
        target = StateReference(match.group(2), match.group(3))
        operator = match.group(4)
        source_value = match.group(5).strip()
        if not source_value:
            raise ContractError(
                f"Interactions Flow `{flow}` {section} contains an empty state value"
            )
        source = parse_state_reference(source_value)
        if operator == "<-" and source is None and source_value != "error":
            raise ContractError(
                f"Interactions Flow `{flow}` {section} mapping source must be "
                "`[Type].field` or `error`"
            )
        mutations.append(
            StateMutation(
                target=target,
                operator=operator,
                value=source_value,
                source=source,
            )
        )
    duplicate_targets = _duplicates(
        [f"{item.target.type_name}.{item.target.field}" for item in mutations]
    )
    if duplicate_targets:
        raise ContractError(
            f"Interactions Flow `{flow}` {section} writes duplicate targets: "
            + ", ".join(duplicate_targets)
        )
    return tuple(mutations)


def parse_interactions(
    lines: list[str], endpoints: tuple[FrontendEndpoint, ...]
) -> tuple[InteractionFlow, ...]:
    """Parse frontend trigger, Event, state, concurrency, and navigation flows."""

    if lines == ["none"]:
        return ()
    if not lines:
        raise ContractError(
            "BFF contracts must declare `Interactions:`; use `Interactions: none` "
            "only for an approved API-less contract"
        )
    records: list[tuple[str, list[str]]] = []
    flow: str | None = None
    record_lines: list[str] = []
    for line in lines:
        start = FLOW_RECORD.fullmatch(line)
        if start:
            if flow is not None:
                records.append((flow, record_lines))
            flow = start.group(1)
            record_lines = []
            continue
        if flow is None:
            raise ContractError(
                "Interactions must begin each record with `- Flow: kebab-case-id`"
            )
        record_lines.append(line)
    if flow is not None:
        records.append((flow, record_lines))

    duplicate_flows = _duplicates([name for name, _ in records])
    if duplicate_flows:
        raise ContractError(
            "Interactions contains duplicate Flow ids: " + ", ".join(duplicate_flows)
        )
    endpoint_identities = {endpoint.request_type for endpoint in endpoints}
    parsed: list[InteractionFlow] = []
    for name, lines_for_flow in records:
        fields = _record_fields("Interactions", name, lines_for_flow)
        expected = set(INTERACTION_FIELDS)
        actual = set(fields)
        if actual != expected:
            missing = sorted(expected - actual)
            extras = sorted(actual - expected)
            detail: list[str] = []
            if missing:
                detail.append("missing " + ", ".join(missing))
            if extras:
                detail.append("unsupported " + ", ".join(extras))
            raise ContractError(
                f"Interactions Flow `{name}` must contain exactly the fixed field "
                "set: " + "; ".join(detail)
            )
        event = EXACT_REFERENCE.fullmatch(fields["Event"])
        if event is None:
            raise ContractError(
                f"Interactions Flow `{name}` Event must be `[XxxEvent]`"
            )
        trigger = TRIGGER.fullmatch(fields["Trigger"])
        if trigger is None:
            raise ContractError(
                f"Interactions Flow `{name}` Trigger must be `startup`, "
                "`reactivation`, `widget [Widget].<action>`, or "
                "`external stable-id`"
            )
        uses_value = fields["Uses"]
        uses_endpoint = USES_REFERENCE.fullmatch(uses_value)
        if uses_value == "local":
            endpoint = None
        elif uses_endpoint:
            endpoint = uses_endpoint.group(1)
            if endpoint not in endpoint_identities:
                raise ContractError(
                    f"Interactions Flow `{name}` Uses references unknown endpoint "
                    f"identity [{endpoint}]"
                )
        else:
            raise ContractError(
                f"Interactions Flow `{name}` Uses must be `local` or "
                "`ui-api [XxxBffReq]`"
            )
        guard_value: StateGuard | None
        if fields["Guard"] == "none":
            guard_value = None
        else:
            guard_match = STATE_GUARD.fullmatch(fields["Guard"])
            if guard_match is None:
                raise ContractError(
                    f"Interactions Flow `{name}` Guard must be `none` or "
                    "`[Model].field == true|false`"
                )
            guard_value = StateGuard(
                StateReference(guard_match.group(1), guard_match.group(2)),
                guard_match.group(3) == "true",
            )
        concurrency = fields["Concurrency"]
        if concurrency not in CONCURRENCY_VALUES:
            raise ContractError(
                f"Interactions Flow `{name}` Concurrency must be one of: "
                + ", ".join(sorted(CONCURRENCY_VALUES))
            )
        if endpoint is not None and concurrency == "not-applicable":
            raise ContractError(
                f"Interactions Flow `{name}` uses a UI API and cannot declare "
                "`not-applicable` concurrency"
            )
        navigation = fields["Navigation"]
        if navigation not in NAVIGATION_VALUES:
            raise ContractError(
                f"Interactions Flow `{name}` Navigation must be `none` or "
                "`app-on-success`"
            )
        pending_mutations = parse_state_mutations(
            "Pending State", name, fields["Pending State"]
        )
        success_mutations = parse_state_mutations(
            "Success State", name, fields["Success State"]
        )
        failure_mutations = parse_state_mutations(
            "Failure State", name, fields["Failure State"]
        )
        if endpoint is not None and not (
            pending_mutations and success_mutations and failure_mutations
        ):
            raise ContractError(
                f"Interactions Flow `{name}` uses a UI API and must declare "
                "Pending, Success, and Failure state mutations"
            )
        parsed.append(
            InteractionFlow(
                flow=name,
                trigger=fields["Trigger"],
                trigger_widget=trigger.group(1),
                event=event.group(1),
                uses=uses_value,
                endpoint=endpoint,
                guard=fields["Guard"],
                guard_value=guard_value,
                pending_state=fields["Pending State"],
                pending_mutations=pending_mutations,
                success_state=fields["Success State"],
                success_mutations=success_mutations,
                failure_state=fields["Failure State"],
                failure_mutations=failure_mutations,
                concurrency=concurrency,
                navigation=navigation,
            )
        )
    duplicate_events = _duplicates([flow.event for flow in parsed])
    if duplicate_events:
        raise ContractError(
            "Interactions Events must identify exactly one Flow: "
            + ", ".join(duplicate_events)
        )
    uncovered = sorted(
        endpoint_identities
        - {flow.endpoint for flow in parsed if flow.endpoint is not None}
    )
    if uncovered:
        raise ContractError(
            "Interactions must cover every UI endpoint: " + ", ".join(uncovered)
        )
    return tuple(parsed)


def parse_frontend_semantics(
    sections: dict[str, list[str]],
) -> FrontendSemantics:
    """Parse the breaking v9 frontend grammar from contract doc sections."""

    if "Behavior" in sections:
        raise ContractError(
            "singular `Behavior:` is obsolete; migrate to endpoint-scoped `Behaviors:`"
        )
    endpoints = parse_endpoints(sections.get("BFF-UI-API", []))
    api_less = sections.get("BFF-UI-API") == ["-"]
    behaviors = parse_behaviors(sections.get("Behaviors", []), endpoints)
    request_sources = parse_request_sources(
        sections.get("Request Field Sources", []), endpoints
    )
    interaction_lines = sections.get("Interactions", [])
    if api_less and not interaction_lines:
        raise ContractError(
            "API-less BFF contracts must explicitly declare `Interactions: none` "
            "or structured local interaction flows"
        )
    if endpoints and interaction_lines == ["none"]:
        raise ContractError(
            "BFF contracts with UI endpoints must declare structured interaction flows"
        )
    interactions = parse_interactions(interaction_lines, endpoints)
    if api_less and any(flow.endpoint is not None for flow in interactions):
        raise ContractError("API-less BFF contracts may declare only local interactions")
    return FrontendSemantics(
        endpoints=endpoints,
        behaviors=behaviors,
        request_sources=request_sources,
        interactions=interactions,
    )

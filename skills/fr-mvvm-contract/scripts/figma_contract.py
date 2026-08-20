"""Parse and validate Figma ownership declarations in component contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, parse_qsl, unquote, urlencode, urlparse, urlunparse

from contract_core import ContractError

NODE_ID = re.compile(r"[0-9]+(?::[0-9]+)*")
ENTRY = re.compile(r"^-\s*([A-Za-z][A-Za-z0-9_-]*)\s*\|\s*(\S+)\s*\|\s*(.+)$")
PRIMARY_FRAME = re.compile(r"^-\s*Frame:\s*(.+)$")
PRIMARY_PAGE_TITLE = re.compile(r"^-\s*Page Title:\s*(.+)$")
PRIMARY_NODE = re.compile(r"^-\s*Node:\s*(\S+)$")


@dataclass(frozen=True)
class FigmaNodeDeclaration:
    name: str
    url: str
    file_key: str
    node_id: str
    role: str
    evidence: str
    page_title: str | None = None


@dataclass(frozen=True)
class FigmaContractNodes:
    primary: FigmaNodeDeclaration
    states: tuple[FigmaNodeDeclaration, ...]
    references: tuple[FigmaNodeDeclaration, ...]
    excluded: tuple[FigmaNodeDeclaration, ...]

    @property
    def bindable(self) -> tuple[FigmaNodeDeclaration, ...]:
        return (self.primary, *self.states)

    @property
    def all(self) -> tuple[FigmaNodeDeclaration, ...]:
        return (*self.bindable, *self.references, *self.excluded)


def normalize_node_id(value: str) -> str:
    node_id = value.replace("-", ":")
    if not NODE_ID.fullmatch(node_id):
        raise ContractError(f"invalid Figma node-id: {value}")
    return node_id


def parse_figma_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (
        hostname == "figma.com" or hostname.endswith(".figma.com")
    ):
        raise ContractError("Figma URL must be an https://figma.com URL")

    parts = [unquote(part) for part in parsed.path.split("/") if part]
    if len(parts) < 2 or parts[0] not in {"design", "file"}:
        raise ContractError("Figma URL must target a design or file")
    file_key = parts[1]
    if len(parts) >= 4 and parts[2] == "branch":
        file_key = parts[3]

    values = parse_qs(parsed.query).get("node-id", [])
    if len(values) != 1 or not values[0]:
        raise ContractError("Figma URL must contain exactly one concrete node-id")
    return file_key, normalize_node_id(values[0])


def figma_url_for_node(primary_url: str, node_id: str) -> str:
    """Build a developer-facing Frame URL from the primary design URL."""

    normalized = normalize_node_id(node_id)
    parsed = urlparse(primary_url)
    query: list[tuple[str, str]] = []
    replaced = False
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key == "node-id":
            if not replaced:
                query.append((key, normalized.replace(":", "-")))
                replaced = True
            continue
        query.append((key, value))
    if not replaced:
        raise ContractError("primary Figma URL must contain a concrete node-id")
    return urlunparse(parsed._replace(query=urlencode(query)))


def _primary(lines: list[str]) -> FigmaNodeDeclaration:
    if len(lines) == 1 and lines[0].strip():
        value = lines[0].strip()
        file_key, node_id = parse_figma_url(value)
        return FigmaNodeDeclaration(
            name="primary",
            url=value,
            file_key=file_key,
            node_id=node_id,
            role="primary",
            evidence="authoritative primary screen",
        )
    if len(lines) not in {2, 3}:
        raise ContractError(
            "Figma must declare one Frame and one Node; current contracts add "
            "Page Title between them"
        )
    frame_match = PRIMARY_FRAME.fullmatch(lines[0])
    page_title_match = (
        PRIMARY_PAGE_TITLE.fullmatch(lines[1]) if len(lines) == 3 else None
    )
    node_match = PRIMARY_NODE.fullmatch(lines[-1])
    if (
        not frame_match
        or not node_match
        or not frame_match.group(1).strip()
        or (
            len(lines) == 3
            and (
                page_title_match is None
                or not page_title_match.group(1).strip()
            )
        )
    ):
        raise ContractError(
            "Figma must use `- Frame: <actual-frame-name>`, optionally "
            "`- Page Title: <visible-page-title>`, then "
            "`- Node: https://figma.com/...node-id=...`"
        )
    value = node_match.group(1)
    file_key, node_id = parse_figma_url(value)
    return FigmaNodeDeclaration(
        name=frame_match.group(1).strip(),
        url=value,
        file_key=file_key,
        node_id=node_id,
        role="primary",
        evidence="authoritative primary screen",
        page_title=(
            page_title_match.group(1).strip()
            if page_title_match is not None
            else None
        ),
    )


def _entries(
    sections: dict[str, list[str]], section: str, role: str
) -> tuple[FigmaNodeDeclaration, ...]:
    result: list[FigmaNodeDeclaration] = []
    for line in sections.get(section, []):
        match = ENTRY.fullmatch(line)
        if not match:
            raise ContractError(
                f"{section} entries must use "
                "`- name | https://figma.com/...node-id=... | evidence`"
            )
        name, url, evidence = (part.strip() for part in match.groups())
        if not evidence:
            raise ContractError(f"{section} entry `{name}` must explain its evidence")
        file_key, node_id = parse_figma_url(url)
        result.append(
            FigmaNodeDeclaration(
                name=name,
                url=url,
                file_key=file_key,
                node_id=node_id,
                role=role,
                evidence=evidence,
            )
        )
    return tuple(result)


def _states(
    sections: dict[str, list[str]], primary: FigmaNodeDeclaration
) -> tuple[FigmaNodeDeclaration, ...]:
    result: list[FigmaNodeDeclaration] = []
    for line in sections.get("Figma States", []):
        match = ENTRY.fullmatch(line)
        if not match:
            raise ContractError(
                "Figma States entries must use `- stateName | <node-id> | evidence`"
            )
        name, value, evidence = (part.strip() for part in match.groups())
        if not evidence:
            raise ContractError(
                f"Figma States entry `{name}` must explain its evidence"
            )

        # Keep existing contracts readable while all new and modified contracts
        # use only the compact node-id declared by the skill.
        if value.startswith("https://"):
            file_key, node_id = parse_figma_url(value)
            if file_key != primary.file_key:
                raise ContractError("all Figma declarations must target the same file")
            url = value
        else:
            node_id = normalize_node_id(value)
            file_key = primary.file_key
            url = figma_url_for_node(primary.url, node_id)
        result.append(
            FigmaNodeDeclaration(
                name=name,
                url=url,
                file_key=file_key,
                node_id=node_id,
                role="state",
                evidence=evidence,
            )
        )
    return tuple(result)


def parse_figma_contract_nodes(
    sections: dict[str, list[str]],
) -> FigmaContractNodes:
    primary = _primary(sections.get("Figma", []))
    nodes = FigmaContractNodes(
        primary=primary,
        states=_states(sections, primary),
        references=_entries(sections, "Figma References", "reference"),
        excluded=_entries(sections, "Figma Excluded", "excluded"),
    )
    file_keys = {node.file_key for node in nodes.all}
    if len(file_keys) != 1:
        raise ContractError("all Figma declarations must target the same file")
    node_ids = [node.node_id for node in nodes.all]
    duplicates = sorted(
        node_id for node_id in set(node_ids) if node_ids.count(node_id) > 1
    )
    if duplicates:
        raise ContractError(
            "a Figma node may appear in exactly one ownership category: "
            + ", ".join(duplicates)
        )
    names = [node.name for node in nodes.all]
    duplicate_names = sorted(name for name in set(names) if names.count(name) > 1)
    if duplicate_names:
        raise ContractError(
            "Figma declaration names must be unique: " + ", ".join(duplicate_names)
        )
    return nodes

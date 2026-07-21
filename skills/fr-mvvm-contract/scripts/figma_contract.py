"""Parse and validate Figma ownership declarations in component contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote, urlparse

from contract_core import ContractError


NODE_ID = re.compile(r"[0-9]+(?::[0-9]+)*")
ENTRY = re.compile(r"^-\s*([A-Za-z][A-Za-z0-9_-]*)\s*\|\s*(\S+)\s*\|\s*(.+)$")


@dataclass(frozen=True)
class FigmaNodeDeclaration:
    name: str
    url: str
    file_key: str
    node_id: str
    role: str
    evidence: str


@dataclass(frozen=True)
class FigmaContractNodes:
    primary: FigmaNodeDeclaration
    contract_card_node_id: str | None
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


def _primary(lines: list[str]) -> FigmaNodeDeclaration:
    if not lines:
        raise ContractError("component contract must declare a Figma node URL")
    value = " ".join(lines).strip()
    if not value or len(value.split()) != 1:
        raise ContractError("Figma must contain exactly one node-specific URL")
    file_key, node_id = parse_figma_url(value)
    return FigmaNodeDeclaration(
        name="primary",
        url=value,
        file_key=file_key,
        node_id=node_id,
        role="primary",
        evidence="authoritative primary screen",
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
                "`- stateName | https://figma.com/...node-id=... | evidence`"
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


def _contract_card_node_id(lines: list[str]) -> str | None:
    if not lines:
        return None
    value = " ".join(lines).strip()
    if not value or len(value.split()) != 1:
        raise ContractError("Figma Contract Card must contain exactly one node-id")
    return normalize_node_id(value)


def parse_figma_contract_nodes(
    sections: dict[str, list[str]],
) -> FigmaContractNodes:
    nodes = FigmaContractNodes(
        primary=_primary(sections.get("Figma", [])),
        contract_card_node_id=_contract_card_node_id(
            sections.get("Figma Contract Card", [])
        ),
        states=_entries(sections, "Figma States", "state"),
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
    if (
        nodes.contract_card_node_id is not None
        and nodes.contract_card_node_id in node_ids
    ):
        raise ContractError(
            "Figma Contract Card must identify the yellow card, not a Figma page, "
            "state, reference, or excluded node"
        )
    names = [node.name for node in nodes.all]
    duplicate_names = sorted(name for name in set(names) if names.count(name) > 1)
    if duplicate_names:
        raise ContractError(
            "Figma declaration names must be unique: " + ", ".join(duplicate_names)
        )
    return nodes

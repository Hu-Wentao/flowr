"""Resolve project-wide Figma releases against one component contract."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from contract_core import ContractError, doc_sections
from figma_contract import FigmaContractNodes, parse_figma_contract_nodes
from resolve import ResolveError, load_config

CONFIG_SCHEMA = "fr-mvvm-contract.config.v1"
RELEASE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
FILE_KEY = re.compile(r"[A-Za-z0-9_-]+")
OVERRIDE_ENTRY = re.compile(r"^-\s*(Release|Reason|Review After):\s*(.+)$")


class FigmaReleaseError(ValueError):
    """Raised when release configuration or a contract override is invalid."""


@dataclass(frozen=True)
class FigmaRelease:
    """One configured immutable Figma release."""

    name: str
    file_key: str
    status: str


@dataclass(frozen=True)
class FigmaReleaseCatalog:
    """Project-wide Figma release selection."""

    active_release: str
    enforcement: str
    releases: tuple[FigmaRelease, ...]

    def by_name(self) -> dict[str, FigmaRelease]:
        return {release.name: release for release in self.releases}

    def by_file_key(self) -> dict[str, FigmaRelease]:
        return {release.file_key: release for release in self.releases}


@dataclass(frozen=True)
class FigmaReleaseOverride:
    """An intentional page-level exception to the active release."""

    release: str
    reason: str
    review_after: str | None


@dataclass(frozen=True)
class FigmaReleaseResolution:
    """Resolved release status for one concrete contract binding."""

    status: str
    current_release: str | None
    current_file_key: str
    active_release: str
    active_file_key: str
    enforcement: str
    migration_required: bool
    action: str
    override: FigmaReleaseOverride | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FigmaReleaseError(f"{field} must be a mapping")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FigmaReleaseError(f"{field} must be a non-empty string")
    return value.strip()


def parse_figma_release_catalog(
    config: dict[str, Any],
) -> FigmaReleaseCatalog | None:
    """Parse optional global Figma release configuration."""

    raw_figma = config.get("figma")
    if raw_figma is None:
        return None
    figma = _mapping(raw_figma, "figma")
    unknown = set(figma) - {"active_release", "enforcement", "releases"}
    if unknown:
        raise FigmaReleaseError(
            "figma contains unsupported fields: " + ", ".join(sorted(unknown))
        )

    active_release = _string(figma.get("active_release"), "figma.active_release")
    enforcement = _string(figma.get("enforcement", "gradual"), "figma.enforcement")
    if enforcement not in {"gradual", "strict"}:
        raise FigmaReleaseError("figma.enforcement must be gradual or strict")

    raw_releases = _mapping(figma.get("releases"), "figma.releases")
    if not raw_releases:
        raise FigmaReleaseError("figma.releases must not be empty")
    releases: list[FigmaRelease] = []
    file_keys: set[str] = set()
    for raw_name, raw_release in raw_releases.items():
        name = _string(raw_name, "figma.releases key")
        if not RELEASE_NAME.fullmatch(name):
            raise FigmaReleaseError(
                f"figma release name {name!r} contains unsupported characters"
            )
        field = f"figma.releases.{name}"
        release = _mapping(raw_release, field)
        unknown_release = set(release) - {"file_key", "status"}
        if unknown_release:
            raise FigmaReleaseError(
                f"{field} contains unsupported fields: "
                + ", ".join(sorted(unknown_release))
            )
        file_key = _string(release.get("file_key"), f"{field}.file_key")
        if not FILE_KEY.fullmatch(file_key):
            raise FigmaReleaseError(f"{field}.file_key is invalid")
        if file_key in file_keys:
            raise FigmaReleaseError(f"figma releases reuse file_key {file_key!r}")
        file_keys.add(file_key)
        status = _string(release.get("status"), f"{field}.status")
        if status not in {"active", "candidate", "archived"}:
            raise FigmaReleaseError(
                f"{field}.status must be active, candidate, or archived"
            )
        releases.append(FigmaRelease(name, file_key, status))

    by_name = {release.name: release for release in releases}
    if active_release not in by_name:
        raise FigmaReleaseError(
            f"figma.active_release {active_release!r} is not configured"
        )
    active_names = [release.name for release in releases if release.status == "active"]
    if active_names != [active_release]:
        raise FigmaReleaseError("exactly figma.active_release must have status active")
    return FigmaReleaseCatalog(
        active_release=active_release,
        enforcement=enforcement,
        releases=tuple(releases),
    )


def load_figma_release_catalog(project_root: Path) -> FigmaReleaseCatalog | None:
    """Load the configured release catalog from one project."""

    config_path = (
        project_root.resolve()
        / ".agents"
        / "skills-config"
        / "fr-mvvm-contract"
        / "config.yaml"
    )
    try:
        config, _ = load_config(config_path)
    except ResolveError as exc:
        raise FigmaReleaseError(str(exc)) from exc
    if not config:
        return None
    if config.get("schema") != CONFIG_SCHEMA:
        raise FigmaReleaseError(f"config.yaml schema must be {CONFIG_SCHEMA}")
    return parse_figma_release_catalog(config)


def parse_figma_release_override(
    sections: dict[str, list[str]],
) -> FigmaReleaseOverride | None:
    """Parse an explicit old-release exception from one contract."""

    lines = sections.get("Figma Release Override")
    if lines is None:
        return None
    values: dict[str, str] = {}
    for line in lines:
        match = OVERRIDE_ENTRY.fullmatch(line)
        if not match:
            raise FigmaReleaseError(
                "Figma Release Override must use `- Release: <name>`, "
                "`- Reason: <reason>`, and optional `- Review After: YYYY-MM-DD`"
            )
        key, value = match.groups()
        if key in values:
            raise FigmaReleaseError(f"Figma Release Override repeats {key}")
        values[key] = value.strip()
    unknown = set(values) - {"Release", "Reason", "Review After"}
    if unknown:
        raise FigmaReleaseError("Figma Release Override contains unsupported fields")
    release = _string(values.get("Release"), "Figma Release Override.Release")
    reason = _string(values.get("Reason"), "Figma Release Override.Reason")
    review_after = values.get("Review After")
    if review_after is not None:
        try:
            parsed = date.fromisoformat(review_after)
        except ValueError as exc:
            raise FigmaReleaseError(
                "Figma Release Override.Review After must be YYYY-MM-DD"
            ) from exc
        if parsed.isoformat() != review_after:
            raise FigmaReleaseError(
                "Figma Release Override.Review After must be YYYY-MM-DD"
            )
    return FigmaReleaseOverride(release, reason, review_after)


def resolve_figma_release(
    catalog: FigmaReleaseCatalog,
    nodes: FigmaContractNodes,
    sections: dict[str, list[str]],
) -> FigmaReleaseResolution:
    """Compare one concrete contract binding with the active release."""

    current_file_key = nodes.primary.file_key
    active = catalog.by_name()[catalog.active_release]
    current = catalog.by_file_key().get(current_file_key)
    override = parse_figma_release_override(sections)

    if current is None:
        if override is not None:
            raise FigmaReleaseError(
                "Figma Release Override cannot authorize an unknown file_key"
            )
        return FigmaReleaseResolution(
            status="unknown",
            current_release=None,
            current_file_key=current_file_key,
            active_release=active.name,
            active_file_key=active.file_key,
            enforcement=catalog.enforcement,
            migration_required=False,
            action="block-and-register-release",
            override=None,
        )

    if current.name == active.name:
        if override is not None:
            raise FigmaReleaseError(
                "Figma Release Override is invalid on the active release"
            )
        return FigmaReleaseResolution(
            status="current",
            current_release=current.name,
            current_file_key=current.file_key,
            active_release=active.name,
            active_file_key=active.file_key,
            enforcement=catalog.enforcement,
            migration_required=False,
            action="use-current-binding",
            override=None,
        )

    if current.status == "candidate":
        if override is not None:
            raise FigmaReleaseError(
                "Figma Release Override cannot authorize a candidate release"
            )
        return FigmaReleaseResolution(
            status="candidate",
            current_release=current.name,
            current_file_key=current.file_key,
            active_release=active.name,
            active_file_key=active.file_key,
            enforcement=catalog.enforcement,
            migration_required=False,
            action="block-unapproved-release",
            override=None,
        )

    if override is not None:
        if override.release != current.name:
            raise FigmaReleaseError(
                "Figma Release Override.Release must match the contract file_key"
            )
        return FigmaReleaseResolution(
            status="pinned",
            current_release=current.name,
            current_file_key=current.file_key,
            active_release=active.name,
            active_file_key=active.file_key,
            enforcement=catalog.enforcement,
            migration_required=False,
            action="keep-explicit-old-release",
            override=override,
        )

    return FigmaReleaseResolution(
        status="stale",
        current_release=current.name,
        current_file_key=current.file_key,
        active_release=active.name,
        active_file_key=active.file_key,
        enforcement=catalog.enforcement,
        migration_required=True,
        action="inspect-active-release-and-migrate-touched-contract",
        override=None,
    )


def resolve_contract_figma_release(
    project_root: Path,
    contract_file: Path,
) -> FigmaReleaseResolution | None:
    """Resolve one repository-contained contract against project config."""

    root = project_root.resolve()
    candidate = contract_file if contract_file.is_absolute() else root / contract_file
    contract = candidate.resolve()
    try:
        contract.relative_to(root)
    except ValueError as exc:
        raise FigmaReleaseError("contract-file must be inside project-root") from exc
    if not contract.is_file() or not contract.name.endswith(".c.dart"):
        raise FigmaReleaseError("contract-file must be an existing .c.dart contract")
    catalog = load_figma_release_catalog(root)
    if catalog is None:
        return None
    sections = doc_sections(contract.read_text(encoding="utf-8"))
    try:
        nodes = parse_figma_contract_nodes(sections)
    except ContractError as exc:
        raise FigmaReleaseError(str(exc)) from exc
    return resolve_figma_release(catalog, nodes, sections)

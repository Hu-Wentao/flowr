"""Shared contract-first component naming and validation primitives."""

from __future__ import annotations

import re
from pathlib import Path


class ContractError(ValueError):
    """Raised when source files do not follow the contract layout."""


IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"


def require_file(path: Path, description: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise ContractError(f"{description} does not exist: {path}") from error


def find_package_pubspec(component_file: Path) -> Path:
    """Return the nearest package manifest that owns a component library."""

    for directory in (component_file.parent, *component_file.parents):
        candidate = directory / "pubspec.yaml"
        if candidate.is_file():
            return candidate
    raise ContractError(f"no pubspec.yaml owns {component_file}")


def has_direct_dependency(pubspec: Path, dependency: str, *, section: str) -> bool:
    """Check one directly declared dependency in a pubspec section."""

    in_section = False
    for line in pubspec.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[:1].isspace():
            in_section = bool(re.match(rf"{section}\s*:\s*(?:#.*)?$", line))
            continue
        if in_section and re.match(rf"\s+{re.escape(dependency)}\s*:", line):
            return True
    return False


def class_names(source: str) -> list[str]:
    return re.findall(rf"\bclass\s+({IDENTIFIER})\b", source)


def doc_sections(source: str) -> dict[str, list[str]]:
    """Parse stable `/// Label:` sections without treating Dart as Markdown."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in source.splitlines():
        match = re.match(r"\s*///\s*([A-Za-z][A-Za-z -]*):\s*(.*)$", raw)
        if match:
            current = match.group(1).strip()
            sections[current] = (
                [match.group(2).strip()] if match.group(2).strip() else []
            )
            continue
        continuation = re.match(r"\s*///\s*(.*)$", raw)
        if continuation and current is not None:
            value = continuation.group(1).strip()
            if value:
                sections[current].append(value)
        elif raw.strip():
            current = None
    return sections


def bracket_refs(lines: list[str]) -> list[str]:
    return re.findall(rf"\[({IDENTIFIER})\]", "\n".join(lines))


def relative_import_uri(source: str, sibling_name: str) -> bool:
    return bool(
        re.search(rf"\bimport\s+['\"]{re.escape(sibling_name)}['\"]\s*;", source)
    )

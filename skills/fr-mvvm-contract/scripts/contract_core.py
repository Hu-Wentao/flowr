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
            sections[current] = [match.group(2).strip()] if match.group(2).strip() else []
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

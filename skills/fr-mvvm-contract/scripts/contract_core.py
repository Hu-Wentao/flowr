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


def _section_lines(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in lines:
        if not raw.strip():
            current = None
            continue
        match = re.match(r"\s*([A-Za-z][A-Za-z -]*):\s*(.*)$", raw)
        if match:
            current = match.group(1).strip()
            sections[current] = (
                [match.group(2).strip()] if match.group(2).strip() else []
            )
            continue
        if current is not None:
            value = raw.strip()
            if value:
                sections[current].append(value)
    return sections


def block_sections(source: str) -> dict[str, list[str]]:
    """Parse `Label:` sections from ordinary `/* ... */` comment blocks."""

    lines: list[str] = []
    for comment in re.findall(r"/\*(.*?)\*/", source, re.DOTALL):
        for raw in comment.splitlines():
            # Accept conventional leading stars when reading handwritten blocks,
            # while generated contracts use the simpler unprefixed form.
            lines.append(re.sub(r"^\s*\* ?", "", raw).rstrip())
        lines.append("")
    return _section_lines(lines)


def doc_sections(source: str) -> dict[str, list[str]]:
    """Parse stable `/// Label:` sections used by `.page.dart` adapters."""

    lines = []
    for raw in source.splitlines():
        match = re.match(r"\s*///\s?(.*)$", raw)
        lines.append(match.group(1) if match else "")
    return _section_lines(lines)


def has_disallowed_contract_comment(source: str) -> bool:
    """Detect `//`, `///`, or `/**` comments outside Dart strings."""

    quote: str | None = None
    in_block = False
    escaped = False
    index = 0
    while index < len(source):
        pair = source[index : index + 2]
        char = source[index]
        if in_block:
            if pair == "*/":
                in_block = False
                index += 2
                continue
        elif quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif source.startswith("/**", index):
            return True
        elif pair == "/*":
            in_block = True
            index += 2
            continue
        elif pair == "//":
            return True
        elif char in {"'", '"'}:
            quote = char
        index += 1
    return False


def bracket_refs(lines: list[str]) -> list[str]:
    return re.findall(rf"\[({IDENTIFIER})\]", "\n".join(lines))


def relative_import_uri(source: str, sibling_name: str) -> bool:
    return bool(
        re.search(rf"\bimport\s+['\"]{re.escape(sibling_name)}['\"]\s*;", source)
    )

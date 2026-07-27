#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Scan, normalize, and verify Figma SVG assets for Flutter.

Normalization is intentionally narrow: it resolves only CSS color variables
whose fallback is an explicit hex color. Geometry and aspect-ratio findings are
reported for visual review and are never rewritten automatically.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

SVG_RECEIPT_SCHEMA = "fr-mvvm-contract.figma-svg-normalization.v1"
SAFE_COLOR_VAR_RE = re.compile(
    r"(?P<prefix>(?:fill|stroke)\s*(?:=|:)\s*[\"']?)"
    r"var\(\s*--[^,()]+,\s*(?P<color>#[0-9A-Fa-f]{3,8})\s*\)"
    r"(?P<suffix>[\"']?)",
    re.IGNORECASE,
)
ANY_VAR_RE = re.compile(r"var\(", re.IGNORECASE)
NUMBER_RE = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:px)?$")
RISKY_TAGS = {"clipPath", "filter", "mask", "pattern"}
NORMALIZATION_RE = re.compile(r"^resolve-css-color-fallbacks:[1-9][0-9]*$")


class SvgPipelineError(ValueError):
    """Raised when an SVG or normalization receipt is invalid or unsafe."""


@dataclass(frozen=True)
class Finding:
    """One stable SVG diagnostic."""

    code: str
    severity: str
    detail: str


@dataclass(frozen=True)
class SvgInspection:
    """Inspection result for one source file."""

    path: str
    source_export_sha256: str
    safe_color_replacements: int
    findings: tuple[Finding, ...]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SvgPipelineError(f"{field} must be an object")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise SvgPipelineError(f"{field} must be an array")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise SvgPipelineError(f"{field} must be a non-empty string")
    return value


def _hash(value: Any, field: str) -> str:
    raw = _string(value, field)
    if len(raw) != 64 or any(char not in "0123456789abcdef" for char in raw):
        raise SvgPipelineError(f"{field} must be lowercase SHA-256")
    return raw


def _relative(value: Any, field: str) -> str:
    raw = _string(value, field)
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or "\\" in raw:
        raise SvgPipelineError(f"{field} must be a safe repository-relative path")
    return raw


def _contained(root: Path, candidate: Path, field: str) -> Path:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise SvgPipelineError(f"{field} escapes the project root") from exc
    return resolved_candidate


def _rooted(root: Path, candidate: Path, field: str) -> Path:
    path = candidate if candidate.is_absolute() else root / candidate
    return _contained(root, path, field)


def _project_path(root: Path, value: Any, field: str) -> Path:
    return _contained(root, root / _relative(value, field), field)


def iter_files(patterns: list[str]) -> list[Path]:
    """Expand patterns into stable unique files."""

    files: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        matches = [Path(value) for value in sorted(glob.glob(pattern, recursive=True))]
        if not matches:
            candidate = Path(pattern)
            matches = [candidate] if candidate.is_file() else []
        for candidate in matches:
            resolved = candidate.resolve()
            if candidate.is_file() and resolved not in seen:
                seen.add(resolved)
                files.append(candidate)
    return files


def _number(value: str | None) -> float | None:
    if value is None or not NUMBER_RE.fullmatch(value.strip()):
        return None
    return float(value.strip().removesuffix("px"))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def inspect_svg(path: Path) -> SvgInspection:
    """Inspect one SVG without modifying it."""

    data = path.read_bytes()
    findings: list[Finding] = []
    if path.suffix.lower() != ".svg":
        findings.append(
            Finding("extension_mismatch", "error", "file extension is not .svg")
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return SvgInspection(
            path=str(path),
            source_export_sha256=_sha256(data),
            safe_color_replacements=0,
            findings=(
                Finding("invalid_utf8", "error", "SVG must be UTF-8 text"),
            ),
        )

    safe_count = len(SAFE_COLOR_VAR_RE.findall(text))
    if safe_count:
        findings.append(
            Finding(
                "normalizable_css_color",
                "warning",
                f"{safe_count} CSS color variable fallback(s) can be normalized",
            )
        )
    unresolved_count = len(ANY_VAR_RE.findall(text)) - safe_count
    if unresolved_count:
        findings.append(
            Finding(
                "unresolved_css_variable",
                "error",
                f"{unresolved_count} var(...) expression(s) have no safe color rewrite",
            )
        )

    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        findings.append(Finding("invalid_xml", "error", str(exc)))
        return SvgInspection(
            path=str(path),
            source_export_sha256=_sha256(data),
            safe_color_replacements=safe_count,
            findings=tuple(findings),
        )
    if _local_name(root.tag) != "svg":
        findings.append(
            Finding("content_mismatch", "error", "XML root element is not <svg>")
        )
        return SvgInspection(
            path=str(path),
            source_export_sha256=_sha256(data),
            safe_color_replacements=safe_count,
            findings=tuple(findings),
        )

    view_box = root.attrib.get("viewBox")
    parsed_view_box: tuple[float, float, float, float] | None = None
    if view_box is None:
        findings.append(Finding("missing_view_box", "error", "viewBox is required"))
    else:
        try:
            values = tuple(float(value) for value in view_box.replace(",", " ").split())
        except ValueError:
            values = ()
        if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
            findings.append(
                Finding("invalid_view_box", "error", f"invalid viewBox: {view_box}")
            )
        else:
            parsed_view_box = values  # type: ignore[assignment]

    width = _number(root.attrib.get("width"))
    height = _number(root.attrib.get("height"))
    if width is None or height is None or width <= 0 or height <= 0:
        findings.append(
            Finding(
                "missing_or_non_numeric_dimensions",
                "warning",
                "numeric width and height improve Flutter asset traceability",
            )
        )
    elif parsed_view_box is not None:
        rendered_ratio = width / height
        view_box_ratio = parsed_view_box[2] / parsed_view_box[3]
        if abs(rendered_ratio - view_box_ratio) / view_box_ratio > 0.005:
            findings.append(
                Finding(
                    "aspect_ratio_mismatch",
                    "warning",
                    "width/height ratio differs from viewBox ratio",
                )
            )

    if root.attrib.get("preserveAspectRatio", "").strip().lower() == "none":
        findings.append(
            Finding(
                "stretched_aspect_ratio",
                "warning",
                'preserveAspectRatio="none" requires explicit visual review',
            )
        )
    if root.attrib.get("overflow", "").strip().lower() == "visible":
        findings.append(
            Finding(
                "visible_overflow",
                "warning",
                "overflow=visible may hide clipping or blank-bound differences",
            )
        )

    tags = {_local_name(element.tag) for element in root.iter()}
    risky = sorted(tags.intersection(RISKY_TAGS))
    if risky:
        findings.append(
            Finding(
                "complex_geometry",
                "warning",
                "manual render review required for: " + ",".join(risky),
            )
        )
    if any("transform" in element.attrib for element in root.iter()):
        findings.append(
            Finding(
                "transformed_geometry",
                "warning",
                "transforms require rendered bounds review",
            )
        )

    return SvgInspection(
        path=str(path),
        source_export_sha256=_sha256(data),
        safe_color_replacements=safe_count,
        findings=tuple(findings),
    )


def normalize_css_colors(text: str) -> tuple[str, int]:
    """Resolve safe fill/stroke CSS variables to explicit fallback colors."""

    def replace(match: re.Match[str]) -> str:
        return (
            f"{match.group('prefix')}{match.group('color')}"
            f"{match.group('suffix')}"
        )

    return SAFE_COLOR_VAR_RE.subn(replace, text)


def load_receipt(project_root: Path, receipt_path: Path) -> list[dict[str, Any]]:
    """Load and validate one normalization receipt."""

    root = project_root.resolve()
    path = _rooted(root, receipt_path, "receipt")
    try:
        payload = _mapping(json.loads(path.read_text(encoding="utf-8")), "receipt")
    except (json.JSONDecodeError, OSError) as exc:
        raise SvgPipelineError(f"invalid receipt {path}: {exc}") from exc
    unknown = set(payload) - {"schema", "assets"}
    if unknown:
        raise SvgPipelineError(
            "receipt has unsupported fields: " + ", ".join(sorted(unknown))
        )
    if payload.get("schema") != SVG_RECEIPT_SCHEMA:
        raise SvgPipelineError(f"receipt.schema must be {SVG_RECEIPT_SCHEMA}")

    assets: list[dict[str, Any]] = []
    names: set[str] = set()
    paths: set[str] = set()
    raw_assets = _list(payload.get("assets"), "receipt.assets")
    if not raw_assets:
        raise SvgPipelineError("receipt.assets must not be empty")
    for index, raw_asset in enumerate(raw_assets):
        field = f"receipt.assets[{index}]"
        asset = _mapping(raw_asset, field)
        allowed = {
            "name",
            "source_export_sha256",
            "runtime_asset_path",
            "runtime_asset_sha256",
            "normalizations",
        }
        unknown_asset = set(asset) - allowed
        if unknown_asset:
            raise SvgPipelineError(
                f"{field} has unsupported fields: "
                + ", ".join(sorted(unknown_asset))
            )
        name = _string(asset.get("name"), f"{field}.name")
        source_hash = _hash(
            asset.get("source_export_sha256"),
            f"{field}.source_export_sha256",
        )
        runtime_path = _relative(
            asset.get("runtime_asset_path"),
            f"{field}.runtime_asset_path",
        )
        runtime_hash = _hash(
            asset.get("runtime_asset_sha256"),
            f"{field}.runtime_asset_sha256",
        )
        normalizations = _list(
            asset.get("normalizations"),
            f"{field}.normalizations",
        )
        if len(normalizations) != 1 or any(
            not isinstance(value, str)
            or not NORMALIZATION_RE.fullmatch(value)
            for value in normalizations
        ):
            raise SvgPipelineError(
                f"{field}.normalizations must declare the supported rewrite"
            )
        if name in names:
            raise SvgPipelineError(f"duplicate asset name: {name}")
        if runtime_path in paths:
            raise SvgPipelineError(f"duplicate runtime asset path: {runtime_path}")
        names.add(name)
        paths.add(runtime_path)
        _project_path(root, runtime_path, f"{field}.runtime_asset_path")
        assets.append(
            {
                "name": name,
                "source_export_sha256": source_hash,
                "runtime_asset_path": runtime_path,
                "runtime_asset_sha256": runtime_hash,
                "normalizations": normalizations,
            }
        )
    return assets


def verify_receipt(project_root: Path, receipt_path: Path) -> list[str]:
    """Return actionable receipt verification errors."""

    root = project_root.resolve()
    errors: list[str] = []
    for asset in load_receipt(root, receipt_path):
        runtime_path = _project_path(
            root,
            asset["runtime_asset_path"],
            "runtime_asset_path",
        )
        if not runtime_path.is_file():
            errors.append(f"missing:{asset['runtime_asset_path']}")
            continue
        digest = _sha256(runtime_path.read_bytes())
        if digest != asset["runtime_asset_sha256"]:
            errors.append(f"hash:{asset['runtime_asset_path']}")
    return errors


def _normalize(
    project_root: Path,
    sources: list[Path],
    output_dir: Path,
    receipt_path: Path,
) -> dict[str, Any]:
    root = project_root.resolve()
    output = _rooted(root, output_dir, "output_dir")
    receipt = _rooted(root, receipt_path, "receipt")
    if not sources:
        raise SvgPipelineError("no matching SVG files")

    names: set[str] = set()
    prepared: list[tuple[Path, Path, str, bytes, int]] = []
    for source in sources:
        if source.name in names:
            raise SvgPipelineError(f"duplicate output file name: {source.name}")
        names.add(source.name)
        inspection = inspect_svg(source)
        blocking = [
            finding.code
            for finding in inspection.findings
            if finding.severity == "error"
        ]
        if blocking:
            raise SvgPipelineError(
                f"{source}: blocking findings: {','.join(blocking)}"
            )
        original = source.read_text(encoding="utf-8")
        normalized, replaced = normalize_css_colors(original)
        if replaced == 0:
            raise SvgPipelineError(f"{source}: no safe normalization available")
        if ANY_VAR_RE.search(normalized):
            raise SvgPipelineError(f"{source}: unresolved var(...) remains")
        target = output / source.name
        if target.resolve() == source.resolve():
            raise SvgPipelineError(f"{source}: normalization must not overwrite source")
        if target.resolve() == receipt:
            raise SvgPipelineError(
                f"{source}: receipt must not overwrite a runtime asset"
            )
        prepared.append(
            (
                target,
                source,
                inspection.source_export_sha256,
                normalized.encode("utf-8"),
                replaced,
            )
        )

    output.mkdir(parents=True, exist_ok=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    assets: list[dict[str, Any]] = []
    for target, source, source_hash, normalized, replaced in prepared:
        target.write_bytes(normalized)
        assets.append(
            {
                "name": source.stem,
                "source_export_sha256": source_hash,
                "runtime_asset_path": target.relative_to(root).as_posix(),
                "runtime_asset_sha256": _sha256(normalized),
                "normalizations": [
                    f"resolve-css-color-fallbacks:{replaced}",
                ],
            }
        )
    payload = {"schema": SVG_RECEIPT_SCHEMA, "assets": assets}
    receipt.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def _scan_payload(paths: list[Path]) -> dict[str, Any]:
    inspections = [inspect_svg(path) for path in paths]
    return {
        "status": (
            "clean"
            if inspections
            and all(not inspection.findings for inspection in inspections)
            else "review"
        ),
        "files": [
            {
                "path": inspection.path,
                "source_export_sha256": inspection.source_export_sha256,
                "safe_color_replacements": inspection.safe_color_replacements,
                "findings": [asdict(finding) for finding in inspection.findings],
            }
            for inspection in inspections
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan")
    scan.add_argument("paths", nargs="+")
    normalize = subparsers.add_parser("normalize")
    normalize.add_argument("--output-dir", type=Path, required=True)
    normalize.add_argument("--receipt", type=Path, required=True)
    normalize.add_argument("paths", nargs="+")
    verify = subparsers.add_parser("verify")
    verify.add_argument("--receipt", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.project_root.resolve()
    try:
        if args.command == "scan":
            files = iter_files(args.paths)
            if not files:
                raise SvgPipelineError("no matching SVG files")
            payload = _scan_payload(files)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0 if payload["status"] == "clean" else 1
        if args.command == "normalize":
            payload = _normalize(
                root,
                iter_files(args.paths),
                args.output_dir,
                args.receipt,
            )
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        errors = verify_receipt(root, args.receipt)
        payload = {
            "status": "pass" if not errors else "fail",
            "errors": errors,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    except (OSError, SvgPipelineError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

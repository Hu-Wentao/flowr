#!/usr/bin/env python3
"""Print compact FlowR MVVM context without loading large source files."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


SKIP_DIRS = {".dart_tool", ".git", ".idea", ".vscode", "build", "ios/Pods"}


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "packages/flowr/lib/flowr_mvvm.dart").exists():
            return candidate
    return current


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def one_line(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def class_header(source: str, name: str) -> str:
    match = re.search(
        rf"(?:abstract\s+)?class\s+{re.escape(name)}[^\{{]+",
        source,
        flags=re.MULTILINE,
    )
    return one_line(match.group(0)) if match else f"API_NOT_FOUND: {name}"


def constructor_names(source: str, class_name: str) -> list[str]:
    names = []
    for match in re.finditer(rf"\b{re.escape(class_name)}(?:\.(\w+))?\s*\(", source):
        suffix = match.group(1)
        names.append(f"{class_name}.{suffix}" if suffix else class_name)
    return sorted(set(names))


def static_member_names(source: str, class_name: str) -> list[str]:
    names = []
    for match in re.finditer(rf"\bstatic\s+[^\n=]+?\s+(\w+)\s*\(", source):
        names.append(f"{class_name}.{match.group(1)}")
    return sorted(set(names))


def typedef_line(source: str, name: str) -> str:
    match = re.search(rf"typedef\s+{re.escape(name)}[^\n]+(?:\n\s+[^\n;]+)?;", source)
    return one_line(match.group(0)) if match else f"API_NOT_FOUND: {name}"


def path_is_skipped(path: Path) -> bool:
    parts = set(path.parts)
    if parts.intersection(SKIP_DIRS):
        return True
    return "Pods" in parts and "ios" in parts


def common_prefix_len(left: Path, right: Path) -> int:
    left_parts = left.resolve().parts
    right_parts = right.resolve().parts
    count = 0
    for a, b in zip(left_parts, right_parts):
        if a != b:
            break
        count += 1
    return count


def find_mvvm_files(root: Path, target: Path | None, limit: int) -> list[Path]:
    files = [
        path
        for path in root.rglob("*.mvvm.dart")
        if path.is_file() and not path_is_skipped(path)
    ]
    if target is not None:
        target_path = (root / target).resolve() if not target.is_absolute() else target.resolve()
        files.sort(key=lambda p: (-common_prefix_len(p.parent, target_path.parent), len(p.parts), str(p)))
    else:
        files.sort(key=lambda p: (len(p.parts), str(p)))
    return files[:limit]


def summarize_dart_file(path: Path, root: Path) -> str:
    source = read_text(path)
    rel = path.relative_to(root)
    classes = re.findall(r"^\s*(?:sealed\s+|abstract\s+|base\s+|final\s+)?class\s+(\w+)(?:[^{]*)", source, re.MULTILINE)
    extends = re.findall(r"class\s+(\w+)[^{]*extends\s+(Fr(?:Bloc)?ViewModel<[^>{]+>)", source)
    class_part = ", ".join(classes[:8]) if classes else "no classes found"
    extends_part = "; ".join(f"{name} extends {base}" for name, base in extends[:4])
    if extends_part:
        class_part = f"{class_part}; {extends_part}"
    return f"- `{rel}`: {class_part}"


def equal_value_status(config_source: str, changelog_source: str) -> list[str]:
    combined = f"{config_source}\n{changelog_source}"
    lines = []
    if "equal-value re-emission" in combined or "equal-state suppression" in combined:
        lines.append("No public config switch exists for equal-value re-emission.")
    else:
        lines.append("Confirm equal-value behavior before generating compatibility code.")
    if "equal-state suppression" in combined or "does not emit" in combined:
        lines.append("Equal states are suppressed; generate new unequal immutable model instances.")
    else:
        lines.append("Use immutable state updates; inspect changelog if equal-value behavior matters.")
    return lines


def build_report(root: Path, target: Path | None, limit: int) -> str:
    flowr_export = read_text(root / "packages/flowr/lib/flowr_mvvm.dart")
    view_model = read_text(root / "packages/flowr/lib/src/view_model.dart")
    view = read_text(root / "packages/flowr/lib/src/view.dart")
    provider = read_text(root / "packages/flowr/lib/src/provider.dart")
    config = read_text(root / "packages/flowr/lib/src/config.dart")
    changelog = read_text(root / "packages/flowr/CHANGELOG.md")

    report: list[str] = []
    report.append("# FlowR MVVM Context")
    report.append(f"- repo: `{root}`")
    if target is not None:
        report.append(f"- target: `{target}`")
    report.append("")
    report.append("## API Summary")
    if "package:flowr/src/view_model.dart" in flowr_export:
        report.append("- import `package:flowr/flowr_mvvm.dart` for MVVM APIs.")
    else:
        report.append("- API_NOT_FOUND: verify `flowr_mvvm.dart` exports MVVM APIs.")
    report.append(f"- `{class_header(view_model, 'FrViewModel')}`")
    report.append(f"- `{class_header(view_model, 'FrBlocViewModel')}`")
    report.append(f"- `{class_header(view, 'FrView')}`")
    report.append(f"- `{class_header(view, 'FrListener')}`")
    report.append(f"- `{class_header(view, 'FrConsumer')}`")
    report.append(f"- `{typedef_line(view, 'FrSnap')}`")
    constructors = constructor_names(provider, "FrProvider")
    helpers = static_member_names(provider, "FrProvider")
    provider_api = sorted(set(constructors + helpers))
    if provider_api:
        report.append(f"- provider APIs: `{', '.join(provider_api)}`")
    else:
        report.append("- API_NOT_FOUND: inspect `packages/flowr/lib/src/provider.dart`.")
    report.append("")
    report.append("## Breaking-Change Guardrails")
    report.extend(f"- {line}" for line in equal_value_status(config, changelog))
    report.append("- For `List`, `Map`, or `Set` fields, allocate a new collection before emitting.")
    report.append("")
    report.append("## Nearby MVVM Files")
    files = find_mvvm_files(root, target, limit)
    if files:
        report.extend(summarize_dart_file(path, root) for path in files)
    else:
        report.append("- none found")
    report.append("")
    report.append("## Manual Reads")
    report.append("- Read source files only for APIs marked `API_NOT_FOUND`, FlowR internals changes, or uncommon APIs not summarized here.")
    return "\n".join(report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root or any path inside it.")
    parser.add_argument("--target", type=Path, help="Intended .mvvm.dart file or feature directory.")
    parser.add_argument("--limit", type=int, default=8, help="Maximum nearby .mvvm.dart files to list.")
    args = parser.parse_args()

    root = find_repo_root(args.root)
    print(build_report(root, args.target, max(args.limit, 0)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Print compact contract-page layout context."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import cast


SKIP_DIRS = {".dart_tool", ".git", ".idea", ".vscode", "build", "ios/Pods"}


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / "melos.yaml").exists():
            return candidate
    for candidate in (current, *current.parents):
        if (candidate / "pubspec.yaml").exists():
            return candidate
    return current


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


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


def page_root_from_path(path: Path) -> Path | None:
    parts = path.parts
    for index, part in enumerate(parts):
        if part != "lib":
            continue
        if index + 1 < len(parts) and parts[index + 1] == "page":
            return Path(*parts[: index + 2])
        if (
            index + 2 < len(parts)
            and parts[index + 1] == "src"
            and parts[index + 2] == "page"
        ):
            return Path(*parts[: index + 3])
    return None


def contract_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*_page.dart"):
        if not path.is_file() or path_is_skipped(path):
            continue
        if path.name.endswith(".v.dart") or path.name.endswith(".vm.dart"):
            continue
        if page_root_from_path(path) is None:
            continue
        files.append(path)
    return files


def detected_page_roots(root: Path) -> list[Path]:
    roots = {
        page_root
        for path in contract_files(root)
        if (page_root := page_root_from_path(path))
    }
    for candidate in (root / "lib/page", root / "lib/src/page"):
        if candidate.exists():
            roots.add(candidate)
    return sorted(roots, key=lambda path: (len(path.parts), str(path)))


def sort_contract_files(files: list[Path], target: Path | None) -> list[Path]:
    if target is None:
        return sorted(files, key=lambda path: (len(path.parts), str(path)))
    target_path = target.resolve() if target.is_absolute() else target
    return sorted(
        files,
        key=lambda path: (
            -common_prefix_len(path.parent, target_path.parent),
            len(path.parts),
            str(path),
        ),
    )


def class_names(source: str) -> list[str]:
    return re.findall(
        r"^\s*(?:sealed\s+|abstract\s+|base\s+|final\s+)?class\s+(\w+)",
        source,
        re.MULTILINE,
    )


def page_summary(path: Path, root: Path) -> str:
    source = read_text(path)
    rel = path.relative_to(root)
    stem = path.name[:-5]
    view_path = path.with_name(f"{stem}.v.dart")
    vm_path = path.with_name(f"{stem}.vm.dart")
    status: list[str] = []
    status.append("view" if view_path.exists() else "missing view")
    status.append("vm" if vm_path.exists() else "missing vm")
    names = class_names(source)
    class_part = ", ".join(names[:6]) if names else "no classes found"
    return f"- `{rel}`: {', '.join(status)}; classes: {class_part}"


def shared_widget_files(root: Path) -> list[Path]:
    widgets: list[Path] = [
        path
        for path in root.rglob("widget.dart")
        if path.is_file()
        and not path_is_skipped(path)
        and path.parts[-2:] == ("page", "widget.dart")
        and page_root_from_path(path) is not None
    ]
    widgets.sort(key=str)
    return widgets


def build_report(root: Path, target: Path | None, limit: int) -> str:
    report: list[str] = []
    report.append("# Fr Contract MVVM Context")
    report.append(f"- repo: `{root}`")
    if target is not None:
        report.append(f"- target: `{target}`")
    if (root / "skills/flowr-usage/SKILL.md").exists():
        report.append("- flowr usage skill: `skills/flowr-usage/SKILL.md`")
    if (root / "skills/flowr-dart-usage/SKILL.md").exists():
        report.append("- dart usage skill: `skills/flowr-dart-usage/SKILL.md`")
    page_roots = detected_page_roots(root)
    if page_roots:
        roots = ", ".join(f"`{path.relative_to(root)}`" for path in page_roots)
        report.append(f"- detected page root(s): {roots}")
    else:
        report.append("- detected page root(s): none; generator falls back to `lib/page`")
    report.append("")
    report.append("## Layout Guardrails")
    report.append("- `xxx_page.dart` owns imports for both `part` files.")
    report.append(
        "- Keep the contract comment block in figma -> api -> route -> shared widgets -> widget tree -> theme -> events -> state order."
    )
    report.append("- Use `Figma: none` and `API: none` when those sources are not available.")
    report.append(
        "- Use the project's existing `lib/page` or `lib/src/page` root; optional middle folders may sit under `page`."
    )
    report.append("- `page/widget.dart` is only for cross-page reusable widgets.")
    report.append(
        "- Prefer plain-text route comments until router doc refs are resolvable in scope."
    )
    report.append("")
    report.append("## Shared Widget Files")
    widgets = shared_widget_files(root)
    if widgets:
        report.extend(f"- `{path.relative_to(root)}`" for path in widgets[:limit])
    else:
        report.append("- none found")
    report.append("")
    report.append("## Nearby Contract Pages")
    files = sort_contract_files(contract_files(root), target)[:limit]
    if files:
        report.extend(page_summary(path, root) for path in files)
    else:
        report.append("- none found")
    return "\n".join(report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root or any path inside it.",
    )
    _ = parser.add_argument(
        "--target", type=Path, help="Intended page directory or contract file."
    )
    _ = parser.add_argument(
        "--limit", type=int, default=8, help="Maximum page folders to list."
    )
    args = parser.parse_args()

    root_arg = cast(Path, args.root)
    target = cast(Path | None, args.target)
    limit = cast(int, args.limit)

    root = find_repo_root(root_arg)
    if target is not None and not target.is_absolute():
        target = root / target
    print(build_report(root, target, max(limit, 0)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

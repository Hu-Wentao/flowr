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
    for path in root.rglob("*.dart"):
        if not path.is_file() or path_is_skipped(path):
            continue
        if not path.name.endswith(("_page.dart", "_view.dart")):
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
    report.append(
        "- `xxx_page.dart` or `xxx_view.dart` owns imports for both `part` files."
    )
    report.append(
        "- Treat the contract dart file as the only long-lived source of truth; any temporary JSON spec is only a generator hand-off and should not be committed as a parallel design artifact."
    )
    report.append(
        "- The root `XxxPage` / `XxxView` stays stateless and only wires providers/lifecycle hooks; concrete UI belongs in the `.v.dart` part."
    )
    report.append(
        "- Keep the contract comment block in figma -> state ownership -> route -> shared widgets -> widget tree -> theme -> events -> viewmodels -> models order. In `bff` mode, place `BFF-API:` after `Models:`. In concrete API mode, keep `API:` near the top and omit `BFF-API:`."
    )
    report.append(
        "- This skill is bloc-only: analyze M/V/VM/Event first, then generate `FrBlocViewModel` pages from a structured spec."
    )
    report.append(
        "- Page-local models default to the generated `@FrState` Freezed preset so `toJson()` is available for debug snapshots. Target projects must provide `freezed_annotation`, `freezed`, and `build_runner`."
    )
    report.append(
        "- If the target project does not already use `freezed`, load `skills/flowr-dart-usage/references/freezed-install.md` before scaffolding."
    )
    report.append(
        "- Decide state ownership before creating page-private model fields; reference top-level and shared state owners instead of copying their data."
    )
    report.append(
        "- Event comments should reference event classes with `[]`, including private subclasses, because the contract file and `.vm.dart` part share the same library."
    )
    report.append(
        "- Before generating or editing a page, require `figmaUrl` and `api` inputs. `api` must be `NONE`, `BFF`, `BFF-JSON`, `BFF-PROTO`, or a real API/OpenAPI reference."
    )
    report.append(
        "- Read the Figma URL first, then inspect nearby pages, page-level shared widgets, and theme constraints before deriving widgets, reused components, state fields, or models."
    )
    report.append(
        "- If `api` is `NONE`, skip API reading but still record that the page has no backend contract. If `api` resolves to `BFF`, split upstream APIs first and keep local state outside exported DTO classes. `BFF-JSON` means BFF plus a JSON document artifact. `BFF-PROTO` means BFF plus a proto artifact. If `api` points to a concrete reference, read it before finalizing view-model dependencies and DTO ownership."
    )
    report.append(
        "- `exportFormat` is optional when `api` resolves to `BFF`. It accepts `JSON` or `PROTO`, defaults to `JSON`, and should not conflict with `BFF-JSON` / `BFF-PROTO` shorthands embedded in `api`."
    )
    report.append(
        "- Keep `Figma:` as a stable reference to the Figma URL. In `bff` mode, omit `API:`, render `BFF-API:` after `Models:`, and use multiline entries such as `GET <BASE>/home-page/summary` followed by `[SummaryReq], [SummaryModel]`."
    )
    report.append(
        "- Derive `<BASE>` from the page folder chain under `lib/page` or `lib/src/page`: `lib/page/home_page/home_page.dart` -> `<BASE>/home-page/...`; `lib/page/home_page/sub_page/sub_page.dart` -> `<BASE>/home-page/sub-page/...`."
    )
    report.append(
        "- In `bff` mode, `FrAcddMode` only expresses `api` vs `bff`. Skill-layer artifact types are `JSON` and `PROTO`, with `JSON` as the default. Under the hood, `JSON` maps to the `fr_acdd` markdown export with JSON5 request/response snippets."
    )
    report.append(
        "- When exported DTOs need Freezed presets, prefer `@FrAcddFreezed` for `PROTO` and `@FrAcddFreezedJSON` for `JSON`. The JSON preset still needs the usual `factory Xxx.fromJson(...)` and a generated `.g.dart` part in the contract library."
    )
    report.append(
        "- For `JSON` export, do not add protobuf `tag` values by default. If a field annotation would be just `@FrAcddField()`, omit it entirely. Only keep `@FrAcddField(...)` when the field needs proto tags or other non-default metadata."
    )
    report.append(
        "- `@FrAcddDto` should describe backend-transfer DTOs only. Page-local state belongs in page models or view-model members, not in exported DTO classes. If a model contains runtime-only or non-JSON-serializable fields, keep it on `preset: plain` instead of the default `@FrState` preset."
    )
    report.append(
        "- Do not create `_XxxPageDimens` style classes. Prefer direct literals plus responsive constraints such as expanded width, flex layout, and parent-driven sizing."
    )
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

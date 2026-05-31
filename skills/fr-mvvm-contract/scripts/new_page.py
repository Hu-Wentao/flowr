#!/usr/bin/env python3
"""Generate a contract-first FlowR page starter."""

from __future__ import annotations

import argparse
from collections import Counter
import re
from pathlib import Path


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


def path_is_skipped(path: Path) -> bool:
    parts = set(path.parts)
    if parts.intersection(SKIP_DIRS):
        return True
    return "Pods" in parts and "ios" in parts


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


def contract_page_files(root: Path) -> list[Path]:
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


def infer_page_root(project_root: Path) -> Path:
    lib_page = project_root / "lib/page"
    lib_src_page = project_root / "lib/src/page"

    counts: Counter[Path] = Counter()
    for path in contract_page_files(project_root):
        page_root = page_root_from_path(path)
        if page_root is not None:
            counts[page_root] += 1

    if counts:
        return sorted(
            counts,
            key=lambda path: (
                -counts[path],
                0 if path == lib_page else 1 if path == lib_src_page else 2,
                len(path.parts),
                str(path),
            ),
        )[0]

    if lib_src_page.exists() and not lib_page.exists():
        return lib_src_page

    return lib_page


def resolve_relative_to_root(path: Path, project_root: Path) -> Path:
    return path if path.is_absolute() else project_root / path


def ensure_relative(path: Path, option: str) -> Path:
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{option} must be a relative path below the page root")
    return path


def display_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def tokenize_name(value: str) -> list[str]:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value.strip())
    parts = [part.lower() for part in re.findall(r"[A-Za-z0-9]+", normalized)]
    if not parts:
        raise ValueError("name must contain at least one letter or number")
    if parts[-1] != "page":
        parts.append("page")
    return parts


def snake_name(value: str) -> str:
    return "_".join(tokenize_name(value))


def pascal_name(value: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in tokenize_name(value))


def title_name(value: str) -> str:
    return " ".join(part[:1].upper() + part[1:] for part in tokenize_name(value))


def route_line(route: str | None) -> str:
    if route:
        return f"/// Route: {route}"
    return "/// Route: update route name or add a router doc ref when available."


def section_line(label: str, value: str | None) -> str:
    return f"/// {label}: {value}" if value else f"/// {label}: none"


def contract_template(
    name: str,
    mode: str,
    route: str | None,
    figma: str | None,
    api: str | None,
) -> str:
    title = title_name(name)
    loading_default = "true" if mode == "bloc" else "false"
    events_block = (
        "\n".join(
            (
                "/// Events:",
                f"/// - [{name}Started] bootstrap page state",
                f"/// - [{name}TitleChanged] update page title",
            )
        )
        if mode == "bloc"
        else "/// Events: none"
    )
    on_created = (
        f",\n      onCreated: (context, vm) => vm.add(const {name}Started())"
        if mode == "bloc"
        else ""
    )
    async_import = "import 'dart:async';\n\n" if mode == "method" else ""

    return f"""{async_import}import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

part '{snake_name(name)}.v.dart';
part '{snake_name(name)}.vm.dart';

{section_line("Figma", figma)}
{section_line("API", api)}
{route_line(route)}
/// Reused Widgets: none. Add shared widgets from the project page root's `widget.dart` when needed.
/// Widget Tree:
/// [{name}Scaffold]
/// |- [{name}Header]
/// '- [{name}Body]
/// Theme: [{name}Theme]
{events_block}
/// State: [{name}ViewModel], [{name}Model]
class {name} extends StatelessWidget {{
  const {name}({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return FrProvider(
      (_) => {name}ViewModel(){on_created},
      child: const _{name}View(),
    );
  }}
}}

class {name}Theme {{
  final EdgeInsets pagePadding;
  final double sectionSpacing;

  const {name}Theme({{
    this.pagePadding = const EdgeInsets.all(24),
    this.sectionSpacing = 16,
  }});
}}

class {name}Model {{
  final bool loading;
  final String title;

  const {name}Model({{
    this.loading = {loading_default},
    this.title = '{title}',
  }});

  {name}Model copyWith({{
    bool? loading,
    String? title,
  }}) =>
      {name}Model(
        loading: loading ?? this.loading,
        title: title ?? this.title,
      );
}}
"""


def view_template(name: str, mode: str) -> str:
    action = (
        f"() => snap.vm.add({name}TitleChanged('${{snap.data.title}} updated'))"
        if mode == "bloc"
        else f"() => snap.vm.rename('${{snap.data.title}} updated')"
    )

    return f"""part of '{snake_name(name)}.dart';

class _{name}View extends StatelessWidget {{
  const _{name}View();

  @override
  Widget build(BuildContext context) {{
    return FrView<{name}ViewModel, {name}Model>(
      builder: (context, snap, child) => {name}Scaffold(snap: snap),
    );
  }}
}}

/// Main scaffold for the page layout.
class {name}Scaffold extends StatelessWidget {{
  const {name}Scaffold({{
    required this.snap,
    super.key,
  }});

  final FrSnap<{name}ViewModel, {name}Model> snap;

  @override
  Widget build(BuildContext context) {{
    const theme = {name}Theme();

    return Scaffold(
      appBar: AppBar(
        title: Text(snap.data.title),
      ),
      body: Padding(
        padding: theme.pagePadding,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            {name}Header(title: snap.data.title),
            SizedBox(height: theme.sectionSpacing),
            {name}Body(snap: snap),
          ],
        ),
      ),
    );
  }}
}}

/// Page title section.
class {name}Header extends StatelessWidget {{
  const {name}Header({{
    required this.title,
    super.key,
  }});

  final String title;

  @override
  Widget build(BuildContext context) {{
    return Text(
      title,
      style: Theme.of(context).textTheme.headlineSmall,
    );
  }}
}}

/// Main body bound to current page state.
class {name}Body extends StatelessWidget {{
  const {name}Body({{
    required this.snap,
    super.key,
  }});

  final FrSnap<{name}ViewModel, {name}Model> snap;

  @override
  Widget build(BuildContext context) {{
    if (snap.data.loading) {{
      return const CircularProgressIndicator();
    }}

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Current title: ${{snap.data.title}}'),
        const SizedBox(height: 12),
        FilledButton(
          onPressed: {action},
          child: const Text('Rename'),
        ),
      ],
    );
  }}
}}
"""


def method_vm_template(name: str) -> str:
    return f"""part of '{snake_name(name)}.dart';

class {name}ViewModel extends FrViewModel<{name}Model> {{
  {name}ViewModel() : super(const {name}Model());

  FutureOr<{name}Model?> setLoading(bool loading) => update(
        (old) => old.copyWith(loading: loading),
      );

  FutureOr<{name}Model?> rename(String title) => update(
        (old) => old.copyWith(title: title),
      );
}}
"""


def bloc_vm_template(name: str) -> str:
    return f"""part of '{snake_name(name)}.dart';

sealed class {name}Event {{
  const {name}Event();
}}

class {name}Started extends {name}Event {{
  const {name}Started();
}}

class {name}TitleChanged extends {name}Event {{
  const {name}TitleChanged(this.title);

  final String title;
}}

class {name}ViewModel extends FrBlocViewModel<{name}Event, {name}Model> {{
  {name}ViewModel() : super(const {name}Model()) {{
    on<{name}Started>(
      (event, emit) => emit(state.copyWith(loading: false)),
    );
    on<{name}TitleChanged>(
      (event, emit) => emit(state.copyWith(title: event.title)),
    );
  }}
}}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Page name, for example profile, profile_page, or ProfilePage.")
    parser.add_argument("--mode", choices=("method", "bloc"), default="method")
    parser.add_argument("--figma", help="Figma source note or link written into the contract comment.")
    parser.add_argument("--api", help="API/data-source note written into the contract comment.")
    parser.add_argument("--route", help="Plain-text route label written into the contract comment.")
    parser.add_argument(
        "--page-root",
        type=Path,
        help=(
            "Page root such as lib/page or lib/src/page. Defaults to the "
            "project's existing page layout."
        ),
    )
    parser.add_argument(
        "--parent",
        type=Path,
        help=(
            "Optional middle directory below the page root, for example "
            "account/settings."
        ),
    )
    parser.add_argument(
        "--dir",
        type=Path,
        help=(
            "Full output directory. Overrides --page-root and --parent; "
            "default is <detected-page-root>/<name>_page."
        ),
    )
    parser.add_argument("--force", action="store_true", help="Overwrite files when they already exist.")
    return parser.parse_args()


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; pass --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    class_name = pascal_name(args.name)
    file_name = snake_name(args.name)
    project_root = find_repo_root(Path.cwd())
    if args.dir:
        output_dir = args.dir
    else:
        page_root = (
            resolve_relative_to_root(args.page_root, project_root)
            if args.page_root
            else infer_page_root(project_root)
        )
        try:
            parent = ensure_relative(args.parent, "--parent") if args.parent else None
        except ValueError as error:
            raise SystemExit(str(error)) from error
        output_dir = page_root / parent / file_name if parent else page_root / file_name

    contract_path = output_dir / f"{file_name}.dart"
    view_path = output_dir / f"{file_name}.v.dart"
    vm_path = output_dir / f"{file_name}.vm.dart"
    vm_content = (
        method_vm_template(class_name)
        if args.mode == "method"
        else bloc_vm_template(class_name)
    )

    try:
        write_file(
            contract_path,
            contract_template(
                class_name,
                args.mode,
                args.route,
                args.figma,
                args.api,
            ),
            args.force,
        )
        write_file(view_path, view_template(class_name, args.mode), args.force)
        write_file(vm_path, vm_content, args.force)
    except FileExistsError as error:
        raise SystemExit(str(error)) from error

    print(f"wrote {display_path(contract_path, project_root)}")
    print(f"wrote {display_path(view_path, project_root)}")
    print(f"wrote {display_path(vm_path, project_root)}")
    print(
        "next: fvm dart format "
        f"{display_path(contract_path, project_root)} "
        f"{display_path(view_path, project_root)} "
        f"{display_path(vm_path, project_root)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

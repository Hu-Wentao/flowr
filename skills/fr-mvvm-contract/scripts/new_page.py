#!/usr/bin/env python3
"""Generate a contract-first FlowR page starter."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


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


def contract_template(name: str, mode: str, route: str | None) -> str:
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

{route_line(route)}
/// Reused Widgets: none. Add shared widgets from `lib/page/widget.dart` when needed.
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
    parser.add_argument("--route", help="Plain-text route label written into the contract comment.")
    parser.add_argument("--dir", type=Path, help="Output directory. Defaults to lib/page/<name>_page.")
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
    output_dir = args.dir or Path("lib/page") / file_name

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
            contract_template(class_name, args.mode, args.route),
            args.force,
        )
        write_file(view_path, view_template(class_name, args.mode), args.force)
        write_file(vm_path, vm_content, args.force)
    except FileExistsError as error:
        raise SystemExit(str(error)) from error

    print(f"wrote {contract_path}")
    print(f"wrote {view_path}")
    print(f"wrote {vm_path}")
    print(f"next: fvm dart format {contract_path} {view_path} {vm_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

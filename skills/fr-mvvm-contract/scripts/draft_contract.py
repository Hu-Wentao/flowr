#!/usr/bin/env python3
"""Create the reviewable Page Support plus Component Contract source pair."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def pascal(value: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value))
    if not parts:
        raise ValueError("name must contain letters or numbers")
    return "".join(part[:1].upper() + part[1:] for part in parts)


def snake(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value).replace("-", "_")
    value = re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_").lower()
    if not value:
        raise ValueError("name must contain letters or numbers")
    return value


def write(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"refusing to overwrite {path}; pass --force")
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--dir", type=Path, required=True)
    parser.add_argument("--figma-url", required=True)
    parser.add_argument("--api", default="BFF-JSON")
    parser.add_argument("--route", default="pending route registration")
    parser.add_argument("--component-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    base = snake(args.name)
    prefix = pascal(base)
    args.dir.mkdir(parents=True, exist_ok=True)
    shell = args.dir / f"{base}.dart"
    contract = args.dir / f"{base}.c.dart"
    write(
        shell,
        "import 'package:flowr/flowr_mvvm.dart';\n"
        "import 'package:flutter/material.dart';\n"
        "import 'package:freezed_annotation/freezed_annotation.dart';\n\n"
        f"part '{base}.c.dart';\n"
        f"part '{base}.v.dart';\n"
        f"part '{base}.vm.dart';\n"
        f"part '{base}.freezed.dart';\n"
        f"part '{base}.g.dart';\n",
        args.force,
    )
    write(
        contract,
        f"part of '{base}.dart';\n\n"
        f"/// Figma: {args.figma_url}\n"
        f"/// BFF-API: {args.api}\n"
        "/// State Ownership: component-owned\n"
        "/// Components: review lib/components for cross-route reuse before implementation.\n"
        f"/// Widget Tree: [{prefix}View]\n"
        "/// Theme: none\n"
        f"/// Events: [{prefix}Started]\n"
        f"/// ViewModels: [{prefix}ViewModel]\n"
        f"/// Models: [{prefix}Model]\n"
        f"class {prefix}PageArgs {{\n"
        f"  const {prefix}PageArgs();\n"
        "}\n\n"
        f"class {prefix}View extends StatelessWidget {{\n"
        f"  const {prefix}View({{required this.args, super.key}});\n\n"
        f"  final {prefix}PageArgs args;\n\n"
        "  @override\n"
        "  Widget build(BuildContext context) {\n"
        f"    return FrProvider((context) => {prefix}ViewModel(args: args),\n"
        f"      onCreated: (context, vm) => vm.add(const {prefix}Started()),\n"
        f"      child: const _{prefix}ViewBody(),\n"
        "    );\n"
        "  }\n"
        "}\n\n"
        "@FrState\n"
        f"class {prefix}Model with _${prefix}Model {{\n"
        f"  const factory {prefix}Model() = _{prefix}Model;\n"
        "}\n",
        args.force,
    )
    if not args.component_only:
        write(
            args.dir / f"{base}.page.dart",
            f"import '{base}.dart';\n"
            "import 'package:flutter/material.dart';\n\n"
            f"/// Route: {args.route}\n"
            f"/// Component: [{prefix}View]\n"
            f"class {prefix}Page extends StatelessWidget {{\n"
            f"  const {prefix}Page({{required this.args, super.key}});\n\n"
            f"  final {prefix}PageArgs args;\n\n"
            "  @override\n"
            "  Widget build(BuildContext context) => "
            f"{prefix}View(args: args);\n"
            "}\n",
            args.force,
        )
    print(shell)
    print(contract)
    if not args.component_only:
        print(args.dir / f"{base}.page.dart")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

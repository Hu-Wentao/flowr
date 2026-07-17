#!/usr/bin/env python3
"""Create the reviewable Page Support plus Component Contract source pair."""

from __future__ import annotations

import argparse
import re
import sys
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
    parser.add_argument(
        "--mode",
        choices=("bff-json", "api"),
        help="Contract mode. Defaults to bff-json when no concrete API is supplied.",
    )
    parser.add_argument(
        "--api",
        help="Concrete API description in api mode; legacy `--api BFF-JSON` is deprecated.",
    )
    parser.add_argument("--route", default="pending route registration")
    parser.add_argument(
        "--theme",
        choices=("none", "material", "fr-mvvm-theme"),
        default="none",
    )
    parser.add_argument("--theme-type")
    parser.add_argument(
        "--theme-owner", choices=("app-shared", "component")
    )
    parser.add_argument("--component-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    mode = args.mode
    if mode is None and args.api is None:
        mode = "bff-json"
    elif mode is None and args.api == "BFF-JSON":
        mode = "bff-json"
        print(
            "warning: `--api BFF-JSON` is deprecated; use `--mode bff-json`",
            file=sys.stderr,
        )
    elif mode is None:
        parser.error("a concrete --api requires explicit `--mode api`")
    if mode == "api" and (not args.api or args.api == "BFF-JSON"):
        parser.error("`--mode api` requires a concrete --api description")
    if mode == "bff-json" and args.api and args.api != "BFF-JSON":
        parser.error("use `--mode api` for a concrete backend API")
    if args.theme == "fr-mvvm-theme":
        if not args.theme_type or not args.theme_owner:
            parser.error(
                "--theme fr-mvvm-theme requires --theme-type and --theme-owner"
            )
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.theme_type):
            parser.error("--theme-type must be a Dart type identifier")
    elif args.theme_type or args.theme_owner:
        parser.error(
            "--theme-type/--theme-owner are valid only with --theme fr-mvvm-theme"
        )
    base = snake(args.name)
    prefix = pascal(base)
    theme_contract = (
        f"/// Theme: fr-mvvm-theme [{args.theme_type}]\n"
        f"/// Theme Ownership: {args.theme_owner}\n"
        if args.theme == "fr-mvvm-theme"
        else f"/// Theme: {args.theme}\n"
    )
    args.dir.mkdir(parents=True, exist_ok=True)
    shell = args.dir / f"{base}.dart"
    contract = args.dir / f"{base}.c.dart"
    fr_acdd_import = (
        "import 'package:fr_acdd/fr_acdd.dart';\n" if mode == "bff-json" else ""
    )
    write(
        shell,
        "import 'package:flowr/flowr_mvvm.dart';\n"
        + fr_acdd_import
        + "import 'package:flutter/material.dart';\n"
        "import 'package:freezed_annotation/freezed_annotation.dart';\n\n"
        f"part '{base}.c.dart';\n"
        f"part '{base}.v.dart';\n"
        f"part '{base}.vm.dart';\n"
        f"part '{base}.freezed.dart';\n"
        f"part '{base}.g.dart';\n",
        args.force,
    )
    api_section = (
        "/// BFF-API:\n"
        f"/// POST <BASE>/{base.replace('_', '-')}/bootstrap\n"
        f"/// [{prefix}BffRequest], [{prefix}BffResponse]\n"
        if mode == "bff-json"
        else f"/// API: {args.api}\n"
    )
    page_annotation = (
        "@FrAcddPage(\n"
        "  mode: FrAcddMode.bff,\n"
        f"  namespace: '{base}',\n"
        ")\n"
        if mode == "bff-json"
        else ""
    )
    dto_contract = (
        "\n// Replace the placeholder fields while completing the contract; do not\n"
        "// generate the BFF artifact until the business fields are approved.\n"
        "@FrAcddDto(kind: FrAcddDtoKind.root)\n"
        "@FrAcddFreezedJSON\n"
        f"class {prefix}BffRequest with _${prefix}BffRequest {{\n"
        f"  const factory {prefix}BffRequest({{\n"
        "    required String pendingRequestField,\n"
        f"  }}) = _{prefix}BffRequest;\n\n"
        f"  factory {prefix}BffRequest.fromJson(Map<String, dynamic> json) =>\n"
        f"      _${prefix}BffRequestFromJson(json);\n"
        "}\n\n"
        "@FrAcddDto(kind: FrAcddDtoKind.root)\n"
        "@FrAcddFreezedJSON\n"
        f"class {prefix}BffResponse with _${prefix}BffResponse {{\n"
        f"  const factory {prefix}BffResponse({{\n"
        "    required String pendingResponseField,\n"
        f"  }}) = _{prefix}BffResponse;\n\n"
        f"  factory {prefix}BffResponse.fromJson(Map<String, dynamic> json) =>\n"
        f"      _${prefix}BffResponseFromJson(json);\n"
        "}\n"
        if mode == "bff-json"
        else ""
    )
    write(
        contract,
        f"part of '{base}.dart';\n\n"
        f"/// Figma: {args.figma_url}\n"
        "/// State Ownership: component-owned\n"
        "/// Components: review lib/components for cross-route reuse before implementation.\n"
        "/// Shared Widgets: review route widgets and lib/widgets before implementation.\n"
        f"/// Widget Tree: [{prefix}View] > TODO: list key widgets before approval\n"
        f"{theme_contract}"
        f"/// Events: [{prefix}Started]\n"
        f"/// ViewModels: [{prefix}ViewModel]\n"
        f"/// Models: [{prefix}Model]\n"
        + api_section
        + f"class {prefix}Args {{\n"
        f"  const {prefix}Args();\n"
        "}\n\n"
        + page_annotation
        + f"class {prefix}View extends StatelessWidget {{\n"
        f"  const {prefix}View({{required this.args, super.key}});\n\n"
        f"  final {prefix}Args args;\n\n"
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
        "}\n"
        + dto_contract,
        args.force,
    )
    if not args.component_only:
        write(
            args.dir / f"{base}.page.dart",
            f"import '{base}.dart';\n"
            "import 'package:flutter/material.dart';\n\n"
            f"/// Route: {args.route}\n"
            f"/// Component: [{prefix}View]\n"
            f"class {prefix}PageArgs {{\n"
            f"  const {prefix}PageArgs();\n"
            "}\n\n"
            f"class {prefix}Page extends StatelessWidget {{\n"
            f"  const {prefix}Page({{required this.args, super.key}});\n\n"
            f"  final {prefix}PageArgs args;\n\n"
            "  @override\n"
            "  Widget build(BuildContext context) => "
            f"{prefix}View(args: const {prefix}Args());\n"
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

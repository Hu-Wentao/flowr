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
    parser.add_argument("--theme-owner", choices=("app-shared", "component"))
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
        "/// API Type: <PENDING_API_TYPE>\n"
        "/// BFF-API:\n"
        "/// <PENDING_METHOD> <PENDING_PATH>\n"
        f"/// [{prefix}BffReq], [{prefix}BffRsp]\n"
        "/// Data:\n"
        "/// - UI Data: <PENDING_UI_DATA>\n"
        "/// - Source: <PENDING_DATA_SOURCE>\n"
        "/// - Loading/Refresh: <PENDING_LOADING_REFRESH>\n"
        "/// - Empty/Error: <PENDING_EMPTY_ERROR>\n"
        "/// Business:\n"
        "/// - Goal: <PENDING_GOAL>\n"
        "/// - Upstream Proof: <PENDING_UPSTREAM_PROOF>\n"
        "/// - Effect: <PENDING_EFFECT>\n"
        "/// - Success Condition: <PENDING_SUCCESS_CONDITION>\n"
        "/// - Failure Cases: <PENDING_ERROR> -> <PENDING_RECOVERY>\n"
        "/// - Navigation Ownership: <PENDING_NAVIGATION_OWNERSHIP>\n"
        "/// Request Field Sources:\n"
        "/// - pendingRequestField <- <PENDING_SOURCE> | <PENDING_PURPOSE>\n"
        "/// BFF Service: <PENDING_SERVICE>\n"
        if mode == "bff-json"
        else (
            "/// API Type: <PENDING_API_TYPE>\n"
            f"/// API: {args.api}\n"
            "/// Data:\n"
            "/// - UI Data: <PENDING_UI_DATA>\n"
            "/// - Source: <PENDING_DATA_SOURCE>\n"
            "/// - Loading/Refresh: <PENDING_LOADING_REFRESH>\n"
            "/// - Empty/Error: <PENDING_EMPTY_ERROR>\n"
            "/// Business:\n"
            "/// - Goal: <PENDING_GOAL>\n"
            "/// - Upstream Proof: <PENDING_UPSTREAM_PROOF>\n"
            "/// - Effect: <PENDING_EFFECT>\n"
            "/// - Success Condition: <PENDING_SUCCESS_CONDITION>\n"
            "/// - Failure Cases: <PENDING_ERROR> -> <PENDING_RECOVERY>\n"
            "/// - Navigation Ownership: <PENDING_NAVIGATION_OWNERSHIP>\n"
        )
    )
    page_annotation = (
        f"@FrAcddPage(\n  mode: FrAcddMode.bff,\n  namespace: '{base}',\n)\n"
        if mode == "bff-json"
        else ""
    )
    dto_contract = (
        "\n/// Replace the placeholder fields while completing the contract; do not\n"
        "/// generate the BFF artifact until API semantics and fields are approved.\n"
        "@FrAcddDto(kind: FrAcddDtoKind.root)\n"
        "@FrAcddFreezedJSON\n"
        f"abstract class {prefix}BffReq with _${prefix}BffReq {{\n"
        f"  const factory {prefix}BffReq({{\n"
        "    required String pendingRequestField,\n"
        f"  }}) = _{prefix}BffReq;\n\n"
        f"  factory {prefix}BffReq.fromJson(Map<String, dynamic> json) =>\n"
        f"      _${prefix}BffReqFromJson(json);\n"
        "}\n\n"
        "@FrAcddDto(kind: FrAcddDtoKind.root)\n"
        "@FrAcddFreezedJSON\n"
        f"abstract class {prefix}BffRsp with _${prefix}BffRsp {{\n"
        f"  const factory {prefix}BffRsp({{\n"
        "    required String pendingResponseField,\n"
        f"  }}) = _{prefix}BffRsp;\n\n"
        f"  factory {prefix}BffRsp.fromJson(Map<String, dynamic> json) =>\n"
        f"      _${prefix}BffRspFromJson(json);\n"
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
        + page_annotation
        + f"class {prefix}View extends StatelessWidget {{\n"
        f"  const {prefix}View({{super.key}});\n\n"
        "  @override\n"
        "  Widget build(BuildContext context) {\n"
        f"    return FrProvider((context) => {prefix}ViewModel(),\n"
        f"      onCreated: (context, vm) => vm.add(const {prefix}Started()),\n"
        f"      child: const _{prefix}ViewBody(),\n"
        "    );\n"
        "  }\n"
        "}\n\n"
        "@FrState\n"
        f"class {prefix}Model with _${prefix}Model {{\n"
        f"  const factory {prefix}Model() = _{prefix}Model;\n"
        "}\n" + dto_contract,
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
            f"const {prefix}View();\n"
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

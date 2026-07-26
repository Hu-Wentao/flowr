#!/usr/bin/env python3
"""Create the reviewable Page Support plus Component Contract source pair."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from contract_core import ContractError, validate_leaf_module_directory


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
        "--figma-frame",
        required=True,
        help="Exact title of the authoritative Figma Frame.",
    )
    parser.add_argument(
        "--mode",
        choices=("local", "bff-json", "api"),
        help=(
            "Contract mode. Page drafts default to bff-json; component-only "
            "drafts default to local."
        ),
    )
    parser.add_argument(
        "--api",
        help="Concrete API description in api mode; legacy `--api BFF-JSON` is deprecated.",
    )
    parser.add_argument("--route", default="pending route registration")
    parser.add_argument(
        "--theme",
        choices=("none", "material", "app-shared", "component"),
        default="none",
    )
    parser.add_argument("--theme-type")
    parser.add_argument("--component-only", action="store_true")
    parser.add_argument(
        "--state-owner",
        choices=("none", "app", "component"),
        help=(
            "Component-only state owner. Defaults to none. Component-owned "
            "state is an explicit opt-in."
        ),
    )
    parser.add_argument(
        "--state-type",
        help="Upstream ViewModel type required by --state-owner app.",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    mode = args.mode
    if mode is None and args.api is None:
        mode = "local" if args.component_only else "bff-json"
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
    if mode == "local" and args.api:
        parser.error("`--mode local` does not accept --api")
    if not args.component_only and (args.state_owner or args.state_type):
        parser.error("--state-owner and --state-type are component-only options")
    state_owner = args.state_owner or ("none" if args.component_only else "page")
    if state_owner == "app":
        if not args.state_type:
            parser.error("--state-owner app requires --state-type")
        if mode != "local":
            parser.error("app-owned components use --mode local")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.state_type):
            parser.error("--state-type must be a Dart type identifier")
    elif args.state_type:
        parser.error("--state-type is valid only with --state-owner app")
    if args.component_only and mode in {"bff-json", "api"} and state_owner != "component":
        parser.error(
            "component-only API/BFF drafts require explicit "
            "`--state-owner component`"
        )
    if args.theme in {"app-shared", "component"}:
        if not args.theme_type:
            parser.error(f"--theme {args.theme} requires --theme-type")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.theme_type):
            parser.error("--theme-type must be a Dart type identifier")
    elif args.theme_type:
        parser.error("--theme-type is valid only with --theme app-shared or component")
    base = snake(args.name)
    prefix = pascal(base)
    theme_contract = (
        f"/// Theme: {args.theme} [{args.theme_type}]\n"
        if args.theme in {"app-shared", "component"}
        else f"/// Theme: {args.theme}\n"
    )
    args.dir.mkdir(parents=True, exist_ok=True)
    shell = args.dir / f"{base}.dart"
    contract = args.dir / f"{base}.c.dart"
    try:
        validate_leaf_module_directory(shell)
    except ContractError as error:
        parser.error(str(error))
    owns_state = state_owner in {"page", "component"}
    uses_flowr = state_owner != "none"
    uses_codegen = owns_state or mode == "bff-json"
    imports = ""
    if uses_flowr:
        imports += "import 'package:flowr/flowr_mvvm.dart';\n"
    if mode == "bff-json":
        imports += "import 'package:fr_acdd/fr_acdd.dart';\n"
    imports += "import 'package:flutter/material.dart';\n"
    if uses_codegen:
        imports += "import 'package:freezed_annotation/freezed_annotation.dart';\n"
    parts = f"\npart '{base}.c.dart';\npart '{base}.v.dart';\n"
    if owns_state:
        parts += f"part '{base}.vm.dart';\n"
    if uses_codegen:
        parts += f"part '{base}.freezed.dart';\npart '{base}.g.dart';\n"
    write(
        shell,
        imports + parts,
        args.force,
    )
    if mode == "bff-json":
        api_section = (
            "/// BFF-API:\n"
            "/// <PENDING_METHOD> <PENDING_PATH>\n"
            f"/// [{prefix}BffReq], [{prefix}BffRsp]\n"
            "/// Behavior:\n"
            "/// - UI Data: <PENDING_UI_DATA>\n"
            "/// - Source: <PENDING_DATA_SOURCE>\n"
            "/// - Loading/Refresh: <PENDING_LOADING_REFRESH>\n"
            "/// - Empty/Error: <PENDING_EMPTY_ERROR>\n"
            "/// - Effect: <PENDING_EFFECT>\n"
            "/// - Success: <PENDING_SUCCESS>\n"
            "/// - Failure: <PENDING_ERROR> -> <PENDING_RECOVERY>\n"
            "/// - Navigation: <PENDING_NAVIGATION>\n"
            "/// Request Field Sources:\n"
            "/// - pendingRequestField <- <PENDING_SOURCE> | <PENDING_PURPOSE>\n"
            f"/// BFF Service: [{prefix}Service]\n"
        )
    elif mode == "api":
        api_section = (
            f"/// API: {args.api}\n"
            "/// Behavior:\n"
            "/// - UI Data: <PENDING_UI_DATA>\n"
            "/// - Source: <PENDING_DATA_SOURCE>\n"
            "/// - Loading/Refresh: <PENDING_LOADING_REFRESH>\n"
            "/// - Empty/Error: <PENDING_EMPTY_ERROR>\n"
            "/// - Effect: <PENDING_EFFECT>\n"
            "/// - Success: <PENDING_SUCCESS>\n"
            "/// - Failure: <PENDING_ERROR> -> <PENDING_RECOVERY>\n"
            "/// - Navigation: <PENDING_NAVIGATION>\n"
        )
    else:
        api_section = ""
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
        f"      _${prefix}BffReqFromJson(json);\n\n"
        "  @override\n"
        "  Map<String, dynamic> toJson();\n"
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
    catalog_contract = (
        "/// Capabilities:\n"
        "/// - TODO: declare the cross-route capability owned by this component.\n"
        "/// Public Views:\n"
        f"/// - [{prefix}View] — TODO: describe this reusable entry.\n"
        if args.component_only
        else ""
    )
    if state_owner == "page":
        state_ownership = f"page-owned [{prefix}ViewModel]"
        state_sections = (
            f"/// Events: [{prefix}Started]\n"
            f"/// Startup Event: [{prefix}Started]\n"
            f"/// ViewModels: [{prefix}ViewModel]\n"
            f"/// Models: [{prefix}Model]\n"
        )
    elif state_owner == "component":
        state_ownership = f"component-owned [{prefix}ViewModel]"
        state_sections = (
            f"/// Events: [{prefix}Started]\n"
            f"/// Startup Event: [{prefix}Started]\n"
            f"/// ViewModels: [{prefix}ViewModel]\n"
            f"/// Models: [{prefix}Model]\n"
        )
    elif state_owner == "app":
        state_ownership = f"app-owned [{args.state_type}]"
        state_sections = f"/// ViewModels: [{args.state_type}]\n"
    else:
        state_ownership = "none"
        state_sections = ""
    if state_owner == "component":
        view_body = (
            f"    return FrProvider((context) => {prefix}ViewModel(),\n"
            f"      onCreated: (context, vm) => vm.add(const {prefix}Started()),\n"
            f"      child: const _{prefix}ViewBody(),\n"
            "    );\n"
        )
    else:
        view_body = f"    return const _{prefix}ViewBody();\n"
    model_contract = (
        "\n@FrState\n"
        f"class {prefix}Model with _${prefix}Model {{\n"
        f"  const factory {prefix}Model() = _{prefix}Model;\n"
        "}\n"
        if owns_state
        else ""
    )
    write(
        contract,
        f"part of '{base}.dart';\n\n"
        "/// Figma:\n"
        f"/// - Frame: {args.figma_frame}\n"
        f"/// - Node: {args.figma_url}\n"
        f"/// State Ownership: {state_ownership}\n"
        + catalog_contract
        + f"/// Widget Tree: [{prefix}View] > TODO: list key widgets before approval\n"
        f"{theme_contract}"
        + state_sections
        + api_section
        + page_annotation
        + f"class {prefix}View extends StatelessWidget {{\n"
        f"  const {prefix}View({{super.key}});\n\n"
        "  @override\n"
        "  Widget build(BuildContext context) {\n"
        + view_body
        + "  }\n"
        "}\n"
        + model_contract
        + dto_contract,
        args.force,
    )
    if not args.component_only:
        route = args.route
        route_literal = repr(route if route.startswith("/") else "<PENDING_ROUTE>")
        write(
            args.dir / f"{base}.page.dart",
            "import 'package:flutter/widgets.dart';\n"
            "import 'package:flowr/flowr_mvvm.dart';\n"
            "import 'package:go_router/go_router.dart';\n\n"
            f"import '{base}.dart';\n\n"
            f"part '{base}.page.g.dart';\n\n"
            f"@TypedGoRoute<{prefix}Page>(path: {route_literal})\n"
            f"class {prefix}Page extends GoRouteData with ${prefix}Page {{\n"
            f"  const {prefix}Page();\n\n"
            "  @override\n"
            "  Widget build(BuildContext context, GoRouterState state) =>\n"
            f"      FrProvider((context) => {prefix}ViewModel(),\n"
            f"        onCreated: (context, vm) => vm.add(const {prefix}Started()),\n"
            f"        child: const {prefix}View(),\n"
            "      );\n"
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

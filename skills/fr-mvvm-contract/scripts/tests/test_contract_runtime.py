from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1]
UV_RUN_SCRIPT = ("uv", "run", "--script")
for path in (SCRIPTS,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from contract_core import ContractError  # noqa: E402
from contract_parser import parse_component, parse_page  # noqa: E402
import generate_from_contract as generator  # noqa: E402
from validate_contract import validate_widget_tree  # noqa: E402


class ContractRuntimeTest(unittest.TestCase):
    def draft(
        self, directory: Path, *, page: bool = True, extra: list[str] | None = None
    ) -> Path:
        command = [
            *UV_RUN_SCRIPT,
            str(SCRIPTS / "draft_contract.py"),
            "--name",
            "order_content",
            "--dir",
            str(directory),
            "--figma-url",
            "https://www.figma.com/design/example?node-id=1",
            "--figma-frame",
            "Order content",
        ]
        if not page:
            command.append("--component-only")
            requested = extra or []
            if "--mode" in requested and requested[requested.index("--mode") + 1] in {
                "api",
                "bff-json",
            }:
                command.extend(["--state-owner", "component"])
        else:
            command.extend(["--route", "/orders/:orderId"])
        command.extend(extra or [])
        subprocess.run(command, check=True, capture_output=True, text=True)
        return directory / "order_content.dart"

    def approve(self, component: Path) -> None:
        contract = component.with_name("order_content.c.dart")
        contract.write_text(
            contract.read_text(encoding="utf-8")
            .replace(
                "/// Widget Tree: [OrderContentView] > "
                "TODO: list key widgets before approval\n",
                "/// Widget Tree: [OrderContentView] > [OrderList], "
                "[OrderPrimaryButton]\n",
            )
            .replace(
                "/// - TODO: declare the cross-route capability owned by this component.\n",
                "/// - Order content presentation and refresh.\n",
            )
            .replace(
                "/// - [OrderContentView] — TODO: describe this reusable entry.\n",
                "/// - [OrderContentView] — reusable order content.\n",
            )
            .replace("pendingRequestField", "orderId")
            .replace("pendingResponseField", "orderStatus")
            .replace(
                "/// <PENDING_METHOD> <PENDING_PATH>",
                "/// GET /orders/:orderId",
            )
            .replace("<PENDING_UI_DATA>", "order status")
            .replace("<PENDING_DATA_SOURCE>", "order service")
            .replace(
                "<PENDING_LOADING_REFRESH>",
                "show loading before the request and support explicit refresh",
            )
            .replace(
                "<PENDING_EMPTY_ERROR>",
                "missing order is empty; service failure is blocking",
            )
            .replace(
                "/// - Effect: <PENDING_EFFECT>\n"
                "/// - Success: <PENDING_SUCCESS>\n"
                "/// - Failure: <PENDING_ERROR> -> <PENDING_RECOVERY>\n"
                "/// - Navigation: <PENDING_NAVIGATION>\n",
                "",
            )
            .replace("<PENDING_SOURCE>", "OrderContentView.orderId")
            .replace("<PENDING_PURPOSE>", "selects the order to load"),
            encoding="utf-8",
        )

    def test_page_aggregates_sibling_component(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            page = parse_page(component.with_name("order_content.page.dart"))
            self.assertEqual(page.primary_view, "OrderContentView")
            self.assertEqual(page.page_class, "OrderContentPage")
            self.assertEqual(page.page_classes, ["OrderContentPage"])
            self.assertEqual(
                page.routes, {"OrderContentPage": "/orders/:orderId"}
            )
            self.assertEqual(page.component.events, ["OrderContentStarted"])

            page_source = component.with_name("order_content.page.dart").read_text(
                encoding="utf-8"
            )
            contract_source = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )
            view_source = component.with_name("order_content.v.dart").read_text(
                encoding="utf-8"
            )
            self.assertIn("@TypedGoRoute<OrderContentPage>", page_source)
            self.assertIn(
                "class OrderContentPage extends GoRouteData with $OrderContentPage",
                page_source,
            )
            self.assertIn("part 'order_content.page.g.dart';", page_source)
            self.assertIn(
                "@TypedGoRoute<OrderContentPage>(path: '/orders/:orderId')",
                page_source,
            )
            self.assertIn(
                "FrProvider((context) => OrderContentViewModel()", page_source
            )
            self.assertIn("const OrderContentView()", page_source)
            self.assertNotIn("FrProvider", contract_source)
            self.assertNotIn("class OrderContentView", contract_source)
            self.assertIn("class OrderContentView", view_source)
            self.assertLess(
                contract_source.index("/// Figma:"),
                contract_source.index("part of 'order_content.dart';"),
            )
            self.assertIn(
                "/// State Ownership: page-owned [OrderContentViewModel]",
                contract_source,
            )
            self.assertNotIn("/// Route:", page_source)
            self.assertNotIn("/// Component:", page_source)
            self.assertNotIn("PageArgs", page_source)
            self.assertNotIn("class OrderContentArgs", contract_source)
            self.assertNotIn("PageArgs", contract_source)

            result = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "read_contract.py"),
                    "--page-file",
                    str(component.with_name("order_content.page.dart")),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn(
                "route.OrderContentPage: /orders/:orderId", result.stdout
            )
            self.assertIn("primary_view: OrderContentView", result.stdout)

    def test_draft_marks_widget_tree_incomplete_without_view_body(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            contract = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )

        self.assertIn(
            "/// Widget Tree: [OrderContentView] > "
            "TODO: list key widgets before approval",
            contract,
        )
        self.assertNotIn(
            "Widget Tree: [OrderContentView] > [_OrderContentViewBody]", contract
        )

    def test_read_contract_preserves_multiline_widget_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "/// Widget Tree: [OrderContentView] > "
                    "TODO: list key widgets before approval\n",
                    "/// Widget Tree: [OrderContentView] > [OrderMobileShell] >\n"
                    "///   [Text] title,\n"
                    "///   [OrderTextField],\n"
                    "///   [OrderPrimaryButton]\n",
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "read_contract.py"),
                    "--component-file",
                    str(component),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn(
            "section.Widget Tree: [OrderContentView] > [OrderMobileShell] > | "
            "[Text] title, | [OrderTextField], | [OrderPrimaryButton]",
            result.stdout,
        )

    def test_parser_and_reader_expose_required_service(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(
                Path(temporary), page=False, extra=["--mode", "bff-json"]
            )
            self.approve(component)
            parsed = parse_component(component)
            result = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "read_contract.py"),
                    "--component-file",
                    str(component),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual(parsed.api_kind, "query")
        self.assertEqual(parsed.bff_service, "[OrderContentService]")
        self.assertIn("api.kind: query", result.stdout)
        self.assertNotIn("bff.runtime:", result.stdout)
        self.assertIn("bff.service: [OrderContentService]", result.stdout)

    def test_draft_declares_json_serializable_part_for_fr_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(
                Path(temporary), page=False, extra=["--mode", "bff-json"]
            )
            source = component.read_text(encoding="utf-8")
            contract = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )

            self.assertIn("@FrState", contract)
            self.assertIn("part 'order_content.freezed.dart';", source)
            self.assertIn("part 'order_content.g.dart';", source)
            self.assertNotIn(
                "Map<String, dynamic> _$OrderContentModelToJson", source + contract
            )

    def test_component_default_is_local_without_redundant_vm_or_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            source = component.read_text(encoding="utf-8")
            contract = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )

            self.assertIn("/// State Ownership: none", contract)
            self.assertNotIn("FrProvider", contract)
            self.assertNotIn("ViewModels:", contract)
            self.assertNotIn("Models:", contract)
            self.assertNotIn("BFF-API:", contract)
            self.assertNotIn("package:flowr", source)
            self.assertNotIn("package:fr_acdd", source)
            self.assertNotIn("order_content.vm.dart", source)
            self.assertNotIn("order_content.freezed.dart", source)
            self.assertNotIn("order_content.g.dart", source)
            self.assertFalse(component.with_suffix(".bff.md").exists())
            self.approve(component)
            validated = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "validate_contract.py"),
                    "--component-file",
                    str(component),
                    "--phase",
                    "contract",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_app_owned_component_consumes_global_vm_without_local_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(
                Path(temporary),
                page=False,
                extra=[
                    "--state-owner",
                    "app",
                    "--state-type",
                    "AppLocaleViewModel",
                ],
            )
            source = component.read_text(encoding="utf-8")
            contract = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )
            parsed = parse_component(component)

        self.assertEqual(parsed.state_ownership, "app-owned")
        self.assertEqual(parsed.state_view_model, "AppLocaleViewModel")
        self.assertEqual(parsed.view_models, ["AppLocaleViewModel"])
        self.assertIn(
            "/// State Ownership: app-owned [AppLocaleViewModel]", contract
        )
        self.assertNotIn("FrProvider", contract)
        self.assertNotIn("order_content.vm.dart", source)
        self.assertNotIn("\n/// Models:", contract)
        self.assertNotIn("\n/// Events:", contract)

    def test_component_api_state_requires_explicit_component_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "draft_contract.py"),
                    "--name",
                    "order_content",
                    "--dir",
                    str(directory),
                    "--figma-url",
                    "https://example.com",
                    "--figma-frame",
                    "Order content",
                    "--mode",
                    "api",
                    "--api",
                    "GET /orders/:id",
                    "--component-only",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("--state-owner component", result.stderr)

    def test_api_mode_has_no_bff_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "draft_contract.py"),
                    "--name",
                    "order_content",
                    "--dir",
                    str(directory),
                    "--figma-url",
                    "https://example.com",
                    "--figma-frame",
                    "Order content",
                    "--mode",
                    "api",
                    "--api",
                    "GET /orders/:id",
                    "--component-only",
                    "--state-owner",
                    "component",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            source = (directory / "order_content.dart").read_text(encoding="utf-8")
            contract = (directory / "order_content.c.dart").read_text(encoding="utf-8")

            self.assertEqual(result.stderr, "")
            self.assertIn("/// API: GET /orders/:id", contract)
            self.assertNotIn("BFF Service:", contract)
            self.assertNotIn("FrAcdd", source + contract)

    def test_legacy_bff_api_flag_remains_deprecated_compatibility_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "draft_contract.py"),
                    "--name",
                    "order_content",
                    "--dir",
                    str(directory),
                    "--figma-url",
                    "https://example.com",
                    "--figma-frame",
                    "Order content",
                    "--api",
                    "BFF-JSON",
                    "--component-only",
                    "--state-owner",
                    "component",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("deprecated", result.stderr)
            self.assertIn(
                "FrAcddMode.bff",
                (directory / "order_content.v.dart").read_text(encoding="utf-8"),
            )

    def test_component_survives_page_adapter_removal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            component.with_name("order_content.page.dart").unlink()
            parsed = parse_component(component)
            self.assertEqual(parsed.view, "OrderContentView")

    def test_cross_route_component_can_be_drafted_under_components(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "lib/components/order_content"
            component = self.draft(directory, page=False)
            parsed = parse_component(component)
            contract = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )

            self.assertEqual(parsed.view, "OrderContentView")
            self.assertIn("/// Capabilities:", contract)
            self.assertIn("/// Public Views:", contract)
            self.assertEqual(
                parsed.sections["Public Views"],
                ["- [OrderContentView] — TODO: describe this reusable entry."],
            )
            self.assertFalse(component.with_name("order_content.page.dart").exists())

    def test_component_public_views_are_declared_in_contract_and_implemented_in_view_part(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            self.approve(component)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8")
                .replace(
                    "/// - [OrderContentView] — reusable order content.\n",
                    "/// - [OnboardingLanguageSwitchView] — onboarding entry.\n"
                    "/// - [CustomerOnboardingLanguageSwitchView] — customer entry.\n",
                )
                .replace(
                    "/// Widget Tree: [OrderContentView] > [OrderList], "
                    "[OrderPrimaryButton]\n",
                    "/// Widget Tree:\n"
                    "/// - [OnboardingLanguageSwitchView] > [LanguageSegment]\n"
                    "/// - [CustomerOnboardingLanguageSwitchView] > "
                    "[LanguageSegment]\n",
                ),
                encoding="utf-8",
            )
            view = component.with_name("order_content.v.dart")
            view.write_text(
                view.read_text(encoding="utf-8").replace(
                    "OrderContentView", "OnboardingLanguageSwitchView"
                )
                + "\nclass CustomerOnboardingLanguageSwitchView "
                "extends StatelessWidget {\n"
                "  const CustomerOnboardingLanguageSwitchView({super.key});\n"
                "  Widget build(BuildContext context) => const SizedBox.shrink();\n"
                "}\n",
                encoding="utf-8",
            )

            parsed = parse_component(component)
            self.assertEqual(
                parsed.views,
                [
                    "OnboardingLanguageSwitchView",
                    "CustomerOnboardingLanguageSwitchView",
                ],
            )
            validate_widget_tree(parsed)

    def test_draft_rejects_different_module_in_same_leaf_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.draft(directory)
            result = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "draft_contract.py"),
                    "--name",
                    "invoice_content",
                    "--dir",
                    str(directory),
                    "--figma-url",
                    "https://www.figma.com/design/example?node-id=2",
                    "--figma-frame",
                    "Invoice content",
                    "--component-only",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("must own its leaf directory", result.stderr)
            self.assertIn("`order_content`", result.stderr)
            self.assertFalse((directory / "invoice_content.dart").exists())
            self.assertFalse((directory / "invoice_content.c.dart").exists())

    def test_page_requires_build_to_directly_construct_view(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            page = component.with_name("order_content.page.dart")
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    "const OrderContentView()", "const SizedBox()"
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "construct one primary"):
                parse_page(page)

    def test_page_requires_literal_route_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            page = component.with_name("order_content.page.dart")
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    "path: '/orders/:orderId'", "path: routePath"
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "string-literal path"):
                parse_page(page)

    def test_page_requires_typed_route_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            page = component.with_name("order_content.page.dart")
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    "extends GoRouteData with $OrderContentPage",
                    "extends StatelessWidget",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "extends GoRouteData"):
                parse_page(page)

    def test_page_allows_typed_variants_for_the_same_view(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            page = component.with_name("order_content.page.dart")
            page.write_text(
                page.read_text(encoding="utf-8")
                + "\n"
                + "@TypedGoRoute<ArchivedOrderContentPage>("
                + "path: '/archived-orders')\n"
                + "class ArchivedOrderContentPage extends GoRouteData "
                + "with $ArchivedOrderContentPage {\n"
                + "  const ArchivedOrderContentPage();\n"
                + "  Widget build(BuildContext context, GoRouterState state) "
                + "=> const OrderContentView();\n"
                + "}\n",
                encoding="utf-8",
            )
            parsed = parse_page(page)

        self.assertEqual(
            parsed.page_classes,
            ["OrderContentPage", "ArchivedOrderContentPage"],
        )
        self.assertEqual(
            parsed.routes,
            {
                "OrderContentPage": "/orders/:orderId",
                "ArchivedOrderContentPage": "/archived-orders",
            },
        )

    def test_page_variants_must_directly_build_same_view(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            page = component.with_name("order_content.page.dart")
            page.write_text(
                page.read_text(encoding="utf-8")
                + "\n@TypedGoRoute<ArchivedOrderContentPage>("
                + "path: '/archived-orders')\n"
                + "class ArchivedOrderContentPage extends GoRouteData "
                + "with $ArchivedOrderContentPage {\n"
                + "  const ArchivedOrderContentPage();\n"
                + "  Widget build(BuildContext context, GoRouterState state) "
                + "=> const ArchivedOrderContentView();\n"
                + "}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "one shared primary View"):
                parse_page(page)

    def test_component_part_rejects_import(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                "import 'bad.dart';\n" + contract.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "must not declare"):
                parse_component(component)

    def test_component_contract_rejects_page_args_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8")
                + "\nclass OrderContentPageArgs {}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, r"must not declare \*PageArgs"):
                parse_component(component)

    def test_component_contract_rejects_input_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8") + "\nclass OrderContentArgs {}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ContractError, "ordinary View constructor fields"
            ):
                parse_component(component)

    def test_structured_theme_is_exposed_by_parser(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(
                Path(temporary),
                page=False,
                extra=[
                    "--mode",
                    "api",
                    "--api",
                    "GET /orders",
                    "--theme",
                    "component",
                    "--theme-type",
                    "OrderContentTheme",
                ],
            )
            parsed = parse_component(component)
            contract = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )

        self.assertEqual(parsed.theme_mode, "fr-mvvm-theme")
        self.assertEqual(parsed.theme_type, "OrderContentTheme")
        self.assertEqual(parsed.theme_ownership, "component")
        self.assertIsNone(parsed.theme_warning)
        self.assertIn("/// Theme: component [OrderContentTheme]", contract)
        self.assertNotIn("Theme Ownership", contract)

    def test_separate_theme_ownership_is_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "/// Theme: none",
                    "/// Theme: fr-mvvm-theme [OrderContentTheme]\n"
                    "/// Theme Ownership: component",
                ),
                encoding="utf-8",
            )
            parsed = parse_component(component)
            result = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "read_contract.py"),
                    "--component-file",
                    str(component),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual(parsed.theme_mode, "legacy")
        self.assertIsNone(parsed.theme_ownership)
        self.assertIn("separate `Theme Ownership`", parsed.theme_warning or "")
        self.assertIn("theme.type: unavailable (legacy)", result.stdout)
        self.assertIn("theme.ownership: unavailable (legacy)", result.stdout)

    def test_legacy_theme_is_readable_with_migration_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "/// Theme: none", "/// Theme: [OrderContentColors]"
                ),
                encoding="utf-8",
            )
            parsed = parse_component(component)

        self.assertEqual(parsed.theme_mode, "legacy")
        self.assertIn("migrate", parsed.theme_warning or "")

    def test_component_theme_generation_adds_one_theme_part(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pubspec.yaml").write_text(
                "name: fixture\n"
                "dependencies:\n"
                "  fr_mvvm_theme: any\n"
                "  json_annotation: any\n"
                "dev_dependencies:\n"
                "  json_serializable: any\n",
                encoding="utf-8",
            )
            component = self.draft(
                root / "lib/components/order_content",
                page=False,
                extra=[
                    "--mode",
                    "api",
                    "--api",
                    "GET /orders",
                    "--theme",
                    "component",
                    "--theme-type",
                    "OrderContentTheme",
                ],
            )
            self.approve(component)
            command = [
                *UV_RUN_SCRIPT,
                str(SCRIPTS / "generate_from_contract.py"),
                "--component-file",
                str(component),
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            subprocess.run(command, check=True, capture_output=True, text=True)
            shell = component.read_text(encoding="utf-8")
            theme = component.with_name("order_content.thm.dart")
            theme_source = theme.read_text(encoding="utf-8")

        self.assertEqual(shell.count("part 'order_content.thm.dart';"), 1)
        self.assertIn(
            "class OrderContentTheme extends FrPageTheme<OrderContentTheme>",
            theme_source,
        )

    def test_app_shared_theme_generation_registers_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pubspec.yaml").write_text(
                "name: fixture\n"
                "dependencies:\n"
                "  fr_mvvm_theme: any\n"
                "  json_annotation: any\n"
                "dev_dependencies:\n"
                "  json_serializable: any\n",
                encoding="utf-8",
            )
            core = root / "lib/core"
            core.mkdir(parents=True)
            app_theme = core / "app_theme.dart"
            app_theme.write_text(
                "import 'package:fr_mvvm_theme/fr_mvvm_theme.dart';\n"
                "class AppThemeModel extends FrThemeModel {\n"
                "  AppThemeModel({required super.themeId, required this.seedColor});\n"
                "  final Object seedColor;\n"
                "  @override\n"
                "  Map<String, dynamic> toJson() => {'seedColor': seedColor};\n"
                "}\n"
                "final builtIn = AppThemeModel(themeId: 'built_in', seedColor: 1);\n",
                encoding="utf-8",
            )
            component = self.draft(
                root / "lib/app/order_content",
                page=False,
                extra=[
                    "--mode",
                    "api",
                    "--api",
                    "GET /orders",
                    "--theme",
                    "app-shared",
                    "--theme-type",
                    "OnboardingTheme",
                ],
            )
            self.approve(component)
            command = [
                *UV_RUN_SCRIPT,
                str(SCRIPTS / "generate_from_contract.py"),
                "--component-file",
                str(component),
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            subprocess.run(command, check=True, capture_output=True, text=True)
            source = app_theme.read_text(encoding="utf-8")

        self.assertEqual(source.count("final OnboardingTheme onboarding;"), 1)
        self.assertEqual(source.count("'onboarding': onboarding"), 1)
        self.assertEqual(source.count("onboarding: const OnboardingTheme()"), 1)
        self.assertIn("required this.onboarding}", source)
        self.assertNotIn("}, required this.onboarding", source)
        self.assertIn("seedColor: 1, onboarding: const OnboardingTheme()", source)

    def test_theme_preflight_failure_leaves_component_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pubspec.yaml").write_text(
                "name: fixture\n"
                "dependencies:\n"
                "  fr_mvvm_theme: any\n"
                "  json_annotation: any\n"
                "dev_dependencies:\n"
                "  json_serializable: any\n",
                encoding="utf-8",
            )
            core = root / "lib/core"
            core.mkdir(parents=True)
            (core / "app_theme.dart").write_text(
                "class InvalidThemeRegistry {}\n", encoding="utf-8"
            )
            component = self.draft(
                root / "lib/app/order_content",
                page=False,
                extra=[
                    "--mode",
                    "api",
                    "--api",
                    "GET /orders",
                    "--theme",
                    "app-shared",
                    "--theme-type",
                    "OnboardingTheme",
                ],
            )
            self.approve(component)
            original_shell = component.read_text(encoding="utf-8")
            view = component.with_name("order_content.v.dart")
            original_view = view.read_text(encoding="utf-8")
            result = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "generate_from_contract.py"),
                    "--component-file",
                    str(component),
                    "--write-stubs",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("AppThemeModel", result.stderr)
            self.assertEqual(component.read_text(encoding="utf-8"), original_shell)
            self.assertEqual(view.read_text(encoding="utf-8"), original_view)
            self.assertFalse(component.with_name("order_content.vm.dart").exists())
            self.assertFalse((core / "onboarding_theme.dart").exists())

    def test_force_never_replaces_an_implemented_derived_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "pubspec.yaml").write_text(
                "name: fixture\n"
                "dependencies:\n"
                "  json_annotation: any\n"
                "dev_dependencies:\n"
                "  json_serializable: any\n",
                encoding="utf-8",
            )
            component = self.draft(
                root / "lib/components/order_content",
                page=False,
                extra=["--mode", "api", "--api", "GET /orders"],
            )
            self.approve(component)
            view = component.with_name("order_content.v.dart")
            view.write_text(
                view.read_text(encoding="utf-8").replace(
                    "// Implement this derived file from read_contract.py output.",
                    "// Implemented View.",
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "generate_from_contract.py"),
                    "--component-file",
                    str(component),
                    "--write-stubs",
                    "--force",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("refusing to replace implemented", result.stderr)
            self.assertIn("Implemented View", view.read_text(encoding="utf-8"))
            self.assertFalse(component.with_name("order_content.vm.dart").exists())

    def test_file_set_commit_rolls_back_after_a_write_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            existing = root / "existing.dart"
            created = root / "created.dart"
            existing.write_text("original\n", encoding="utf-8")
            existing.chmod(0o640)
            original_atomic_write = generator.atomic_write
            failed = False

            def flaky_write(path: Path, content: bytes) -> None:
                nonlocal failed
                if path == created and not failed:
                    failed = True
                    raise OSError("simulated commit failure")
                original_atomic_write(path, content)

            with mock.patch.object(generator, "atomic_write", side_effect=flaky_write):
                with self.assertRaisesRegex(
                    ContractError, "original files were restored"
                ):
                    generator.apply_updates({existing: b"changed\n", created: b"new\n"})

            self.assertEqual(existing.read_text(encoding="utf-8"), "original\n")
            self.assertEqual(existing.stat().st_mode & 0o777, 0o640)
            self.assertFalse(created.exists())


if __name__ == "__main__":
    unittest.main()

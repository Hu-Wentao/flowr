from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1]
for path in (SCRIPTS,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from contract_core import ContractError  # noqa: E402
from contract_parser import parse_component, parse_page  # noqa: E402
import generate_from_contract as generator  # noqa: E402


class ContractRuntimeTest(unittest.TestCase):
    def draft(
        self, directory: Path, *, page: bool = True, extra: list[str] | None = None
    ) -> Path:
        command = [
            sys.executable,
            str(SCRIPTS / "draft_contract.py"),
            "--name",
            "order_content",
            "--dir",
            str(directory),
            "--figma-url",
            "https://www.figma.com/design/example?node-id=1",
        ]
        if not page:
            command.append("--component-only")
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
            .replace("pendingRequestField", "orderId")
            .replace("pendingResponseField", "orderStatus")
            .replace("/// API Type: <PENDING_API_TYPE>", "/// API Type: data")
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
                "/// Business:\n"
                "/// - Goal: <PENDING_GOAL>\n"
                "/// - Upstream Proof: <PENDING_UPSTREAM_PROOF>\n"
                "/// - Effect: <PENDING_EFFECT>\n"
                "/// - Success Condition: <PENDING_SUCCESS_CONDITION>\n"
                "/// - Failure Cases: <PENDING_ERROR> -> <PENDING_RECOVERY>\n"
                "/// - Navigation Ownership: <PENDING_NAVIGATION_OWNERSHIP>\n",
                "",
            )
            .replace("<PENDING_SOURCE>", "OrderContentView.orderId")
            .replace("<PENDING_PURPOSE>", "selects the order to load")
            .replace("/// BFF Service: <PENDING_SERVICE>\n", ""),
            encoding="utf-8",
        )

    def test_page_aggregates_sibling_component(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            page = parse_page(component.with_name("order_content.page.dart"))
            self.assertEqual(page.primary_view, "OrderContentView")
            self.assertEqual(page.page_args, "OrderContentPageArgs")
            self.assertEqual(page.component.events, ["OrderContentStarted"])

            page_source = component.with_name("order_content.page.dart").read_text(
                encoding="utf-8"
            )
            contract_source = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )
            self.assertIn("class OrderContentPageArgs", page_source)
            self.assertIn("const OrderContentView()", page_source)
            self.assertNotIn("class OrderContentArgs", contract_source)
            self.assertNotIn("PageArgs", contract_source)

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
                    sys.executable,
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

    def test_parser_and_reader_expose_api_and_omitted_service(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            self.approve(component)
            parsed = parse_component(component)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "read_contract.py"),
                    "--component-file",
                    str(component),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual(parsed.api_type, "data")
        self.assertIsNone(parsed.bff_service)
        self.assertIn("api.type: data", result.stdout)
        self.assertNotIn("bff.runtime:", result.stdout)
        self.assertIn("bff.service: not declared", result.stdout)

    def test_draft_declares_json_serializable_part_for_fr_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
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

    def test_default_mode_drafts_required_bff_contract_without_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            source = component.read_text(encoding="utf-8")
            contract = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )

            self.assertIn("package:fr_acdd/fr_acdd.dart", source)
            self.assertIn("@FrAcddPage(", contract)
            self.assertIn("mode: FrAcddMode.bff", contract)
            self.assertIn("@FrAcddDto(kind: FrAcddDtoKind.root)", contract)
            self.assertIn("@FrAcddFreezedJSON", contract)
            self.assertIn("/// API Type: <PENDING_API_TYPE>", contract)
            self.assertIn("/// <PENDING_METHOD> <PENDING_PATH>", contract)
            self.assertNotIn("BFF Runtime:", contract)
            self.assertIn("/// BFF Service: <PENDING_SERVICE>", contract)
            self.assertNotIn("/bootstrap", contract)
            self.assertFalse(component.with_suffix(".bff.md").exists())

    def test_api_mode_has_no_bff_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "draft_contract.py"),
                    "--name",
                    "order_content",
                    "--dir",
                    str(directory),
                    "--figma-url",
                    "https://example.com",
                    "--mode",
                    "api",
                    "--api",
                    "GET /orders/:id",
                    "--component-only",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            source = (directory / "order_content.dart").read_text(encoding="utf-8")
            contract = (directory / "order_content.c.dart").read_text(encoding="utf-8")

            self.assertEqual(result.stderr, "")
            self.assertIn("/// API: GET /orders/:id", contract)
            self.assertNotIn("FrAcdd", source + contract)

    def test_legacy_bff_api_flag_remains_deprecated_compatibility_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "draft_contract.py"),
                    "--name",
                    "order_content",
                    "--dir",
                    str(directory),
                    "--figma-url",
                    "https://example.com",
                    "--api",
                    "BFF-JSON",
                    "--component-only",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("deprecated", result.stderr)
            self.assertIn(
                "FrAcddMode.bff",
                (directory / "order_content.c.dart").read_text(encoding="utf-8"),
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
            self.assertIn("lib/components for cross-route reuse", contract)
            self.assertEqual(
                parsed.sections["Shared Widgets"],
                ["review route widgets and lib/widgets before implementation."],
            )
            self.assertFalse(component.with_name("order_content.page.dart").exists())

    def test_page_requires_explicit_primary_view_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            page = component.with_name("order_content.page.dart")
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    "/// Component: [OrderContentView]\n", ""
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "Component"):
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
                    "fr-mvvm-theme",
                    "--theme-type",
                    "OrderContentTheme",
                    "--theme-owner",
                    "component",
                ],
            )
            parsed = parse_component(component)

        self.assertEqual(parsed.theme_mode, "fr-mvvm-theme")
        self.assertEqual(parsed.theme_type, "OrderContentTheme")
        self.assertEqual(parsed.theme_ownership, "component")
        self.assertIsNone(parsed.theme_warning)

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
                    "fr-mvvm-theme",
                    "--theme-type",
                    "OrderContentTheme",
                    "--theme-owner",
                    "component",
                ],
            )
            self.approve(component)
            command = [
                sys.executable,
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
                    "fr-mvvm-theme",
                    "--theme-type",
                    "OnboardingTheme",
                    "--theme-owner",
                    "app-shared",
                ],
            )
            self.approve(component)
            command = [
                sys.executable,
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
                    "fr-mvvm-theme",
                    "--theme-type",
                    "OnboardingTheme",
                    "--theme-owner",
                    "app-shared",
                ],
            )
            self.approve(component)
            original_shell = component.read_text(encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
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
            self.assertFalse(component.with_name("order_content.v.dart").exists())
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
                "part of 'order_content.dart';\n\nclass _ImplementedView {}\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
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
            self.assertIn("_ImplementedView", view.read_text(encoding="utf-8"))
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

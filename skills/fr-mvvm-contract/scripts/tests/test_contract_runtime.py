from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
for path in (SCRIPTS,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from contract_core import ContractError  # noqa: E402
from contract_parser import parse_component, parse_page  # noqa: E402


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

    def test_page_aggregates_sibling_component(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            page = parse_page(component.with_name("order_content.page.dart"))
            self.assertEqual(page.primary_view, "OrderContentView")
            self.assertEqual(page.page_args, "OrderContentPageArgs")
            self.assertEqual(page.component.component_input, "OrderContentArgs")
            self.assertEqual(page.component.events, ["OrderContentStarted"])

            page_source = component.with_name("order_content.page.dart").read_text(
                encoding="utf-8"
            )
            contract_source = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )
            self.assertIn("class OrderContentPageArgs", page_source)
            self.assertIn("OrderContentArgs()", page_source)
            self.assertIn("class OrderContentArgs", contract_source)
            self.assertNotIn("PageArgs", contract_source)

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
            self.assertNotRegex(source + contract, r"_\$\w+(?:ToJson|FromJson)\s*\(")

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
                contract.read_text(encoding="utf-8").replace(
                    "OrderContentArgs", "OrderContentPageArgs"
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, r"must not declare \*PageArgs"):
                parse_component(component)

    def test_structured_theme_is_exposed_by_parser(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(
                Path(temporary),
                page=False,
                extra=[
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
                "name: fixture\ndependencies:\n  fr_mvvm_theme: any\n",
                encoding="utf-8",
            )
            component = self.draft(
                root / "lib/components/order_content",
                page=False,
                extra=[
                    "--theme",
                    "fr-mvvm-theme",
                    "--theme-type",
                    "OrderContentTheme",
                    "--theme-owner",
                    "component",
                ],
            )
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
                "name: fixture\ndependencies:\n  fr_mvvm_theme: any\n",
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
                    "--theme",
                    "fr-mvvm-theme",
                    "--theme-type",
                    "OnboardingTheme",
                    "--theme-owner",
                    "app-shared",
                ],
            )
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
        self.assertIn(
            "seedColor: 1, onboarding: const OnboardingTheme()", source
        )


if __name__ == "__main__":
    unittest.main()

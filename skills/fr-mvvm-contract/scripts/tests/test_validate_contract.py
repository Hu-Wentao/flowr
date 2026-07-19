#!/usr/bin/env python3
"""Regression tests for generated JSON contract validation."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
VALIDATOR = SCRIPTS / "validate_contract.py"


class ValidateContractTest(unittest.TestCase):
    def write_fixture(
        self,
        root: Path,
        *,
        annotation: str = "FrState",
        include_g_part: bool = True,
        include_json_annotation: bool = True,
        include_json_serializable: bool = True,
        handwritten_suffix: str | None = None,
        handwritten_body: str = (
            "Map<String, dynamic> _$OrderContentModelToJson(\n"
            "  OrderContentModel instance,\n"
            ") => <String, dynamic>{};\n"
        ),
    ) -> Path:
        dev_dependencies = (
            "  json_serializable: any\n" if include_json_serializable else ""
        )
        (root / "pubspec.yaml").write_text(
            "name: validator_fixture\n"
            "environment:\n"
            "  sdk: ^3.7.0\n"
            "dependencies:\n"
            + ("  json_annotation: any\n" if include_json_annotation else "")
            + "dev_dependencies:\n"
            f"{dev_dependencies}",
            encoding="utf-8",
        )
        source_dir = root / "lib/order_content"
        source_dir.mkdir(parents=True)
        component = source_dir / "order_content.dart"
        g_part = "part 'order_content.g.dart';\n" if include_g_part else ""
        component.write_text(
            "part 'order_content.c.dart';\n"
            "part 'order_content.v.dart';\n"
            "part 'order_content.vm.dart';\n"
            "part 'order_content.freezed.dart';\n"
            f"{g_part}",
            encoding="utf-8",
        )
        (source_dir / "order_content.c.dart").write_text(
            "part of 'order_content.dart';\n\n"
            "/// Widget Tree: [OrderContentView] > [Text] title,\n"
            "///   [OrderTextField], [OrderPrimaryButton]\n"
            "/// Theme: none\n"
            "/// Events: [OrderContentStarted]\n"
            "/// ViewModels: [OrderContentViewModel]\n"
            "/// Models: [OrderContentModel]\n"
            "/// API Type: data\n"
            "/// API: GET /order-content\n"
            "/// Data:\n"
            "/// - UI Data: order content\n"
            "/// - Source: order service\n"
            "/// - Loading/Refresh: show loading and support explicit refresh\n"
            "/// - Empty/Error: missing order is empty; service failure is blocking\n"
            "class OrderContentView {\n"
            "  Object build() => FrProvider;\n"
            "}\n\n"
            f"@{annotation}\n"
            "class OrderContentModel {}\n",
            encoding="utf-8",
        )
        for suffix in ("v", "vm"):
            body = handwritten_body if handwritten_suffix == suffix else ""
            (source_dir / f"order_content.{suffix}.dart").write_text(
                "part of 'order_content.dart';\n" + body,
                encoding="utf-8",
            )
        if handwritten_suffix in {"c", "srv"}:
            target = source_dir / f"order_content.{handwritten_suffix}.dart"
            if handwritten_suffix == "c":
                target.write_text(
                    target.read_text(encoding="utf-8") + handwritten_body,
                    encoding="utf-8",
                )
            else:
                target.write_text(
                    "part of 'order_content.dart';\n" + handwritten_body,
                    encoding="utf-8",
                )
        return component

    def validate(
        self, component: Path, *, phase: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(VALIDATOR),
            "--component-file",
            str(component),
        ]
        if phase:
            command.extend(["--phase", phase])
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

    def validate_page(
        self, page: Path, *, phase: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(VALIDATOR), "--page-file", str(page)]
        if phase:
            command.extend(["--phase", phase])
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_contract_sections_reject_block_comments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            contract = component.with_name("order_content.c.dart")
            source = contract.read_text(encoding="utf-8")
            start = source.index("/// Widget Tree:")
            end = source.index("class OrderContentView")
            block = source[start:end].replace("/// ", "")
            contract.write_text(
                source[:start] + "/*\n" + block + "*/\n" + source[end:],
                encoding="utf-8",
            )

            result = self.validate(component, phase="contract")

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("must use consecutive `///`", result.stderr)

    def write_page(self, component: Path, *, direct_passthrough: bool = False) -> Path:
        page = component.with_name("order_content.page.dart")
        view_args = "args: args" if direct_passthrough else "orderId: args.orderId"
        page.write_text(
            "import 'order_content.dart';\n"
            "/// Route: AppRoutes.orderContent\n"
            "/// Component: [OrderContentView]\n"
            "class OrderContentPageArgs {\n"
            "  const OrderContentPageArgs(this.orderId);\n"
            "  final String orderId;\n"
            "}\n"
            "class OrderContentPage {\n"
            "  const OrderContentPage(this.args);\n"
            "  final OrderContentPageArgs args;\n"
            f"  Object build() => OrderContentView({view_args});\n"
            "}\n",
            encoding="utf-8",
        )
        return page

    def test_fr_state_contract_with_g_part_and_dependency_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(self.write_fixture(Path(temporary)))

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_component_state_requires_model_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "OrderContentModel", "OrderContentState"
                ),
                encoding="utf-8",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("XxxModel suffix", result.stderr)

    def test_contract_phase_does_not_require_generated_parts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            result = self.validate(component, phase="contract")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("validation (contract): OK", result.stdout)

    def test_contract_phase_rejects_draft_field_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8")
                + "final pendingRequestField = 'TODO';\n",
                encoding="utf-8",
            )
            result = self.validate(component, phase="contract")

        self.assertEqual(result.returncode, 2)
        self.assertIn("draft placeholder `pendingRequestField`", result.stderr)

    def test_final_phase_requires_codegen_and_rejects_stubs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            missing = self.validate(component, phase="final")
            self.assertEqual(missing.returncode, 2)
            self.assertIn("order_content.freezed.dart", missing.stderr)

            for suffix in ("freezed", "g"):
                component.with_name(f"order_content.{suffix}.dart").write_text(
                    "part of 'order_content.dart';\n", encoding="utf-8"
                )
            view = component.with_name("order_content.v.dart")
            view.write_text(
                "part of 'order_content.dart';\n\n"
                "// Implement this derived file from read_contract.py output.\n",
                encoding="utf-8",
            )
            stub = self.validate(component, phase="final")
            self.assertEqual(stub.returncode, 2)
            self.assertIn("unfinished derived stub", stub.stderr)

            view.write_text(
                "part of 'order_content.dart';\nclass _OrderContentBody {}\n",
                encoding="utf-8",
            )
            complete = self.validate(component, phase="final")

        self.assertEqual(complete.returncode, 0, complete.stderr)
        self.assertIn("validation (final): OK", complete.stdout)

    def replace_widget_tree(self, component: Path, replacement: str | None) -> None:
        contract = component.with_name("order_content.c.dart")
        source = contract.read_text(encoding="utf-8")
        source = source.replace(
            "/// Widget Tree: [OrderContentView] > [Text] title,\n"
            "///   [OrderTextField], [OrderPrimaryButton]\n",
            replacement or "",
        )
        contract.write_text(source, encoding="utf-8")

    def test_widget_tree_accepts_key_widgets_and_semantic_annotations(self) -> None:
        trees = {
            "confirm-password": (
                "/// Widget Tree: [OrderContentView] > [OnboardingMobileShell] >\n"
                "///   [Text] title, [OnboardingTextField] confirm password,\n"
                "///   [Text] validation error (conditional),\n"
                "///   [OnboardingPrimaryButton] confirm\n"
            ),
            "login": (
                "/// Widget Tree: [OrderContentView] > [LoginShell] >\n"
                "///   [Text] title, [EmailTextField], [PasswordTextField],\n"
                "///   [LoginButton]\n"
            ),
            "verification-code": (
                "/// Widget Tree: [OrderContentView] > [VerificationShell] >\n"
                "///   [Text] instructions, [VerificationCodeField] × 6,\n"
                "///   [Text] validation error (conditional), [VerifyButton]\n"
            ),
            "home": (
                "/// Widget Tree: [OrderContentView] > [_HomeHeader],\n"
                "///   [AccountSummaryCard], [RecentActivityItem] × N,\n"
                "///   [EmptyState] when empty, [HomeActionMenu]\n"
            ),
        }
        for scenario, tree in trees.items():
            with self.subTest(scenario=scenario):
                with tempfile.TemporaryDirectory() as temporary:
                    component = self.write_fixture(Path(temporary))
                    self.replace_widget_tree(component, tree)
                    result = self.validate(component)

                self.assertEqual(result.returncode, 0, result.stderr)

    def test_widget_tree_rejects_missing_section(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            self.replace_widget_tree(component, None)
            result = self.validate(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("must declare `Widget Tree:`", result.stderr)

    def test_widget_tree_rejects_wrong_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            self.replace_widget_tree(
                component,
                "/// Widget Tree: [OtherView] > [OrderTextField]\n",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("root must be", result.stderr)
        self.assertIn("[OrderContentView]", result.stderr)

    def test_widget_tree_rejects_todo_root_only_and_natural_language_summary(
        self,
    ) -> None:
        trees = (
            "/// Widget Tree: [OrderContentView] > TODO: list key widgets\n",
            "/// Widget Tree: [OrderContentView]\n",
            "/// Widget Tree: [OrderContentView] > confirmation form\n",
        )
        for tree in trees:
            with self.subTest(tree=tree):
                with tempfile.TemporaryDirectory() as temporary:
                    component = self.write_fixture(Path(temporary))
                    self.replace_widget_tree(component, tree)
                    result = self.validate(component)

                self.assertEqual(result.returncode, 2)
                self.assertIn("Widget Tree", result.stderr)

    def test_widget_tree_rejects_formulaic_view_body(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            self.replace_widget_tree(
                component,
                "/// Widget Tree: [OrderContentView] > [_OrderContentViewBody] >\n"
                "///   [OrderPrimaryButton]\n",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("_XxxViewBody", result.stderr)

    def test_widget_tree_rejects_wrappers_layout_glue_and_decorations(self) -> None:
        forbidden = (
            "FrProvider",
            "FrConsumer",
            "Builder",
            "Align",
            "DecoratedBox",
            "Expanded",
            "Flexible",
            "Padding",
            "SafeArea",
            "SizedBox",
            "Spacer",
            "Divider",
        )
        for widget in forbidden:
            with self.subTest(widget=widget):
                with tempfile.TemporaryDirectory() as temporary:
                    component = self.write_fixture(Path(temporary))
                    self.replace_widget_tree(
                        component,
                        f"/// Widget Tree: [OrderContentView] > [{widget}] > [OrderPrimaryButton]\n",
                    )
                    result = self.validate(component)

                self.assertEqual(result.returncode, 2)
                self.assertIn(widget, result.stderr)

    def test_widget_tree_leaves_ambiguous_layout_widgets_to_review(self) -> None:
        for widget in ("Row", "Column", "Stack", "Container"):
            with self.subTest(widget=widget):
                with tempfile.TemporaryDirectory() as temporary:
                    component = self.write_fixture(Path(temporary))
                    self.replace_widget_tree(
                        component,
                        f"/// Widget Tree: [OrderContentView] > [{widget}] > [OrderPrimaryButton]\n",
                    )
                    result = self.validate(component)

                self.assertEqual(result.returncode, 0, result.stderr)

    def test_widget_tree_rejects_more_than_twelve_key_widgets(self) -> None:
        widgets = ", ".join(f"[KeyWidget{index}]" for index in range(13))
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            self.replace_widget_tree(
                component,
                f"/// Widget Tree: [OrderContentView] > {widgets}\n",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("13 key Widget references", result.stderr)
        self.assertIn("at most 12", result.stderr)

    def test_fr_state_and_fr_state_json_require_g_part(self) -> None:
        for annotation in ("FrState", "FrStateJson"):
            with self.subTest(annotation=annotation):
                with tempfile.TemporaryDirectory() as temporary:
                    result = self.validate(
                        self.write_fixture(
                            Path(temporary),
                            annotation=annotation,
                            include_g_part=False,
                        )
                    )

                self.assertEqual(result.returncode, 2)
                self.assertIn("order_content.g.dart", result.stderr)
                self.assertIn("build_runner", result.stderr)

    def test_fr_state_requires_direct_json_serializable_dev_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(Path(temporary), include_json_serializable=False)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("json_serializable", result.stderr)
        self.assertIn("dev_dependencies", result.stderr)
        self.assertIn("build_runner", result.stderr)

    def test_fr_state_requires_direct_json_annotation_runtime_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.validate(
                self.write_fixture(Path(temporary), include_json_annotation=False)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("json_annotation", result.stderr)
        self.assertIn("dependencies", result.stderr)
        self.assertIn("runtime", result.stderr)

    def test_dev_dependency_does_not_satisfy_json_annotation_runtime_dependency(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.write_fixture(root, include_json_annotation=False)
            pubspec = root / "pubspec.yaml"
            pubspec.write_text(
                pubspec.read_text(encoding="utf-8") + "  json_annotation: any\n",
                encoding="utf-8",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("json_annotation", result.stderr)
        self.assertIn("must not be added with --dev", result.stderr)

    def test_runtime_dependency_does_not_satisfy_direct_dev_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.write_fixture(root, include_json_serializable=False)
            pubspec = root / "pubspec.yaml"
            pubspec.write_text(
                pubspec.read_text(encoding="utf-8")
                + "dependencies:\n  json_serializable: any\n",
                encoding="utf-8",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("dev_dependencies", result.stderr)

    def test_source_parts_must_not_define_generated_json_functions(self) -> None:
        bodies = {
            "ToJson": (
                "Map<String, dynamic> _$OrderContentModelToJson(\n"
                "  OrderContentModel instance,\n"
                ") => <String, dynamic>{};\n"
            ),
            "FromJson": (
                "OrderContentModel _$OrderContentModelFromJson(\n"
                "  Map<String, dynamic> json,\n"
                ") { return OrderContentModel(); }\n"
            ),
        }
        for suffix in ("c", "v", "vm", "srv"):
            for function_kind, body in bodies.items():
                with self.subTest(suffix=suffix, function_kind=function_kind):
                    with tempfile.TemporaryDirectory() as temporary:
                        result = self.validate(
                            self.write_fixture(
                                Path(temporary),
                                handwritten_suffix=suffix,
                                handwritten_body=body,
                            )
                        )

                    self.assertEqual(result.returncode, 2)
                    self.assertIn(f"order_content.{suffix}.dart", result.stderr)
                    self.assertIn(".g.dart", result.stderr)
                    self.assertIn("build_runner", result.stderr)
                    self.assertIn("must not be handwritten", result.stderr)

    def test_generated_json_function_call_is_not_mistaken_for_definition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            vm = component.with_name("order_content.vm.dart")
            vm.write_text(
                vm.read_text(encoding="utf-8")
                + "Map<String, dynamic> snapshot(OrderContentModel value) "
                "=> _$OrderContentModelToJson(value);\n",
                encoding="utf-8",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_component_parts_must_not_reference_page_args(self) -> None:
        for suffix in ("c", "v", "vm"):
            with self.subTest(suffix=suffix):
                with tempfile.TemporaryDirectory() as temporary:
                    component = self.write_fixture(Path(temporary))
                    target = component.with_name(f"order_content.{suffix}.dart")
                    target.write_text(
                        target.read_text(encoding="utf-8")
                        + "Object useRouteArgs(OrderContentPageArgs value) => value;\n",
                        encoding="utf-8",
                    )
                    result = self.validate(component)

                self.assertEqual(result.returncode, 2)
                self.assertIn("route-owned OrderContentPageArgs", result.stderr)

    def test_component_must_not_reference_page_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            vm = component.with_name("order_content.vm.dart")
            vm.write_text(
                vm.read_text(encoding="utf-8") + "// order_content.page.dart\n",
                encoding="utf-8",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("must not import or reference", result.stderr)

    def test_page_expands_page_args_into_view_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            result = self.validate_page(self.write_page(component))

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_page_must_not_pass_page_args_directly_to_view(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            result = self.validate_page(
                self.write_page(component, direct_passthrough=True)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("must convert route-owned OrderContentPageArgs", result.stderr)

    def test_page_must_convert_every_declared_page_arg_field(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            page = self.write_page(component)
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    "  final String orderId;\n",
                    "  final String orderId;\n  final String customerId;\n",
                ),
                encoding="utf-8",
            )
            result = self.validate_page(page, phase="contract")

        self.assertEqual(result.returncode, 2)
        self.assertIn("does not convert", result.stderr)
        self.assertIn("customerId", result.stderr)

    def test_legacy_free_text_theme_fails_strict_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "/// Theme: none", "/// Theme: [OrderContentColors]"
                ),
                encoding="utf-8",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("legacy Theme declaration", result.stderr)

    def test_material_theme_requires_color_scheme_and_no_theme_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "/// Theme: none", "/// Theme: material"
                ),
                encoding="utf-8",
            )
            view = component.with_name("order_content.v.dart")
            view.write_text(
                view.read_text(encoding="utf-8")
                + "Object colors(Object context) => Theme.of(context).colorScheme;\n",
                encoding="utf-8",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(component.with_name("order_content.thm.dart").exists())

    def configure_component_theme(self, root: Path, component: Path) -> None:
        pubspec = root / "pubspec.yaml"
        pubspec.write_text(
            pubspec.read_text(encoding="utf-8").replace(
                "dependencies:\n", "dependencies:\n  fr_mvvm_theme: any\n"
            ),
            encoding="utf-8",
        )
        contract = component.with_name("order_content.c.dart")
        contract.write_text(
            contract.read_text(encoding="utf-8").replace(
                "/// Theme: none",
                "/// Theme: fr-mvvm-theme [OrderContentTheme]\n"
                "/// Theme Ownership: component",
            ),
            encoding="utf-8",
        )
        component.write_text(
            component.read_text(encoding="utf-8") + "part 'order_content.thm.dart';\n",
            encoding="utf-8",
        )
        component.with_name("order_content.thm.dart").write_text(
            "part of 'order_content.dart';\n"
            "class OrderContentTheme extends FrPageTheme<OrderContentTheme> {}\n",
            encoding="utf-8",
        )
        view = component.with_name("order_content.v.dart")
        view.write_text(
            view.read_text(encoding="utf-8")
            + "Object active(Object context) => context.ofThm<OrderContentTheme>();\n",
            encoding="utf-8",
        )

    def test_component_fr_theme_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.write_fixture(root)
            self.configure_component_theme(root, component)
            result = self.validate(component)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_static_colors_fail_fr_theme_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.write_fixture(root)
            self.configure_component_theme(root, component)
            view = component.with_name("order_content.v.dart")
            view.write_text(
                view.read_text(encoding="utf-8")
                + "Object legacy() => OrderContentColors.primary;\n",
                encoding="utf-8",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("XxxColors", result.stderr)

    def test_app_shared_theme_rejects_empty_to_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.write_fixture(root)
            self.configure_component_theme(root, component)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8")
                .replace("OrderContentTheme", "OnboardingTheme")
                .replace("Theme Ownership: component", "Theme Ownership: app-shared"),
                encoding="utf-8",
            )
            view = component.with_name("order_content.v.dart")
            view.write_text(
                view.read_text(encoding="utf-8").replace(
                    "OrderContentTheme", "OnboardingTheme"
                ),
                encoding="utf-8",
            )
            core = root / "lib/core"
            core.mkdir()
            (core / "app_theme.dart").write_text(
                "class OnboardingTheme extends FrPageTheme<OnboardingTheme> {}\n"
                "class AppThemeModel extends FrThemeModel {\n"
                "  final OnboardingTheme onboarding;\n"
                "  Map<String, dynamic> toJson() => const {};\n"
                "}\n",
                encoding="utf-8",
            )
            (root / "lib/application.dart").write_text(
                "Object root(Object theme) => "
                "ThemeData(extensions: theme.data.extensions);\n",
                encoding="utf-8",
            )
            result = self.validate(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("toJson() must preserve onboarding", result.stderr)


if __name__ == "__main__":
    unittest.main()

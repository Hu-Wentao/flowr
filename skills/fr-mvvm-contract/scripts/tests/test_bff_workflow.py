#!/usr/bin/env python3
"""Regression coverage for the required BFF-JSON delivery loop."""

from __future__ import annotations

import os
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]


class BffWorkflowTest(unittest.TestCase):
    def write_pubspec(self, root: Path, *, fr_acdd: bool = True) -> None:
        (root / "pubspec.yaml").write_text(
            "name: bff_fixture\n"
            "environment:\n  sdk: ^3.7.0\n"
            "dependencies:\n" + ("  fr_acdd: any\n" if fr_acdd else "") + "  dio: any\n"
            "  efficient_dio_logger: any\n"
            "  retrofit: any\n" + "  json_annotation: any\n"
            "dev_dependencies:\n"
            "  build_runner: any\n"
            "  retrofit_generator: any\n"
            "  json_serializable: any\n",
            encoding="utf-8",
        )

    def draft(self, root: Path, *, page: bool, mode: str = "bff-json") -> Path:
        self.write_pubspec(root)
        directory = root / "lib/order_content"
        command = [
            sys.executable,
            str(SCRIPTS / "draft_contract.py"),
            "--name",
            "order_content",
            "--dir",
            str(directory),
            "--figma-url",
            "https://example.com/design",
            "--mode",
            mode,
        ]
        if mode == "api":
            command.extend(["--api", "GET /orders/:id"])
        if not page:
            command.append("--component-only")
        else:
            command.extend(["--route", "/orders/:orderId"])
        subprocess.run(command, check=True, capture_output=True, text=True)
        contract = directory / "order_content.c.dart"
        source = (
            contract.read_text(encoding="utf-8")
            .replace(
                "/// Widget Tree: [OrderContentView] > "
                "TODO: list key widgets before approval\n",
                "/// Widget Tree: [OrderContentView] > [OrderList], "
                "[OrderPrimaryButton]\n",
            )
            .replace(
                "/// Backend Calls:\n"
                "/// - pendingBackendCall <- <PENDING_OPENAPI_LOCATION>.openapi.json | "
                "<PENDING_METHOD> <PENDING_PATH>\n"
                "/// Backend Call Flow:\n"
                "/// - [pendingBackendCall] <PENDING_CALL_FLOW>\n",
                "/// Backend Calls:\n/// - none\n/// Backend Call Flow:\n/// - none\n",
            )
            .replace("pendingRequestField", "orderId")
            .replace("pendingResponseField", "orderStatus")
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
        )
        if mode == "bff-json":
            source = (
                source.replace(
                    "/// <PENDING_METHOD> <PENDING_PATH>",
                    "/// GET /orders/:orderId",
                )
                .replace("<PENDING_SOURCE>", "OrderContentView.orderId")
                .replace("<PENDING_PURPOSE>", "selects the order to load")
                .replace(
                    "const factory OrderContentModel() = _OrderContentModel;",
                    "const factory OrderContentModel({\n"
                    "    @Default(false) bool isExpanded,\n"
                    "    required int selectedTab,\n"
                    "  }) = _OrderContentModel;",
                )
            )
        contract.write_text(source, encoding="utf-8")
        return directory / "order_content.dart"

    def fake_fvm(
        self, root: Path, *, preflight_failure: bool = False
    ) -> dict[str, str]:
        bin_dir = root / "bin"
        bin_dir.mkdir()
        executable = bin_dir / "fvm"
        failure = (
            "print('analyzer 13 AST API incompatibility', file=sys.stderr); sys.exit(1)"
            if preflight_failure
            else "sys.exit(0)"
        )
        executable.write_text(
            "#!/usr/bin/env python3\n"
            "import pathlib, sys\n"
            "if '--help' in sys.argv:\n"
            f"    {failure}\n"
            "args = sys.argv\n"
            "source = pathlib.Path(args[args.index('--input') + 1]).read_text()\n"
            "response_field = ('refreshedOrderStatus' if "
            "'refreshedOrderStatus' in source else 'orderStatus')\n"
            "output = pathlib.Path(args[args.index('--output') + 1])\n"
            "output.write_text(\n"
            "    '# generated JSON5 BFF\\n\\n'\n"
            "    '## BFF-API\\n\\n'\n"
            "    '### GET /orders/:orderId\\n'\n"
            "    '- Request DTOs: [OrderContentBffReq]\\n'\n"
            "    '- Response DTOs: [OrderContentBffRsp]\\n\\n'\n"
            "    '#### Request JSON5\\n\\n```json5\\n{\\n'\n"
            "    '  // Dart type: String\\n  orderId: \\'string\\',\\n'\n"
            "    '}\\n```\\n\\n#### Response JSON5\\n\\n```json5\\n{\\n'\n"
            "    f\"  // Dart type: String\\n  {response_field}: 'string',\\n\"\n"
            "    '}\\n```\\n'\n"
            ")\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        return env

    def run_script(
        self, script: str, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), *args],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def test_page_and_component_generation_create_bff_artifact(self) -> None:
        for page in (True, False):
            with self.subTest(page=page), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                component = self.draft(root, page=page)
                selector = "--page-file" if page else "--component-file"
                target = (
                    component.with_name("order_content.page.dart")
                    if page
                    else component
                )
                env = self.fake_fvm(root)
                result = self.run_script(
                    "generate_from_contract.py",
                    selector,
                    str(target),
                    "--write-stubs",
                    env=env,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(component.with_suffix(".bff.md").is_file())
                artifact = component.with_suffix(".bff.md").read_text()
                self.assertTrue(artifact.startswith("---\nbff_meta:\n"))
                self.assertIn('schema: "bff-md-meta/v5"', artifact)
                self.assertIn("## UI API Contract", artifact)
                self.assertIn("## Backend Call Contract", artifact)
                self.assertIn("### OpenAPI References", artifact)
                self.assertIn("### Backend Call Flow", artifact)
                self.assertIn("## UI Contract", artifact)
                self.assertIn("## Integration Mapping", artifact)
                self.assertIn(
                    "| `OrderContentModel` | `isExpanded` | `bool` | Frontend |",
                    artifact,
                )
                self.assertIn(
                    "| `OrderContentModel` | `selectedTab` | `int` | Frontend |",
                    artifact,
                )
                self.assertNotIn("<!-- BFF_META", artifact)
                business = artifact.split("## UI API Contract", 1)[1].split(
                    "## Backend Call Contract", 1
                )[0]
                self.assertNotIn("isExpanded", business)
                self.assertNotIn("selectedTab", business)
                component.with_name("order_content.srv.g.dart").write_text(
                    "part of 'order_content.srv.dart';\n",
                    encoding="utf-8",
                )
                validated = self.run_script(
                    "validate_contract.py",
                    "--component-file",
                    str(component),
                    env=env,
                )
                self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_component_generates_after_page_adapter_is_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.draft(root, page=True)
            component.with_name("order_content.page.dart").unlink()
            result = self.run_script(
                "generate_bff.py",
                "--component-file",
                str(component),
                env=self.fake_fvm(root),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(component.with_suffix(".bff.md").is_file())

    def test_generated_body_keeps_each_backend_api_request_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            component = self.draft(root, page=False)
            spec = root / "docs/backend/orders.openapi.json"
            spec.parent.mkdir(parents=True)
            spec.write_text(
                json.dumps(
                    {
                        "openapi": "3.0.1",
                        "paths": {
                            "/orders": {"post": {"responses": {}}},
                            "/orders/{orderId}": {"get": {"responses": {}}},
                        },
                    }
                ),
                encoding="utf-8",
            )
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "/// Backend Calls:\n"
                    "/// - none\n"
                    "/// Backend Call Flow:\n"
                    "/// - none\n",
                    "/// Backend Calls:\n"
                    "/// - createOrder <- docs/backend/orders.openapi.json | POST /orders\n"
                    "/// - getOrder <- docs/backend/orders.openapi.json | GET /orders/{orderId}\n"
                    "/// Backend Call Flow:\n"
                    "/// - [createOrder] 创建订单\n"
                    "/// - [getOrder] 读取创建后的订单\n",
                ),
                encoding="utf-8",
            )

            result = self.run_script(
                "generate_bff.py",
                "--component-file",
                str(component),
                env=self.fake_fvm(root),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = component.with_suffix(".bff.md").read_text(encoding="utf-8")
            self.assertIn("id: createOrder", artifact)
            self.assertIn('route: "/orders"', artifact)
            self.assertIn("id: getOrder", artifact)
            self.assertIn('route: "/orders/{orderId}"', artifact)
            self.assertIn(
                "- [createOrder] `POST /orders` @ `docs/backend/orders.openapi.json`",
                artifact,
            )
            self.assertIn(
                "- [getOrder] `GET /orders/{orderId}` @ `docs/backend/orders.openapi.json`",
                artifact,
            )
            self.assertNotIn("Backend Request JSON5", artifact)
            self.assertNotIn("Backend Response JSON5", artifact)

    def test_unmigrated_contract_reproduces_v4_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.draft(root, page=False)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "/// Backend Calls:\n"
                    "/// - none\n"
                    "/// Backend Call Flow:\n"
                    "/// - none\n",
                    "",
                ),
                encoding="utf-8",
            )

            result = self.run_script(
                "generate_bff.py",
                "--component-file",
                str(component),
                env=self.fake_fvm(root),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = component.with_suffix(".bff.md").read_text(encoding="utf-8")
            self.assertIn('schema: "bff-md-meta/v4"', artifact)
            self.assertIn("## Business Contract", artifact)
            self.assertNotIn("## Backend Call Contract", artifact)

    def test_profiled_bff_response_envelope_requires_data_field(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            component = self.draft(root, page=False)
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "config.yaml").write_text(
                "\n".join(
                    [
                        "schema: fr-mvvm-contract.config.v1",
                        "profile: envelope-test",
                        "transport:",
                        "  bff_response_envelope:",
                        "    state_field: state",
                        "    code_field: code",
                        "    message_field: message",
                        "    data_field: data",
                        "tasks:",
                        "  validate:",
                        "    base: references/validate.md",
                    ]
                ),
                encoding="utf-8",
            )
            result = self.run_script(
                "validate_contract.py", "--component-file", str(component)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn(
            "gateway envelope fields: state, code, message, data", result.stderr
        )

    def test_generate_bff_immediately_generates_declared_retrofit_service(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.draft(root, page=False)
            result = self.run_script(
                "generate_bff.py",
                "--component-file",
                str(component),
                env=self.fake_fvm(root),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            service = component.with_name("order_content.srv.dart")
            self.assertTrue(service.is_file())
            self.assertIn("@RestApi()", service.read_text(encoding="utf-8"))
            self.assertIn(
                "part 'order_content.srv.g.dart';",
                service.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "import 'order_content.srv.dart';",
                component.read_text(encoding="utf-8"),
            )

    def test_check_rejects_missing_and_stale_bff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.draft(root, page=False)
            missing = self.run_script(
                "generate_bff.py", "--component-file", str(component), "--check"
            )
            self.assertEqual(missing.returncode, 2)
            self.assertIn("does not exist", missing.stderr)

            env = self.fake_fvm(root)
            generated = self.run_script(
                "generate_bff.py", "--component-file", str(component), env=env
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "orderStatus", "refreshedOrderStatus"
                ),
                encoding="utf-8",
            )
            stale = self.run_script(
                "generate_bff.py",
                "--component-file",
                str(component),
                "--check",
                env=env,
            )
            self.assertEqual(stale.returncode, 2)
            self.assertIn("stale", stale.stderr)
            validation = self.run_script(
                "validate_contract.py",
                "--component-file",
                str(component),
                env=env,
            )
            self.assertEqual(validation.returncode, 2)
            self.assertIn("stale", validation.stderr)

    def test_validator_rejects_missing_bff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            result = self.run_script(
                "validate_contract.py", "--component-file", str(component)
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("required BFF artifact does not exist", result.stderr)

    def test_validator_requires_json_dto_contract_and_direct_dependency(self) -> None:
        mutations = {
            "@FrAcddFreezedJSON": ("@FrAcddFreezed", "must use @FrAcddFreezedJSON"),
            "factory OrderContentBffReq.fromJson": (
                "factory OrderContentBffReq.fromMap",
                "must declare factory OrderContentBffReq.fromJson",
            ),
            "Map<String, dynamic> toJson();": (
                "Map<String, dynamic> serialize();",
                "must explicitly declare Map<String, dynamic> toJson()",
            ),
            "[OrderContentBffRsp]": (
                "[MissingBffRsp]",
                "references undefined DTOs",
            ),
        }
        for original, (replacement, expected) in mutations.items():
            with (
                self.subTest(original=original),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                component = self.draft(root, page=False)
                contract = component.with_name("order_content.c.dart")
                contract.write_text(
                    contract.read_text(encoding="utf-8").replace(
                        original, replacement, 1
                    ),
                    encoding="utf-8",
                )
                result = self.run_script(
                    "validate_contract.py", "--component-file", str(component)
                )

                self.assertEqual(result.returncode, 2)
                self.assertIn(expected, result.stderr)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.draft(root, page=False)
            pubspec = root / "pubspec.yaml"
            pubspec.write_text(
                pubspec.read_text(encoding="utf-8").replace("  fr_acdd: any\n", ""),
                encoding="utf-8",
            )
            result = self.run_script(
                "validate_contract.py", "--component-file", str(component)
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("directly declare fr_acdd", result.stderr)

    def test_validator_rejects_nonstandard_bff_type_suffixes(self) -> None:
        mutations = {
            "OrderContentBffReq": (
                "OrderContentRequest",
                "XxxBffReq suffix",
            ),
            "OrderContentBffRsp": (
                "OrderContentResponse",
                "XxxBffRsp suffix",
            ),
        }
        for original, (replacement, expected) in mutations.items():
            with (
                self.subTest(original=original),
                tempfile.TemporaryDirectory() as temporary,
            ):
                component = self.draft(Path(temporary), page=False)
                contract = component.with_name("order_content.c.dart")
                contract.write_text(
                    contract.read_text(encoding="utf-8").replace(original, replacement),
                    encoding="utf-8",
                )
                result = self.run_script(
                    "validate_contract.py", "--component-file", str(component)
                )

            self.assertEqual(result.returncode, 2)
            self.assertIn(expected, result.stderr)

        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8")
                + "\n@FrAcddDto(kind: FrAcddDtoKind.nested)\n"
                "@FrAcddFreezedJSON\n"
                "class OrderItemData {\n"
                "  factory OrderItemData.fromJson(Map<String, dynamic> json) "
                "=> OrderItemData();\n"
                "}\n",
                encoding="utf-8",
            )
            result = self.run_script(
                "validate_contract.py", "--component-file", str(component)
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("internal BFF DTO classes", result.stderr)
        self.assertIn("XxxDto suffix", result.stderr)

    def test_api_mode_does_not_generate_or_require_bff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False, mode="api")
            generated = self.run_script(
                "generate_from_contract.py", "--component-file", str(component)
            )
            validated = self.run_script(
                "validate_contract.py", "--component-file", str(component)
            )

            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertFalse(component.with_suffix(".bff.md").exists())

    def test_extractor_preflight_failure_is_explicit_and_preserves_artifact(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.draft(root, page=False)
            artifact = component.with_suffix(".bff.md")
            artifact.write_text("known-good\n", encoding="utf-8")
            result = self.run_script(
                "generate_bff.py",
                "--component-file",
                str(component),
                env=self.fake_fvm(root, preflight_failure=True),
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("extractor preflight failed", result.stderr)
            self.assertIn("analyzer", result.stderr)
            self.assertEqual(artifact.read_text(encoding="utf-8"), "known-good\n")

    def test_derived_preflight_failure_leaves_no_stubs_or_partial_bff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.draft(root, page=False)
            artifact = component.with_suffix(".bff.md")
            artifact.write_text("known-good\n", encoding="utf-8")

            result = self.run_script(
                "generate_from_contract.py",
                "--component-file",
                str(component),
                "--write-stubs",
                env=self.fake_fvm(root, preflight_failure=True),
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("extractor preflight failed", result.stderr)
            self.assertEqual(artifact.read_text(encoding="utf-8"), "known-good\n")
            self.assertFalse(component.with_name("order_content.v.dart").exists())
            self.assertFalse(component.with_name("order_content.vm.dart").exists())


if __name__ == "__main__":
    unittest.main()

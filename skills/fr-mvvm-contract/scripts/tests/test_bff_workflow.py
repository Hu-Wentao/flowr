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
UV_RUN_SCRIPT = ("uv", "run", "--script")


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
            *UV_RUN_SCRIPT,
            str(SCRIPTS / "draft_contract.py"),
            "--name",
            "order_content",
            "--dir",
            str(directory),
            "--figma-url",
            "https://example.com/design",
            "--figma-frame",
            "Order content",
            "--mode",
            mode,
        ]
        if mode == "api":
            command.extend(["--api", "GET /orders/:id"])
        if not page:
            command.extend(["--component-only", "--state-owner", "component"])
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
                "/// - TODO: declare the cross-route capability owned by this component.\n",
                "/// - Order content presentation and refresh.\n",
            )
            .replace(
                "/// - [OrderContentView] — TODO: describe this reusable entry.\n",
                "/// - [OrderContentView] — reusable order content.\n",
            )
            .replace(
                "/// Data Boundary:\n"
                "/// - TODO(data-boundary): identify the approved UI API/OpenAPI "
                "operation or confirm an API-less local-only decision before "
                "implementing data behavior.\n",
                "/// Data Boundary:\n"
                "/// - approved UI API: GET /orders/:orderId is confirmed by "
                "the test fixture.\n",
            )
            .replace(
                "/// SDK Calls:\n"
                "/// - pendingSdkCall <- <PENDING_SDK_CLIENT>.<PENDING_SDK_OPERATION>\n"
                "/// SDK Call Flow:\n"
                "/// - [pendingSdkCall] <PENDING_CALL_FLOW>\n",
                "/// SDK Calls:\n/// - none\n/// SDK Call Flow:\n/// - none\n",
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
            [*UV_RUN_SCRIPT, str(SCRIPTS / script), *args],
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
                self.assertTrue(
                    artifact.startswith(
                        "---\n"
                        "bff_meta:\n"
                        '  schema: "bff-md-meta/v8"\n'
                        '  namespace: "order_content"\n'
                        "  contract_version: 1\n"
                        "  ui_source:\n"
                        "    type: figma\n"
                        '    url: "https://example.com/design"\n'
                        "mdq:\n"
                    )
                )
                self.assertIn(
                    "\n---\n# OrderContentView BFF Contract\n", artifact
                )
                metadata = artifact.split("---\n", 2)[1]
                self.assertNotIn("ui_revision:", metadata)
                self.assertNotIn("mode:", metadata)
                self.assertNotIn("contract_file:", metadata)
                self.assertNotIn("authorities:", metadata)
                self.assertNotIn("ui_apis:", metadata)
                self.assertNotIn("backend_calls:", metadata)
                self.assertIn("## 后端业务流程与业务逻辑 API", artifact)
                self.assertIn("### 业务逻辑 API", artifact)
                self.assertIn("### 业务流程", artifact)
                self.assertIn("## 前端 UI 数据接口", artifact)
                self.assertIn("### 接口描述", artifact)
                self.assertIn("## UI Contract", artifact)
                self.assertIn("## Integration Mapping", artifact)
                self.assertIn("## API Query Records", artifact)
                self.assertIn("apis_by_integration_status:", metadata)
                self.assertIn(
                    "| ui:order_content:get:/orders/:orderId | order_content | "
                    "ui | orderContent | GET | /orders/:orderId | declared | "
                    "unconfirmed | Frontend | frontend BFF declaration |",
                    artifact,
                )
                self.assertIn("### UI State\n\n```json5", artifact)
                self.assertIn("// Model: OrderContentModel", artifact)
                self.assertIn("// Dart type: bool", artifact)
                self.assertIn("// Authority: Frontend\n  isExpanded: false,", artifact)
                self.assertIn("// Dart type: int", artifact)
                self.assertIn("selectedTab: 0,", artifact)
                self.assertNotIn(
                    "| Model | UI Field | Dart Type | Authority |", artifact
                )
                self.assertNotIn("<!-- BFF_META", artifact)
                api_description = artifact.split("### 接口描述", 1)[1].split(
                    "## UI Contract", 1
                )[0]
                self.assertNotIn("isExpanded", api_description)
                self.assertNotIn("selectedTab", api_description)
                sdk = root / "lib/api/gen/orders_api.dart"
                sdk.parent.mkdir(parents=True, exist_ok=True)
                sdk.write_text("abstract class OrdersApi {}\n", encoding="utf-8")
                component.with_name("order_content.srv.dart").write_text(
                    "import '../api/gen/orders_api.dart' as orders_sdk;\n"
                    "import 'order_content.dart';\n"
                    "abstract class OrderContentService {\n"
                    "  Future<OrderContentBffRsp> orderContent("
                    "OrderContentBffReq request);\n"
                    "}\n",
                    encoding="utf-8",
                )
                component.write_text(
                    component.read_text(encoding="utf-8").replace(
                        "part 'order_content.c.dart';",
                        "import 'order_content.srv.dart';\n"
                        "part 'order_content.c.dart';",
                    ),
                    encoding="utf-8",
                )
                target_flag = "--page-file" if page else "--component-file"
                target_file = (
                    component.with_name("order_content.page.dart")
                    if page
                    else component
                )
                validated = self.run_script(
                    "validate_contract.py",
                    target_flag,
                    str(target_file),
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

    def test_frontend_refresh_preserves_backend_owned_section(self) -> None:
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
            env = self.fake_fvm(root)
            generated = self.run_script(
                "generate_bff.py",
                "--component-file",
                str(component),
                env=env,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            artifact_file = component.with_suffix(".bff.md")
            artifact = artifact_file.read_text(encoding="utf-8")
            backend = (
                "## 后端业务流程与业务逻辑 API\n\n"
                "> Authority: Backend. 此区域由后端开发维护。\n\n"
                "### 业务逻辑 API\n\n"
                "- [createOrder] POST /orders | Parameters: body CreateOrderReq "
                "| Response: CreateOrderRsp\n"
                "- [getOrder] GET /orders/{orderId} | Parameters: orderId String "
                "| Response: GetOrderRsp\n\n"
                "### 业务流程\n\n"
                "- [createOrder] 创建订单\n"
                "- [getOrder] 读取创建后的订单\n"
            )
            backend_start = artifact.index("## 后端业务流程与业务逻辑 API")
            frontend_start = artifact.index("## 前端 UI 数据接口")
            artifact_file.write_text(
                artifact[:backend_start] + backend + artifact[frontend_start:],
                encoding="utf-8",
            )
            sdk = root / "lib/api/gen/orders_api.dart"
            sdk.parent.mkdir(parents=True)
            sdk.write_text(
                "class CreateOrderReq {}\nclass CreateOrderRsp {}\n"
                "class GetOrderRsp {}\n",
                encoding="utf-8",
            )
            refreshed = self.run_script(
                "generate_bff.py",
                "--component-file",
                str(component),
                env=env,
            )
            self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
            refreshed_text = artifact_file.read_text(encoding="utf-8")
            preserved = refreshed_text[
                refreshed_text.index("## 后端业务流程与业务逻辑 API") :
                refreshed_text.index("## 前端 UI 数据接口")
            ]
            self.assertEqual(preserved, backend)

    def test_contract_without_backend_calls_renders_empty_backend_logic(self) -> None:
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
            self.assertTrue(
                artifact.startswith(
                    "---\n"
                    "bff_meta:\n"
                    '  schema: "bff-md-meta/v8"\n'
                    '  namespace: "order_content"\n'
                    "  contract_version: 1\n"
                    "  ui_source:\n"
                    "    type: figma\n"
                    '    url: "https://example.com/design"\n'
                    "mdq:\n"
                )
            )
            self.assertIn("\n---\n# OrderContentView BFF Contract\n", artifact)
            self.assertIn("## 后端业务流程与业务逻辑 API", artifact)
            self.assertIn("### 业务逻辑 API\n\n- none", artifact)

    def test_front_matter_uses_explicit_contract_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.draft(root, page=False)
            view = component.with_name("order_content.v.dart")
            view.write_text(
                view.read_text(encoding="utf-8").replace(
                    "namespace: 'order_content',",
                    "namespace: 'order_content',\n  version: 2,",
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
            metadata = artifact.split("---\n", 2)[1]
            self.assertIn('namespace: "order_content"', metadata)
            self.assertIn("contract_version: 2", metadata)

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

    def test_generate_bff_does_not_generate_backend_sdk_adapter(self) -> None:
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
            self.assertFalse(service.exists())

    def test_check_accepts_sdk_adapter_service_without_retrofit_part(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            sdk = root / "lib/api/gen/orders_api.dart"
            sdk.parent.mkdir(parents=True)
            sdk.write_text(
                "abstract class OrdersApi {\n" "  Future<void> getOrder();\n" "}\n",
                encoding="utf-8",
            )
            component = self.draft(root, page=False)
            component.with_name("order_content.srv.dart").write_text(
                "import '../api/gen/orders_api.dart' as orders_sdk;\n"
                "class OrderContentService {\n"
                "  Future<void> orderContent(Object request) async {}\n"
                "}\n",
                encoding="utf-8",
            )
            env = self.fake_fvm(root)
            generated = self.run_script(
                "generate_bff.py",
                "--component-file",
                str(component),
                env=env,
            )
            checked = self.run_script(
                "generate_bff.py",
                "--component-file",
                str(component),
                "--check",
                env=env,
            )

            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertFalse(component.with_name("order_content.srv.g.dart").exists())

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

    def test_api_less_bff_generates_without_dto_or_retrofit_service(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_pubspec(root)
            directory = root / "lib/api_less"
            directory.mkdir(parents=True)
            component = directory / "api_less.dart"
            component.write_text(
                "import 'package:fr_acdd/fr_acdd.dart';\n" "part 'api_less.c.dart';\n",
                encoding="utf-8",
            )
            component.with_name("api_less.c.dart").write_text(
                "part of 'api_less.dart';\n\n"
                "/// State Ownership: none\n"
                "/// Widget Tree: [ApiLessView] > [LocalPasswordForm]\n"
                "/// BFF-API: -\n"
                "@FrAcddPage(mode: FrAcddMode.bff, namespace: 'api_less')\n"
                "class ApiLessView {}\n",
                encoding="utf-8",
            )

            generated = self.run_script(
                "generate_bff.py", "--component-file", str(component)
            )
            checked = self.run_script(
                "generate_bff.py", "--component-file", str(component), "--check"
            )

            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            artifact = component.with_suffix(".bff.md").read_text(encoding="utf-8")
            self.assertIn("### 接口描述\n-", artifact)
            self.assertIn(
                "| backend:api_less:none | api_less | backend_logic | none | - | - | "
                "api_less | not_required | Backend | BFF disposition |",
                artifact,
            )
            self.assertIn(
                "| ui:api_less:none | api_less | ui | none | - | - | api_less | "
                "not_required | Frontend | BFF disposition |",
                artifact,
            )
            self.assertFalse(component.with_name("api_less.srv.dart").exists())

    def test_query_records_surface_runtime_backend_calls_missing_from_bff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.draft(root, page=False)
            sdk = root / "lib/api/gen/runtime_api.dart"
            sdk.parent.mkdir(parents=True, exist_ok=True)
            sdk.write_text(
                "@RestApi()\n"
                "abstract class RuntimeApi {\n"
                "  @POST(\"/app/runtime/execute\")\n"
                "  Future<void> postAppRuntimeExecute();\n"
                "}\n",
                encoding="utf-8",
            )
            component.with_name("order_content.srv.dart").write_text(
                "import '../api/gen/runtime_api.dart';\n"
                "class OrderContentService {\n"
                "  Future<void> execute(RuntimeApi api) => "
                "api.postAppRuntimeExecute();\n"
                "}\n",
                encoding="utf-8",
            )

            generated = self.run_script(
                "generate_bff.py",
                "--component-file",
                str(component),
                env=self.fake_fvm(root),
            )

            self.assertEqual(generated.returncode, 0, generated.stderr)
            artifact = component.with_suffix(".bff.md").read_text(encoding="utf-8")
            self.assertIn(
                "| backend:order_content:runtime:postAppRuntimeExecute | "
                "order_content | backend_logic | postAppRuntimeExecute | POST | "
                "/app/runtime/execute | missing_backend_contract | integrated | "
                "Code/Test Fact | order_content.srv.dart:postAppRuntimeExecute |",
                artifact,
            )

    def test_generated_api_records_are_mdq_queryable(self) -> None:
        candidates = (
            Path.home() / ".agents/skills/queryable-markdown/scripts/mdq.py",
            Path.home() / ".codex/skills/queryable-markdown/scripts/mdq.py",
        )
        mdq = next((path for path in candidates if path.is_file()), None)
        if mdq is None:
            self.skipTest("queryable-markdown is not installed")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.draft(root, page=False)
            generated = self.run_script(
                "generate_bff.py",
                "--component-file",
                str(component),
                env=self.fake_fvm(root),
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            artifact = component.with_suffix(".bff.md")

            validated = subprocess.run(
                ["uv", "run", str(mdq), "validate", str(artifact)],
                capture_output=True,
                text=True,
                check=False,
            )
            queried = subprocess.run(
                [
                    "uv",
                    "run",
                    str(mdq),
                    "query",
                    str(artifact),
                    "--id",
                    "ui:order_content:get:/orders/:orderId",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            self.assertEqual(queried.returncode, 0, queried.stdout + queried.stderr)
            record = json.loads(queried.stdout)["records"][0]
            self.assertEqual(record["fields"]["api_type"], "ui")
            self.assertEqual(
                record["fields"]["integration_status"], "unconfirmed"
            )

    def test_extractor_preflight_failure_is_explicit_and_preserves_artifact(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = self.draft(root, page=False)
            artifact = component.with_suffix(".bff.md")
            artifact.write_text("known-good\n", encoding="utf-8")
            view = component.with_name("order_content.v.dart")
            original_view = view.read_text(encoding="utf-8")
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
            view = component.with_name("order_content.v.dart")
            original_view = view.read_text(encoding="utf-8")

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
            self.assertEqual(view.read_text(encoding="utf-8"), original_view)
            self.assertFalse(component.with_name("order_content.vm.dart").exists())


if __name__ == "__main__":
    unittest.main()

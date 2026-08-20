#!/usr/bin/env python3
"""Regression tests for backend-SDK adapter Service ownership."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from contract_core import ContractError  # noqa: E402
from contract_parser import parse_component  # noqa: E402
from generate_service import generate_service, plan_service  # noqa: E402


class GenerateServiceTest(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[Path, object, bytes]:
        directory = root / "lib/order_content"
        directory.mkdir(parents=True)
        component_file = directory / "order_content.dart"
        component_file.write_text(
            "import 'order_content.srv.dart';\n"
            "part 'order_content.c.dart';\n",
            encoding="utf-8",
        )
        (directory / "order_content.c.dart").write_text(
            "part of 'order_content.dart';\n"
            "/// State Ownership: none\n"
            "/// BFF-UI-API:\n"
            "/// GET /orders\n"
            "/// [OrderContentBffReq], [OrderContentBffRsp]\n"
            "/// Behaviors:\n"
            "/// - Endpoint: [OrderContentBffReq]\n"
            "/// - UI Data: orders\n"
            "/// - Source: test fixture\n"
            "/// - Loading/Refresh: load once\n"
            "/// - Empty/Error: empty list or retry\n"
            "/// Request Field Sources:\n"
            "/// - Endpoint: [OrderContentBffReq]\n"
            "/// - none\n"
            "/// Interactions:\n"
            "/// - Flow: load-orders\n"
            "/// - Trigger: external test-fixture\n"
            "/// - Event: [OrderContentStarted]\n"
            "/// - Uses: ui-api [OrderContentBffReq]\n"
            "/// - Guard: none\n"
            "/// - Pending State: [OrderContentModel].loading = true\n"
            "/// - Success State: [OrderContentModel].loading = false\n"
            "/// - Failure State: [OrderContentModel].loading = false\n"
            "/// - Concurrency: latest-wins\n"
            "/// - Navigation: none\n"
            "/// BFF Service: [OrderContentService]\n"
            "class OrderContentView {}\n",
            encoding="utf-8",
        )
        bff = (
            "## 后端业务流程与业务逻辑 API\n\n"
            "### 业务逻辑 API\n\n- none\n\n"
            "### 业务流程\n\n- none\n"
            "## 前端 UI 数据接口\n\n"
            "#### GET /orders\n"
            "- Request DTOs: [OrderContentBffReq]\n"
            "- Response DTOs: [OrderContentBffRsp]\n"
        ).encode()
        component_file.with_suffix(".bff.md").write_bytes(bff)
        return component_file, parse_component(component_file), bff

    def test_missing_service_is_not_generated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file, component, _ = self.fixture(Path(temporary))

            service = generate_service(component, check=False)

            self.assertIsNone(service)
            self.assertFalse(
                component_file.with_name("order_content.srv.dart").exists()
            )

    def test_check_rejects_missing_service(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            _, component, _ = self.fixture(Path(temporary))

            with self.assertRaisesRegex(ContractError, "SDK adapter service"):
                generate_service(component, check=True)

    def test_existing_sdk_adapter_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file, component, bff = self.fixture(Path(temporary))
            service_file = component_file.with_name("order_content.srv.dart")
            source = (
                "import '../api/gen/orders_api.dart' as orders_sdk;\n"
                "typedef OrderContentReq = orders_sdk.GetOrderReq;\n"
                "class OrderContentService {\n"
                "  Future<orders_sdk.RspWrapper<orders_sdk.OrderDto>> "
                "orderContent(OrderContentReq request) async => "
                "throw UnimplementedError();\n"
                "}\n"
            )
            service_file.write_text(source, encoding="utf-8")

            updates, planned = plan_service(component, bff)

            self.assertEqual(planned, service_file)
            self.assertEqual(updates, {})
            self.assertEqual(service_file.read_text(encoding="utf-8"), source)

    def test_rejects_frontend_retrofit_service(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file, component, bff = self.fixture(Path(temporary))
            component_file.with_name("order_content.srv.dart").write_text(
                "import '../api/gen/orders_api.dart';\n"
                "@RestApi()\nabstract class OrderContentService {}\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ContractError, "not a frontend Retrofit"):
                plan_service(component, bff)

    def test_rejects_service_without_generated_sdk_import(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file, component, bff = self.fixture(Path(temporary))
            component_file.with_name("order_content.srv.dart").write_text(
                "class OrderContentService {}\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(ContractError, "lib/api/gen"):
                plan_service(component, bff)


if __name__ == "__main__":
    unittest.main()

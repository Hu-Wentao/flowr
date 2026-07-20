#!/usr/bin/env python3
"""Tests for BFF Markdown driven component service generation."""

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
from generate_service import (  # noqa: E402
    GENERATED_SERVICE_MARKER,
    apply_updates,
    generate_service,
    parse_bff_markdown,
    plan_service,
)


class GenerateServiceTest(unittest.TestCase):
    """Service generator behavior tests."""

    def fixture(
        self,
        root: Path,
        *,
        method: str = "GET",
        path: str = "/orders/:orderId",
        service: str | None = "[OrderContentService]",
    ) -> Path:
        (root / ".git").mkdir()
        (root / "pubspec.yaml").write_text(
            "name: service_fixture\n"
            "dependencies:\n"
            "  dio: any\n"
            "  efficient_dio_logger: any\n"
            "  retrofit: any\n"
            "dev_dependencies:\n"
            "  build_runner: any\n"
            "  retrofit_generator: any\n",
            encoding="utf-8",
        )
        directory = root / "lib/order_content"
        directory.mkdir(parents=True)
        component = directory / "order_content.dart"
        component.write_text(
            "part 'order_content.c.dart';\n"
            "part 'order_content.v.dart';\n"
            "part 'order_content.vm.dart';\n",
            encoding="utf-8",
        )
        service_line = f"/// BFF Service: {service}\n" if service else ""
        (directory / "order_content.c.dart").write_text(
            "part of 'order_content.dart';\n"
            "/// BFF-API:\n"
            f"/// {method} {path}\n"
            "/// [OrderContentBffReq], [OrderContentBffRsp]\n"
            f"{service_line}"
            "class OrderContentView {}\n",
            encoding="utf-8",
        )
        bff = (
            "# Derived JSON5 Contract\n\n"
            "## BFF-API\n\n"
            f"### {method} {path}\n"
            "- Request DTOs: [OrderContentBffReq]\n"
            "- Response DTOs: [OrderContentBffRsp]\n\n"
            "#### Request JSON5\n\n```json5\n{\n"
            "  // Dart type: String\n"
            "  orderId: 'string',\n"
            "}\n```\n\n"
            "#### Response JSON5\n\n```json5\n{status: 'string'}\n```\n"
        )
        component.with_suffix(".bff.md").write_text(bff, encoding="utf-8")
        return component

    def test_parse_bff_markdown_reads_endpoint_and_dtos(self) -> None:
        parsed = parse_bff_markdown(
            "### POST /orders\n"
            "- Request DTOs: [CreateOrderBffReq]\n"
            "- Response DTOs: [CreateOrderBffRsp]\n"
        )

        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].method, "POST")
        self.assertEqual(parsed[0].path, "/orders")
        self.assertEqual(parsed[0].request_type, "CreateOrderBffReq")
        self.assertEqual(parsed[0].response_type, "CreateOrderBffRsp")

    def test_generate_get_service_uses_application_dio_and_updates_shell(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.fixture(Path(temporary))
            component = parse_component(component_file)
            service = generate_service(component, check=False)
            source = service.read_text(encoding="utf-8") if service else ""
            shell = component_file.read_text(encoding="utf-8")

        self.assertIn(GENERATED_SERVICE_MARKER, source)
        self.assertIn("abstract class OrderContentService", source)
        self.assertIn("@RestApi()", source)
        self.assertIn('@GET("/orders/{orderId}")', source)
        self.assertIn("@Path('orderId') required String orderId", source)
        self.assertIn("@Queries() required Map<String, dynamic> queries", source)
        self.assertIn("extension OrderContentServiceOperations", source)
        self.assertIn("Future<OrderContentBffRsp> orderContent(", source)
        self.assertIn("return _orderContentRequest(", source)
        self.assertNotIn("efficient_dio_logger", source)
        self.assertNotIn("EffDioLogger", source)
        self.assertNotIn("_withServiceLogging", source)
        self.assertIn(
            "factory OrderContentService(Dio dio) =",
            source,
        )
        self.assertIn("_OrderContentService;", source)
        self.assertNotIn("RetrofitApi", source)
        self.assertIn("part 'order_content.srv.g.dart';", source)
        self.assertIn("import 'order_content.srv.dart';", shell)

    def test_post_service_sends_remaining_request_data_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.fixture(
                Path(temporary), method="POST", path="/orders"
            )
            component = parse_component(component_file)
            updates, _ = plan_service(
                component, component_file.with_suffix(".bff.md").read_bytes()
            )
            source = updates[component_file.with_name("order_content.srv.dart")].decode(
                "utf-8"
            )

        self.assertIn('@POST("/orders")', source)
        self.assertIn("Future<OrderContentBffRsp> orderContent(", source)
        self.assertIn("@Body() OrderContentBffReq request", source)
        self.assertNotIn("extension OrderContentServiceOperations", source)
        self.assertNotIn("Map<String, dynamic>.from(request.toJson())", source)

    def test_pathless_get_uses_typed_request_queries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.fixture(Path(temporary), path="/orders")
            component = parse_component(component_file)
            updates, _ = plan_service(
                component, component_file.with_suffix(".bff.md").read_bytes()
            )
            source = updates[component_file.with_name("order_content.srv.dart")].decode(
                "utf-8"
            )

        self.assertIn("@Queries() OrderContentBffReq request", source)
        self.assertNotIn("extension OrderContentServiceOperations", source)

    def test_multiple_endpoints_share_one_service_with_semantic_methods(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.fixture(Path(temporary), path="/orders")
            contract = component_file.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "/// [OrderContentBffReq], [OrderContentBffRsp]\n",
                    "/// [OrderContentBffReq], [OrderContentBffRsp]\n"
                    "/// - POST /orders/submit\n"
                    "/// [OrderContentSubmitBffReq], [OrderContentSubmitBffRsp]\n",
                ),
                encoding="utf-8",
            )
            bff = component_file.with_suffix(".bff.md")
            bff.write_text(
                bff.read_text(encoding="utf-8") + "\n### POST /orders/submit\n"
                "- Request DTOs: [OrderContentSubmitBffReq]\n"
                "- Response DTOs: [OrderContentSubmitBffRsp]\n\n"
                "#### Request JSON5\n\n```json5\n{}\n```\n\n"
                "#### Response JSON5\n\n```json5\n{}\n```\n",
                encoding="utf-8",
            )
            component = parse_component(component_file)
            updates, _ = plan_service(component, bff.read_bytes())
            source = updates[component_file.with_name("order_content.srv.dart")].decode(
                "utf-8"
            )

        self.assertEqual(source.count("abstract class OrderContentService"), 1)
        self.assertIn("Future<OrderContentBffRsp> orderContent(", source)
        self.assertIn("Future<OrderContentSubmitBffRsp> submit(", source)

    def test_duplicate_derived_operation_names_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.fixture(Path(temporary), path="/orders")
            contract = component_file.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "/// [OrderContentBffReq], [OrderContentBffRsp]\n",
                    "/// [OrderContentBffReq], [OrderContentBffRsp]\n"
                    "/// - POST /orders/duplicate\n"
                    "/// [OrderContentBffReq], [OrderContentDuplicateBffRsp]\n",
                ),
                encoding="utf-8",
            )
            bff = component_file.with_suffix(".bff.md")
            bff.write_text(
                bff.read_text(encoding="utf-8") + "\n### POST /orders/duplicate\n"
                "- Request DTOs: [OrderContentBffReq]\n"
                "- Response DTOs: [OrderContentDuplicateBffRsp]\n\n"
                "#### Request JSON5\n\n```json5\n{}\n```\n\n"
                "#### Response JSON5\n\n```json5\n{}\n```\n",
                encoding="utf-8",
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(ContractError, "duplicate service operations"):
                plan_service(component, bff.read_bytes())

    def test_bff_without_service_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.fixture(Path(temporary), service=None)
            component = parse_component(component_file)
            with self.assertRaisesRegex(ContractError, "contract-only delivery"):
                generate_service(component, check=False)

    def test_bff_mismatch_is_rejected_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.fixture(Path(temporary))
            component = parse_component(component_file)
            stale = (
                component_file.with_suffix(".bff.md")
                .read_bytes()
                .replace(b"/orders/:orderId", b"/stale/:orderId")
            )

            with self.assertRaisesRegex(ContractError, "do not match"):
                plan_service(component, stale)

        self.assertFalse(component_file.with_name("order_content.srv.dart").exists())

    def test_existing_service_is_preserved_after_first_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.fixture(Path(temporary))
            service_file = component_file.with_name("order_content.srv.dart")
            service_file.write_text(
                "import 'order_content.dart';\n"
                "part 'order_content.srv.g.dart';\n"
                "@CustomRestApi()\n"
                "final class OrderContentService {}\n",
                encoding="utf-8",
            )
            component = parse_component(component_file)
            updates, planned = plan_service(
                component, component_file.with_suffix(".bff.md").read_bytes()
            )
            apply_updates(updates)
            preserved = service_file.read_text(encoding="utf-8")

        self.assertEqual(planned, service_file)
        self.assertEqual(
            preserved,
            "import 'order_content.dart';\n"
            "part 'order_content.srv.g.dart';\n"
            "@CustomRestApi()\n"
            "final class OrderContentService {}\n",
        )

    def test_check_accepts_developer_modified_service(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.fixture(Path(temporary))
            component = parse_component(component_file)
            service_file = generate_service(component, check=False)
            source = service_file.read_text(encoding="utf-8")
            service_file.write_text(
                source.replace(GENERATED_SERVICE_MARKER + "\n", "").replace(
                    '@GET("/orders/{orderId}")',
                    "@Headers(<String, dynamic>{'X-Project': 'custom'})\n"
                    '@GET("/orders/{orderId}")',
                ),
                encoding="utf-8",
            )
            service_file.with_name("order_content.srv.g.dart").write_text(
                "part of 'order_content.srv.dart';\n",
                encoding="utf-8",
            )

            checked = generate_service(component, check=True)

        self.assertEqual(checked, service_file)


if __name__ == "__main__":
    unittest.main()

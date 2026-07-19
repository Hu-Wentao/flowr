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
        base_url: str | None = "https://dev.example.com",
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
        if base_url is not None:
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "config.yaml").write_text(
                "schema: fr-mvvm-contract.config.v1\n"
                "profile: fixture\n"
                "service:\n"
                f"  base_url: {base_url}\n"
                "tasks: {}\n",
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

        self.assertEqual(parsed.method, "POST")
        self.assertEqual(parsed.path, "/orders")
        self.assertEqual(parsed.request_type, "CreateOrderBffReq")
        self.assertEqual(parsed.response_type, "CreateOrderBffRsp")

    def test_generate_get_service_uses_config_and_updates_shell(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.fixture(Path(temporary))
            component = parse_component(component_file)
            service = generate_service(component, check=False)
            source = service.read_text(encoding="utf-8") if service else ""
            shell = component_file.read_text(encoding="utf-8")

        self.assertIn(GENERATED_SERVICE_MARKER, source)
        self.assertIn("final class OrderContentService", source)
        self.assertIn('@RestApi(baseUrl: "https://dev.example.com/")', source)
        self.assertIn('@GET("/orders/{orderId}")', source)
        self.assertIn("@Path('orderId') required String orderId", source)
        self.assertIn("@Queries() required Map<String, dynamic> queries", source)
        self.assertIn("import 'package:efficient_dio_logger/", source)
        self.assertIn("interceptor is EffDioLogger", source)
        self.assertIn("dio.interceptors.add(EffDioLogger())", source)
        self.assertIn("_withServiceLogging(dio)", source)
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
        self.assertIn("@Body() required Map<String, dynamic> body", source)

    def test_missing_base_url_requires_constructor_value(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.fixture(Path(temporary), base_url=None)
            component = parse_component(component_file)
            updates, _ = plan_service(
                component, component_file.with_suffix(".bff.md").read_bytes()
            )
            source = updates[component_file.with_name("order_content.srv.dart")].decode(
                "utf-8"
            )

        self.assertIn("@RestApi()", source)
        self.assertIn(
            "factory OrderContentRetrofitApi(Dio dio, {String? baseUrl})", source
        )

    def test_contract_only_does_not_generate_service(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.fixture(Path(temporary), service=None)
            component = parse_component(component_file)
            service = generate_service(component, check=False)

        self.assertIsNone(service)

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

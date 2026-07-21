#!/usr/bin/env python3
"""End-to-end regression for BFF Markdown to Retrofit generated service code."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from contract_parser import parse_component  # noqa: E402
from generate_service import generate_service  # noqa: E402


@unittest.skipUnless(shutil.which("fvm"), "fvm is required for Retrofit codegen")
class RetrofitCodegenIntegrationTest(unittest.TestCase):
    """Prove Python source generation followed by Dart implementation generation."""

    def run_command(
        self, root: Path, *command: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )

    def test_bff_markdown_generates_srv_and_retrofit_implementation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="retrofit_codegen_") as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            (root / "lib").mkdir()
            (root / "pubspec.yaml").write_text(
                "name: retrofit_codegen_fixture\n"
                "environment:\n"
                "  sdk: ^3.7.0\n"
                "dependencies:\n"
                "  dio: ^5.9.0\n"
                "  efficient_dio_logger: ^1.8.0\n"
                "  flutter:\n"
                "    sdk: flutter\n"
                "  retrofit: ^4.9.0\n"
                "dev_dependencies:\n"
                "  build_runner: ^2.10.0\n"
                "  retrofit_generator: ^10.0.0\n",
                encoding="utf-8",
            )
            component = root / "lib/order_content.dart"
            component.write_text(
                "part 'order_content.c.dart';\n",
                encoding="utf-8",
            )
            (root / "lib/order_content.c.dart").write_text(
                "part of 'order_content.dart';\n"
                "/// BFF-API:\n"
                "/// POST /orders\n"
                "/// [OrderContentBffReq], [OrderContentBffRsp]\n"
                "/// BFF Service: [OrderContentService]\n"
                "class OrderContentView {}\n"
                "abstract class OrderContentBffReq {\n"
                "  const factory OrderContentBffReq({required String orderId}) =\n"
                "      _OrderContentBffReq;\n"
                "  String get orderId;\n"
                "  Map<String, dynamic> toJson();\n"
                "}\n"
                "final class _OrderContentBffReq implements OrderContentBffReq {\n"
                "  const _OrderContentBffReq({required this.orderId});\n"
                "  @override\n"
                "  final String orderId;\n"
                "  @override\n"
                "  Map<String, dynamic> toJson() => {'orderId': orderId};\n"
                "}\n"
                "class OrderContentBffRsp {\n"
                "  const OrderContentBffRsp({required this.status});\n"
                "  final String status;\n"
                "  factory OrderContentBffRsp.fromJson(Map<String, dynamic> json) =>\n"
                "      OrderContentBffRsp(status: json['status'] as String);\n"
                "}\n",
                encoding="utf-8",
            )
            component.with_suffix(".bff.md").write_text(
                "---\n"
                "bff_meta:\n"
                "  schema: \"bff-md-meta/v4\"\n"
                "  authorities:\n"
                "    business:\n"
                "      owner: backend\n"
                "    ui:\n"
                "      owner: frontend\n"
                "---\n"
                "# OrderContentView BFF Contract\n\n"
                "## Business Contract\n\n"
                "> Authority: Backend.\n\n"
                "## BFF-API\n\n"
                "### POST /orders\n"
                "- Request DTOs: [OrderContentBffReq]\n"
                "- Response DTOs: [OrderContentBffRsp]\n\n"
                "#### Request JSON5\n\n"
                "```json5\n"
                "{\n"
                "  // Dart type: String\n"
                "  orderId: 'string',\n"
                "}\n"
                "```\n\n"
                "#### Response JSON5\n\n"
                "```json5\n"
                "{\n"
                "  // Dart type: String\n"
                "  status: 'string',\n"
                "}\n"
                "```\n\n"
                "## UI Contract\n\n- none\n\n"
                "## Integration Mapping\n\n- none\n",
                encoding="utf-8",
            )

            generated = generate_service(parse_component(component), check=False)
            self.assertEqual(generated, root / "lib/order_content.srv.dart")
            self.assertTrue(generated.is_file())
            service_source = generated.read_text(encoding="utf-8")
            self.assertIn(
                "@Body() OrderContentBffReq request",
                service_source,
            )
            self.assertIn("@RestApi()", service_source)
            self.assertIn("factory OrderContentService(Dio dio)", service_source)
            self.assertNotIn("extension OrderContentServiceOperations", service_source)

            get_result = self.run_command(root, "fvm", "flutter", "pub", "get")
            self.assertEqual(get_result.returncode, 0, get_result.stderr)
            build_result = self.run_command(
                root,
                "fvm",
                "dart",
                "run",
                "build_runner",
                "build",
            )
            self.assertEqual(build_result.returncode, 0, build_result.stderr)

            generated_impl = root / "lib/order_content.srv.g.dart"
            self.assertTrue(generated_impl.is_file(), build_result.stdout)
            implementation_source = generated_impl.read_text(encoding="utf-8")
            self.assertIn("class _OrderContentService", implementation_source)
            self.assertIn("_data.addAll(request.toJson())", implementation_source)
            self.assertNotIn("final _data = request", implementation_source)

            (root / "bin").mkdir()
            (root / "bin/check_service.dart").write_text(
                "import 'package:dio/dio.dart';\n"
                "import 'package:retrofit_codegen_fixture/order_content.srv.dart';\n"
                "void main() {\n"
                "  final dio = Dio(BaseOptions(baseUrl: 'https://api.example.com'));\n"
                "  final before = dio.interceptors.length;\n"
                "  OrderContentService(dio);\n"
                "  OrderContentService(dio);\n"
                "  final after = dio.interceptors.length;\n"
                "  if (after != before) throw StateError('interceptors changed');\n"
                "}\n",
                encoding="utf-8",
            )
            service_result = self.run_command(
                root, "fvm", "dart", "run", "bin/check_service.dart"
            )
            self.assertEqual(service_result.returncode, 0, service_result.stderr)

            analyze_result = self.run_command(root, "fvm", "flutter", "analyze")
            self.assertEqual(analyze_result.returncode, 0, analyze_result.stdout)


if __name__ == "__main__":
    unittest.main()

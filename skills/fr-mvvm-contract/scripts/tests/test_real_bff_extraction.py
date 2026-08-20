#!/usr/bin/env python3
"""Real fr_acdd-to-BFF integration coverage without a fake FVM extractor."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPTS.parents[2]
UV_RUN_SCRIPT = ("uv", "run", "--script")


class RealBffExtractionTest(unittest.TestCase):
    def test_library_shell_extraction_generates_v9_interactions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fr_acdd = REPO_ROOT / "packages/fr_acdd"
            (root / "pubspec.yaml").write_text(
                "name: real_bff_fixture\n"
                "environment:\n  sdk: ^3.7.0\n"
                "dependencies:\n"
                f"  fr_acdd:\n    path: {fr_acdd}\n",
                encoding="utf-8",
            )
            directory = root / "lib/order"
            directory.mkdir(parents=True)
            component = directory / "order.dart"
            component.write_text(
                "import 'package:fr_acdd/fr_acdd.dart';\n"
                "part 'order.c.dart';\n"
                "part 'order.v.dart';\n",
                encoding="utf-8",
            )
            (directory / "order.c.dart").write_text(
                "/// Figma:\n"
                "/// - Node: https://www.figma.com/design/orders?node-id=1-2\n"
                "/// State Ownership: component-owned [OrderViewModel]\n"
                "/// Public Views: [OrderView]\n"
                "/// Widget Tree: [OrderView] > [RetryButton]\n"
                "/// Theme: none\n"
                "/// Events: [OrderStarted], [OrderSubmitted]\n"
                "/// ViewModels: [OrderViewModel]\n"
                "/// Models: [OrderModel]\n"
                "/// BFF-UI-API:\n"
                "/// GET /orders/:orderId\n"
                "/// [LoadOrderBffReq], [LoadOrderBffRsp]\n"
                "/// POST /orders/:orderId/submit\n"
                "/// [SubmitOrderBffReq], [SubmitOrderBffRsp]\n"
                "/// Behaviors:\n"
                "/// - Endpoint: [LoadOrderBffReq]\n"
                "/// - UI Data: order details\n"
                "/// - Source: approved order requirements\n"
                "/// - Loading/Refresh: load on entry and retain data on refresh\n"
                "/// - Empty/Error: missing order is empty; failure supports retry\n"
                "/// - Endpoint: [SubmitOrderBffReq]\n"
                "/// - Effect: submit the approved order\n"
                "/// - Success: confirmationId proves submission\n"
                "/// - Failure: rejected -> restore submit state and show reason\n"
                "/// - Navigation: app\n"
                "/// Request Field Sources:\n"
                "/// - Endpoint: [LoadOrderBffReq]\n"
                "/// - orderId <- OrderPage.orderId | selects the order\n"
                "/// - Endpoint: [SubmitOrderBffReq]\n"
                "/// - orderId <- OrderModel.orderId | selects the order\n"
                "/// Interactions:\n"
                "/// - Flow: load-order\n"
                "/// - Trigger: external integration-test\n"
                "/// - Event: [OrderStarted]\n"
                "/// - Uses: ui-api [LoadOrderBffReq]\n"
                "/// - Guard: [OrderModel].isLoading == false\n"
                "/// - Pending State: [OrderModel].isLoading = true; [OrderModel].error = null\n"
                "/// - Success State: [OrderModel].title <- [LoadOrderBffRsp].title; [OrderModel].isLoading = false\n"
                "/// - Failure State: [OrderModel].error <- error; [OrderModel].isLoading = false\n"
                "/// - Concurrency: latest-wins\n"
                "/// - Navigation: none\n"
                "/// - Flow: submit-order\n"
                "/// - Trigger: external integration-submit\n"
                "/// - Event: [OrderSubmitted]\n"
                "/// - Uses: ui-api [SubmitOrderBffReq]\n"
                "/// - Guard: [OrderModel].isSubmitting == false\n"
                "/// - Pending State: [OrderModel].isSubmitting = true; [OrderModel].error = null\n"
                "/// - Success State: [OrderModel].confirmationId <- [SubmitOrderBffRsp].confirmationId; [OrderModel].isSubmitting = false\n"
                "/// - Failure State: [OrderModel].error <- error; [OrderModel].isSubmitting = false\n"
                "/// - Concurrency: ignore-while-active\n"
                "/// - Navigation: app-on-success\n"
                "/// BFF Service: [OrderService]\n"
                "part of 'order.dart';\n\n"
                "class OrderModel {\n"
                "  const factory OrderModel({required String orderId, required String title, required String confirmationId, required bool isLoading, required bool isSubmitting, String? error}) = OrderModelImpl;\n"
                "}\n"
                "@FrAcddDto(kind: FrAcddDtoKind.root)\n"
                "@FrAcddFreezedJSON\n"
                "abstract class LoadOrderBffReq with _$LoadOrderBffReq {\n"
                "  const factory LoadOrderBffReq({required String orderId}) = _LoadOrderBffReq;\n"
                "  factory LoadOrderBffReq.fromJson(Map<String, dynamic> json) => _$LoadOrderBffReqFromJson(json);\n"
                "  Map<String, dynamic> toJson();\n"
                "}\n"
                "@FrAcddDto(kind: FrAcddDtoKind.root)\n"
                "@FrAcddFreezedJSON\n"
                "abstract class LoadOrderBffRsp with _$LoadOrderBffRsp {\n"
                "  const factory LoadOrderBffRsp({required String title}) = _LoadOrderBffRsp;\n"
                "  factory LoadOrderBffRsp.fromJson(Map<String, dynamic> json) => _$LoadOrderBffRspFromJson(json);\n"
                "}\n"
                "@FrAcddDto(kind: FrAcddDtoKind.root)\n"
                "@FrAcddFreezedJSON\n"
                "abstract class SubmitOrderBffReq with _$SubmitOrderBffReq {\n"
                "  const factory SubmitOrderBffReq({required String orderId}) = _SubmitOrderBffReq;\n"
                "  factory SubmitOrderBffReq.fromJson(Map<String, dynamic> json) => _$SubmitOrderBffReqFromJson(json);\n"
                "  Map<String, dynamic> toJson();\n"
                "}\n"
                "@FrAcddDto(kind: FrAcddDtoKind.root)\n"
                "@FrAcddFreezedJSON\n"
                "abstract class SubmitOrderBffRsp with _$SubmitOrderBffRsp {\n"
                "  const factory SubmitOrderBffRsp({required String confirmationId}) = _SubmitOrderBffRsp;\n"
                "  factory SubmitOrderBffRsp.fromJson(Map<String, dynamic> json) => _$SubmitOrderBffRspFromJson(json);\n"
                "}\n"
                "class OrderStarted {}\n"
                "class OrderSubmitted {}\n",
                encoding="utf-8",
            )
            (directory / "order.v.dart").write_text(
                "part of 'order.dart';\n"
                "@FrAcddPage(mode: FrAcddMode.bff, namespace: 'order', version: 2)\n"
                "class OrderView {}\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["fvm", "dart", "pub", "get"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )

            result = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "generate_bff.py"),
                    "--component-file",
                    str(component),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            artifact = component.with_suffix(".bff.md").read_text(encoding="utf-8")
            self.assertIn('schema: "bff-md-meta/v9"', artifact)
            self.assertIn("### 前端交互逻辑", artifact)
            self.assertIn("#### load-order", artifact)
            self.assertIn("#### [LoadOrderBffReq] · query", artifact)
            self.assertIn("#### GET /orders/:orderId", artifact)
            self.assertIn("#### POST /orders/:orderId/submit", artifact)
            self.assertIn("#### [SubmitOrderBffReq] · command", artifact)
            self.assertIn("#### submit-order", artifact)


if __name__ == "__main__":
    unittest.main()

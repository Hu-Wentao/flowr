#!/usr/bin/env python3
"""Tests for BFF backend OpenAPI operation references."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from contract_core import ContractError  # noqa: E402
from openapi_refs import (  # noqa: E402
    BusinessApi,
    generated_sdk_operations,
    generated_sdk_type_fields,
    parse_business_apis,
    parse_backend_calls,
    validate_bff_business_apis,
    validate_backend_calls,
    validate_direct_business_api_requests,
    validate_legacy_backend_calls,
)


def openapi_document(*operations: tuple[str, str]) -> bytes:
    paths: dict[str, dict[str, object]] = {}
    for method, path in operations:
        paths.setdefault(path, {})[method.lower()] = {"responses": {"200": {}}}
    return json.dumps({"openapi": "3.0.1", "paths": paths}).encode()


class NetworkResponse(BytesIO):
    def __init__(self, payload: bytes, url: str) -> None:
        super().__init__(payload)
        self.url = url

    def geturl(self) -> str:
        return self.url

    def __enter__(self) -> "NetworkResponse":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class OpenApiReferencesTest(unittest.TestCase):
    def test_direct_business_api_request_requires_exact_sdk_typedef(self) -> None:
        calls = (
            BusinessApi(
                "applyAccount",
                "POST",
                "/app/customer/oao/openAcc/apply",
                "body ReqWrapper<OaoApplyOpenAccReq>",
                "RspWrapper<OaoApplyOpenAccRes>",
            ),
        )
        endpoints = (
            (
                "POST",
                "/app/customer/oao/openAcc/apply",
                "CustomerOnboardingIdentityBffReq",
            ),
        )

        boundaries = validate_direct_business_api_requests(
            calls,
            endpoints,
            dart_sources=(
                "typedef CustomerOnboardingIdentityBffReq = "
                "sdk.OaoApplyOpenAccReq;",
            ),
        )

        self.assertEqual(boundaries[0].request_type, "CustomerOnboardingIdentityBffReq")
        self.assertEqual(boundaries[0].sdk_request_type, "OaoApplyOpenAccReq")

    def test_direct_business_api_request_rejects_replacement_wrapper(self) -> None:
        calls = (
            BusinessApi(
                "applyAccount",
                "POST",
                "/app/customer/oao/openAcc/apply",
                "body ReqWrapper<OaoApplyOpenAccReq>",
                "RspWrapper<OaoApplyOpenAccRes>",
            ),
        )

        with self.assertRaisesRegex(ContractError, "replacement wrapper DTO"):
            validate_direct_business_api_requests(
                calls,
                (
                    (
                        "POST",
                        "/app/customer/oao/openAcc/apply",
                        "CustomerOnboardingIdentityBffReq",
                    ),
                ),
                dart_sources=(
                    "class CustomerOnboardingIdentityBffReq {}",
                ),
            )

        with self.assertRaisesRegex(ContractError, "exact typedef"):
            validate_direct_business_api_requests(
                calls,
                (
                    (
                        "POST",
                        "/app/customer/oao/openAcc/apply",
                        "CustomerOnboardingIdentityBffReq",
                    ),
                ),
                dart_sources=(
                    "typedef CustomerOnboardingIdentityBffReq = "
                    "sdk.OaoApplyOpenAccReq?;",
                ),
            )

    def test_generated_sdk_type_fields_reads_direct_request_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            component_file = root / "lib/example/example.dart"
            component_file.parent.mkdir(parents=True)
            component_file.write_text("", encoding="utf-8")
            sdk = root / "lib/api/gen/example_api.dart"
            sdk.parent.mkdir(parents=True)
            sdk.write_text(
                "class OaoApplyOpenAccReq {\n"
                "  const OaoApplyOpenAccReq({this.birthDate, this.idNo});\n"
                "  final String? birthDate;\n"
                "  final String? idNo;\n"
                "}\n",
                encoding="utf-8",
            )

            fields = generated_sdk_type_fields(
                component_file, "OaoApplyOpenAccReq"
            )

            self.assertEqual(fields, ("birthDate", "idNo"))

    def test_generated_sdk_operations_accepts_wrapped_zero_argument_method(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            component_file = root / "lib/example/example.dart"
            component_file.parent.mkdir(parents=True)
            component_file.write_text("", encoding="utf-8")
            sdk = root / "lib/api/gen/example_api.dart"
            sdk.parent.mkdir(parents=True)
            sdk.write_text(
                "abstract class ExampleApi {\n"
                "  @POST(\"/app/rules/get\")\n"
                "  Future<RspWrapper<List<RuleDto>>>\n"
                "  postAppRulesGet();\n"
                "}\n",
                encoding="utf-8",
            )

            operations = generated_sdk_operations(component_file)

            self.assertEqual(len(operations), 1)
            self.assertEqual(operations[0].method, "POST")
            self.assertEqual(operations[0].path, "/app/rules/get")
            self.assertEqual(operations[0].operation, "postAppRulesGet")

    def test_backend_bff_annotations_resolve_openapi_and_sdk_types(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            component_file = root / "lib/example/example.dart"
            component_file.parent.mkdir(parents=True)
            component_file.write_text("", encoding="utf-8")
            spec = root / "orders.openapi.json"
            spec.write_bytes(openapi_document(("POST", "/orders")))
            sdk = root / "lib/api/gen/orders_api.dart"
            sdk.parent.mkdir(parents=True)
            sdk.write_text(
                "class CreateOrderReq {}\nclass CreateOrderRsp {}\n",
                encoding="utf-8",
            )
            content = (
                "## 后端业务流程与业务逻辑 API\n\n"
                "### 业务逻辑 API\n\n"
                "- [create] POST /orders | Parameters: body CreateOrderReq "
                "| Response: CreateOrderRsp\n\n"
                "### 业务流程\n\n"
                "- [create] 创建订单\n"
                "## 前端 UI 数据接口\n"
            )

            calls = validate_bff_business_apis(content, component_file)

            self.assertEqual(calls[0].parameters, "body CreateOrderReq")
            self.assertEqual(calls[0].response_type, "CreateOrderRsp")

    def test_backend_bff_accepts_tight_separators_and_prose_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".git").mkdir()
            component_file = root / "lib/example/example.dart"
            component_file.parent.mkdir(parents=True)
            component_file.write_text("", encoding="utf-8")
            (root / "orders.openapi.json").write_bytes(
                openapi_document(("POST", "/orders"))
            )
            sdk = root / "lib/api/gen/orders_api.dart"
            sdk.parent.mkdir(parents=True)
            sdk.write_text(
                "class CreateOrderReq {}\nclass RspWrapper<T> {}\n",
                encoding="utf-8",
            )
            content = (
                "## 后端业务流程与业务逻辑 API\n\n"
                "### 业务逻辑 API\n\n"
                "- [create] POST /orders|Parameters: body CreateOrderReq（mode=OTP）"
                "|Response: RspWrapper<Void>（AOP 校验后 data.token）\n\n"
                "### 业务流程\n\n"
                "- [create] 创建订单\n"
                "## 前端 UI 数据接口\n"
            )

            calls = validate_bff_business_apis(content, component_file)

            self.assertEqual(calls[0].parameters, "body CreateOrderReq（mode=OTP）")
            self.assertEqual(
                calls[0].response_type,
                "RspWrapper<Void>（AOP 校验后 data.token）",
            )

    def test_backend_bff_accepts_json_and_dto_examples(self) -> None:
        content = (
            "## 后端业务流程与业务逻辑 API\n\n"
            "### 业务逻辑 API\n\n"
            "- none\n\n"
            "DTO 示例：\n\n"
            "```json\n{\"loginId\":\"value\"}\n```\n\n"
            "### 业务流程\n\n"
            "先获取认证方式，再提交认证信息。\n\n"
            "参数示例：\n"
            "{\n  \"auth\": {\"authCode\": \"66666\"}\n}\n"
            "## 前端 UI 数据接口\n"
        )

        calls, flow = parse_business_apis(content)

        self.assertEqual(calls, ())
        self.assertIn("参数示例：", flow)
        self.assertIn('"auth": {"authCode": "66666"}', flow)

    def test_backend_bff_ignores_examples_beside_machine_api_entries(self) -> None:
        content = (
            "## 后端业务流程与业务逻辑 API\n\n"
            "### 业务逻辑 API\n\n"
            "- [create] POST /orders | Parameters: body CreateOrderReq "
            "| Response: CreateOrderRsp\n\n"
            "DTO 示例：\n\n"
            "```json\n{\"orderId\":\"A-1\"}\n```\n\n"
            "### 业务流程\n\n"
            "- [create] 创建订单\n\n"
            "响应示例： {\"code\":\"00000000\"}\n"
            "## 前端 UI 数据接口\n"
        )

        calls, flow = parse_business_apis(content)

        self.assertEqual([call.call_id for call in calls], ["create"])
        self.assertIn('响应示例： {"code":"00000000"}', flow)

    def component(
        self,
        root: Path,
        *,
        calls: list[str],
        flow: list[str],
    ) -> SimpleNamespace:
        (root / ".git").mkdir(exist_ok=True)
        component_file = root / "lib/example/example.dart"
        component_file.parent.mkdir(parents=True, exist_ok=True)
        component_file.write_text("", encoding="utf-8")
        return SimpleNamespace(
            component_file=str(component_file),
            sections={"Backend Calls": calls, "Backend Call Flow": flow},
        )

    def configure_openapi_root(self, root: Path, relative_root: str) -> None:
        config = root / ".agents/skills-config/fr-mvvm-contract/config.yaml"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(
            "\n".join(
                [
                    "schema: fr-mvvm-contract.config.v1",
                    "profile: test-project",
                    "transport:",
                    "  backend_openapi:",
                    f"    local_root: {relative_root}",
                    "tasks:",
                    "  validate:",
                    "    base: references/validate.md",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def test_one_local_document_can_resolve_multiple_api_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.configure_openapi_root(root, "build/api-docs/api/app-backend")
            spec = root / "build/api-docs/api/app-backend/openapi/account.openapi.json"
            spec.parent.mkdir(parents=True)
            spec.write_bytes(
                openapi_document(
                    ("POST", "/accounts"),
                    ("GET", "/accounts/{accountId}"),
                )
            )
            component = self.component(
                root,
                calls=[
                    "- createAccount <- openapi/account.openapi.json | POST /accounts",
                    "- getAccount <- openapi/account.openapi.json | GET /accounts/{accountId}",
                ],
                flow=[
                    "- [createAccount] 创建账户",
                    "- [getAccount] 读取创建后的账户",
                ],
            )

            calls = validate_legacy_backend_calls(component)

        self.assertEqual(
            [call.call_id for call in calls], ["createAccount", "getAccount"]
        )
        self.assertEqual(calls[1].path, "/accounts/{accountId}")

    def test_http_openapi_url_is_loaded_and_operation_path_is_retained(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            url = "https://api.example.com/specs/account.openapi.json"
            component = self.component(
                root,
                calls=[f"- getAccount <- {url} | GET /accounts/{{accountId}}"],
                flow=["- [getAccount] 读取账户"],
            )
            response = NetworkResponse(
                openapi_document(("GET", "/accounts/{accountId}")), url
            )
            with mock.patch("openapi_refs.urlopen", return_value=response) as request:
                calls = validate_legacy_backend_calls(component)

        self.assertEqual(calls[0].location, url)
        self.assertEqual(calls[0].path, "/accounts/{accountId}")
        request.assert_called_once()

    def test_missing_operation_and_unreferenced_flow_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = root / "account.openapi.json"
            spec.write_bytes(openapi_document(("GET", "/accounts")))
            component = self.component(
                root,
                calls=["- createAccount <- account.openapi.json | POST /accounts"],
                flow=["- [createAccount] 创建账户"],
            )
            with self.assertRaisesRegex(ContractError, "operation does not exist"):
                validate_legacy_backend_calls(component)

            component.sections["Backend Call Flow"] = ["- 调用后端"]
            with self.assertRaisesRegex(ContractError, r"\[createAccount\]"):
                validate_legacy_backend_calls(component)

    def test_location_must_be_project_relative_or_http_and_use_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for location, expected in (
                ("../outside.openapi.json", "escapes its configured local root"),
                ("file:///tmp/account.openapi.json", "must use http or https"),
                ("docs/account.json", "must end with `.openapi.json`"),
            ):
                with self.subTest(location=location):
                    component = self.component(
                        root,
                        calls=[f"- account <- {location} | GET /accounts"],
                        flow=["- [account] 读取账户"],
                    )
                    if location.endswith("account.json"):
                        with self.assertRaisesRegex(ContractError, expected):
                            parse_backend_calls(component)
                    else:
                        with self.assertRaisesRegex(ContractError, expected):
                            validate_legacy_backend_calls(component)

    def test_backend_sections_must_be_declared_together(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.component(
                Path(temporary), calls=["- none"], flow=["- none"]
            )
            component.sections.pop("Backend Call Flow")

            with self.assertRaisesRegex(ContractError, "declared together"):
                validate_legacy_backend_calls(component)

            component.sections["Backend Call Flow"] = []
            with self.assertRaisesRegex(ContractError, "must both be `- none`"):
                validate_legacy_backend_calls(component)


if __name__ == "__main__":
    unittest.main()

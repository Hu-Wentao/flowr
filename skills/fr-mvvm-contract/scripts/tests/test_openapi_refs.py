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
    parse_business_apis,
    parse_backend_calls,
    validate_bff_business_apis,
    validate_backend_calls,
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

    def test_backend_bff_rejects_dto_fields(self) -> None:
        content = (
            "## 后端业务流程与业务逻辑 API\n\n"
            "### 业务逻辑 API\n\n"
            "```json\n{\"loginId\":\"value\"}\n```\n\n"
            "### 业务流程\n\n- none\n"
            "## 前端 UI 数据接口\n"
        )

        with self.assertRaisesRegex(ContractError, "must not contain DTO fields"):
            parse_business_apis(content)

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

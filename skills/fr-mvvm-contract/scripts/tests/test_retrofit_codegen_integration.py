#!/usr/bin/env python3
"""Ensure BFF generation never creates a frontend Retrofit service."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from contract_parser import parse_component  # noqa: E402
from generate_service import generate_service  # noqa: E402


class RetrofitCodegenIntegrationTest(unittest.TestCase):
    def test_bff_service_generation_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "lib/order_content"
            directory.mkdir(parents=True)
            component = directory / "order_content.dart"
            component.write_text(
                "part 'order_content.c.dart';\n", encoding="utf-8"
            )
            (directory / "order_content.c.dart").write_text(
                "part of 'order_content.dart';\n"
                "/// State Ownership: none\n"
                "/// BFF-API:\n"
                "/// GET /orders\n"
                "/// [OrderContentBffReq], [OrderContentBffRsp]\n"
                "/// BFF Service: [OrderContentService]\n"
                "class OrderContentView {}\n",
                encoding="utf-8",
            )
            component.with_suffix(".bff.md").write_text(
                "## 后端业务流程与业务逻辑 API\n\n"
                "### 业务逻辑 API\n\n- none\n\n"
                "### 业务流程\n\n- none\n"
                "## 前端 UI 数据接口\n\n"
                "#### GET /orders\n"
                "- Request DTOs: [OrderContentBffReq]\n"
                "- Response DTOs: [OrderContentBffRsp]\n",
                encoding="utf-8",
            )

            generated = generate_service(parse_component(component), check=False)

            self.assertIsNone(generated)
            self.assertFalse(directory.joinpath("order_content.srv.dart").exists())
            self.assertFalse(directory.joinpath("order_content.srv.g.dart").exists())


if __name__ == "__main__":
    unittest.main()

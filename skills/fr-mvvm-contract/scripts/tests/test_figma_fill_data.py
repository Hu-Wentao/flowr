#!/usr/bin/env python3
"""Regression tests for Figma fill-data contracts and audit reporting."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from contract_core import ContractError  # noqa: E402
from figma_fill_data import audit_figma_fill_data, parse_figma_fill_data  # noqa: E402


class FigmaFillDataTest(unittest.TestCase):
    def sections(self, lines: list[str]) -> dict[str, list[str]]:
        return {"Figma Data": lines}

    def test_parses_bound_pending_and_static_entries(self) -> None:
        entries = parse_figma_fill_data(
            self.sections(
                [
                    "- [profile.agent.username] | Node: 1:2 | Kind: remote | Binding: bound | Render: ProfileModel.username | Source: UserInfoDto.username | Fixture: profile.agent.username",
                    "- [profile.agent.mobile] | Node: 1:3 | Kind: remote | Binding: pending | Render: ProfileModel.mobile | Source: TODO(figma-data): awaiting user profile authority | Fixture: profile.agent.mobile",
                    "- [profile.title] | Node: 1:4 | Kind: static-copy | Binding: static",
                ]
            )
        )

        self.assertEqual(
            [entry.binding for entry in entries], ["bound", "pending", "static"]
        )

    def test_rejects_pending_without_todo_and_static_without_copy_kind(self) -> None:
        with self.assertRaisesRegex(ContractError, "pending Source"):
            parse_figma_fill_data(
                self.sections(
                    [
                        "- [profile.agent.mobile] | Node: 1:3 | Kind: remote | Binding: pending | Render: ProfileModel.mobile | Source: UserInfoDto.mobile | Fixture: profile.agent.mobile"
                    ]
                )
            )
        with self.assertRaisesRegex(ContractError, "static-copy"):
            parse_figma_fill_data(
                self.sections(
                    ["- [profile.agent.mobile] | Node: 1:3 | Kind: remote | Binding: static"]
                )
            )

    def test_audit_reports_legacy_and_pending_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contracts = root / "lib/app"
            contracts.mkdir(parents=True)
            (contracts / "legacy.c.dart").write_text(
                "/// Figma:\n/// - Node: https://figma.test/?node-id=1-1\n",
                encoding="utf-8",
            )
            (contracts / "profile.c.dart").write_text(
                "/// Figma:\n/// - Node: https://figma.test/?node-id=1-2\n"
                "/// Figma Data:\n"
                "/// - [profile.agent.mobile] | Node: 1:2 | Kind: remote | Binding: pending | Render: ProfileModel.mobile | Source: TODO(figma-data): awaiting authority | Fixture: profile.agent.mobile\n",
                encoding="utf-8",
            )
            report = audit_figma_fill_data(root)

        self.assertEqual(report["summary"]["legacy_unreviewed"], 1)
        self.assertEqual(report["summary"]["pending"], 1)


if __name__ == "__main__":
    unittest.main()

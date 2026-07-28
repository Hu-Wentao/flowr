#!/usr/bin/env python3
"""Tests for global Figma release selection and page-level exceptions."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SCRIPT_DIR = TEST_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from figma_release import (  # noqa: E402
    FigmaReleaseError,
    load_figma_release_catalog,
    resolve_contract_figma_release,
)


class FigmaReleaseTest(unittest.TestCase):
    """Global release metadata must resolve concrete contract file keys."""

    def _write_config(
        self,
        root: Path,
        *,
        active: str = "v2",
        enforcement: str = "gradual",
    ) -> None:
        config = root / ".agents" / "skills-config" / "fr-mvvm-contract" / "config.yaml"
        config.parent.mkdir(parents=True)
        config.write_text(
            "schema: fr-mvvm-contract.config.v1\n"
            "profile: fixture\n"
            "figma:\n"
            f"  active_release: {active}\n"
            f"  enforcement: {enforcement}\n"
            "  releases:\n"
            "    v1:\n"
            "      file_key: oldFile\n"
            "      status: archived\n"
            "    v2:\n"
            "      file_key: activeFile\n"
            f"      status: {'active' if active == 'v2' else 'candidate'}\n"
            "    v3:\n"
            "      file_key: candidateFile\n"
            "      status: candidate\n",
            encoding="utf-8",
        )

    def _write_contract(
        self,
        root: Path,
        *,
        file_key: str,
        override: str = "",
    ) -> Path:
        contract = root / "lib/order/order.c.dart"
        contract.parent.mkdir(parents=True, exist_ok=True)
        contract.write_text(
            "/// Figma:\n"
            "/// - Frame: Order\n"
            "/// - Node: "
            f"https://www.figma.com/design/{file_key}/Fixture?node-id=1-2\n"
            f"{override}"
            "/// Figma Fidelity: excluded | fixture\n"
            "part of 'order.dart';\n",
            encoding="utf-8",
        )
        return contract

    def test_resolves_current_release(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._write_config(root)
            contract = self._write_contract(root, file_key="activeFile")

            result = resolve_contract_figma_release(root, contract)

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.status, "current")
        self.assertFalse(result.migration_required)

    def test_marks_archived_release_stale_in_gradual_mode(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._write_config(root)
            contract = self._write_contract(root, file_key="oldFile")

            result = resolve_contract_figma_release(root, contract)

        assert result is not None
        self.assertEqual(result.status, "stale")
        self.assertTrue(result.migration_required)
        self.assertEqual(
            result.action,
            "inspect-active-release-and-migrate-touched-contract",
        )

    def test_reasoned_override_pins_archived_release(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._write_config(root)
            contract = self._write_contract(
                root,
                file_key="oldFile",
                override=(
                    "/// Figma Release Override:\n"
                    "/// - Release: v1\n"
                    "/// - Reason: V2 has no approved error state\n"
                    "/// - Review After: 2026-08-15\n"
                ),
            )

            result = resolve_contract_figma_release(root, contract)

        assert result is not None
        self.assertEqual(result.status, "pinned")
        self.assertEqual(
            result.override.reason if result.override else None,
            "V2 has no approved error state",
        )

    def test_rejects_override_that_does_not_match_concrete_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._write_config(root)
            contract = self._write_contract(
                root,
                file_key="oldFile",
                override=(
                    "/// Figma Release Override:\n"
                    "/// - Release: v2\n"
                    "/// - Reason: invalid fixture\n"
                ),
            )

            with self.assertRaisesRegex(
                FigmaReleaseError,
                "must match the contract file_key",
            ):
                resolve_contract_figma_release(root, contract)

    def test_candidate_and_unknown_releases_block(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._write_config(root)
            candidate = self._write_contract(root, file_key="candidateFile")
            candidate_result = resolve_contract_figma_release(root, candidate)
            unknown = self._write_contract(root, file_key="unregisteredFile")
            unknown_result = resolve_contract_figma_release(root, unknown)

        assert candidate_result is not None
        assert unknown_result is not None
        self.assertEqual(candidate_result.status, "candidate")
        self.assertEqual(unknown_result.status, "unknown")

    def test_catalog_requires_exactly_configured_active_status(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._write_config(root, active="v1")

            with self.assertRaisesRegex(
                FigmaReleaseError,
                "exactly figma.active_release",
            ):
                load_figma_release_catalog(root)

    def test_without_release_config_preserves_contract_only_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            contract = self._write_contract(root, file_key="legacyFile")

            result = resolve_contract_figma_release(root, contract)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

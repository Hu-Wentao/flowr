#!/usr/bin/env python3
"""Tests for the generic Figma fidelity audit."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
SCRIPT_DIR = TEST_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from audit_figma_fidelity import (  # noqa: E402
    AuditConfigError,
    audit,
    audit_discovered,
)


class AuditFigmaFidelityTest(unittest.TestCase):
    """Profile validation and invariant checks."""

    def _write_profile(
        self, root: Path, *, asset_hash: str, asset_path: str = "assets/icon.svg"
    ) -> Path:
        profile = {
            "schema": "fr-mvvm-contract.figma-fidelity.v1",
            "id": "fixture",
            "figma_file_key": "file",
            "primary_node": "1:2",
            "viewport": {"width": 360, "height": 780},
            "assets": [
                {
                    "name": "icon",
                    "path": asset_path,
                    "source_export": "icon",
                    "sha256": asset_hash,
                }
            ],
            "checks": [
                {
                    "name": "shell",
                    "kind": "source_rules",
                    "detail": "shell tokens remain present",
                    "rules": [
                        {
                            "path": "lib/view.dart",
                            "contains": ["SharedShell"],
                            "excludes": ["Icons."],
                        }
                    ],
                },
                {
                    "name": "single_owner",
                    "kind": "unique_text",
                    "detail": "node has one owner",
                    "globs": ["lib/**/*.dart"],
                    "values": ["1:2"],
                    "expected": 1,
                },
                {
                    "name": "legacy_absent",
                    "kind": "paths_absent",
                    "detail": "legacy owner stays removed",
                    "paths": ["lib/legacy.dart"],
                },
            ],
        }
        path = root / "profile.json"
        path.write_text(json.dumps(profile), encoding="utf-8")
        return path

    def _fixture(self, root: Path) -> tuple[Path, str]:
        asset = root / "assets/icon.svg"
        asset.parent.mkdir(parents=True)
        asset.write_text("<svg/>", encoding="utf-8")
        view = root / "lib/view.dart"
        view.parent.mkdir(parents=True)
        view.write_text("// SharedShell 1:2", encoding="utf-8")
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()
        return asset, digest

    def _write_contract(self, root: Path, disposition: str | None) -> Path:
        contract = root / "lib/order/order.c.dart"
        contract.parent.mkdir(parents=True, exist_ok=True)
        fidelity = (
            f"/// Figma Fidelity: {disposition}\n"
            if disposition is not None
            else ""
        )
        contract.write_text(
            "/// Figma:\n"
            "/// - Frame: Order\n"
            "/// - Node: https://www.figma.com/design/file/Fixture?node-id=1-2\n"
            f"{fidelity}"
            "/// State Ownership: none\n"
            "part of 'order.dart';\n",
            encoding="utf-8",
        )
        return contract

    def test_passing_profile_runs_all_kinds(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            _, digest = self._fixture(root)
            checks = audit(root, self._write_profile(root, asset_hash=digest))

        self.assertEqual(
            [check.name for check in checks],
            [
                "exact_figma_assets",
                "shell",
                "single_owner",
                "legacy_absent",
            ],
        )
        self.assertTrue(all(check.passed for check in checks))

    def test_asset_hash_failure_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._fixture(root)
            checks = audit(root, self._write_profile(root, asset_hash="0" * 64))

        self.assertFalse(checks[0].passed)
        self.assertIn("hash:assets/icon.svg", checks[0].detail)

    def test_source_rule_reports_forbidden_substitute(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            _, digest = self._fixture(root)
            (root / "lib/view.dart").write_text(
                "// SharedShell 1:2 Icons.search", encoding="utf-8"
            )
            checks = audit(root, self._write_profile(root, asset_hash=digest))

        shell = next(check for check in checks if check.name == "shell")
        self.assertFalse(shell.passed)
        self.assertIn("forbidden-text:Icons.", shell.detail)

    def test_profile_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            _, digest = self._fixture(root)
            profile = self._write_profile(
                root, asset_hash=digest, asset_path="../outside.svg"
            )

            with self.assertRaisesRegex(AuditConfigError, "repository-relative"):
                audit(root, profile)

    def test_discovery_runs_profile_declared_by_contract(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            _, digest = self._fixture(root)
            self._write_profile(root, asset_hash=digest)
            self._write_contract(root, "profile | profile.json")

            checks = audit_discovered(root)

        self.assertTrue(all(check.passed for check in checks))
        self.assertEqual(checks[0].name, "figma_fidelity_coverage")
        self.assertIn(
            "fixture:exact_figma_assets",
            [check.name for check in checks],
        )

    def test_discovery_rejects_primary_contract_without_disposition(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._write_contract(root, None)

            checks = audit_discovered(root)

        self.assertFalse(checks[0].passed)
        self.assertIn(
            "missing-disposition:lib/order/order.c.dart",
            checks[0].detail,
        )

    def test_discovery_reports_explicit_exclusion_without_approving_profile(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._write_contract(
                root,
                "excluded | visual fidelity has not been audited",
            )

            checks = audit_discovered(root)

        self.assertTrue(checks[0].passed)
        self.assertEqual(len(checks), 2)
        self.assertIn("visual fidelity has not been audited", checks[1].detail)

    def test_discovery_rejects_profile_binding_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            _, digest = self._fixture(root)
            profile = self._write_profile(root, asset_hash=digest)
            content = json.loads(profile.read_text(encoding="utf-8"))
            content["primary_node"] = "9:9"
            profile.write_text(json.dumps(content), encoding="utf-8")
            self._write_contract(root, "profile | profile.json")

            checks = audit_discovered(root)

        self.assertFalse(checks[0].passed)
        self.assertIn("profile-binding-mismatch", checks[0].detail)


if __name__ == "__main__":
    unittest.main()

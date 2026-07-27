#!/usr/bin/env python3
"""Tests for contract-discovered Figma fidelity and pure asset locks."""

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
    audit_asset_lock,
    audit_discovered,
)


class AuditFigmaFidelityTest(unittest.TestCase):
    """Contract authority, lock validation, and generic verification."""

    def _write_asset_lock(
        self,
        root: Path,
        *,
        asset_hash: str,
        asset_path: str = "assets/icon.svg",
        lock_name: str = "icon-figma-assets.lock.json",
    ) -> Path:
        lock = {
            "schema": "fr-mvvm-contract.figma-assets-lock.v1",
            "assets": [
                {
                    "name": "icon",
                    "path": asset_path,
                    "source_export": "fixture_icon",
                    "sha256": asset_hash,
                }
            ],
        }
        path = root / lock_name
        path.write_text(json.dumps(lock), encoding="utf-8")
        return path

    def _fixture(self, root: Path) -> tuple[Path, str]:
        asset = root / "assets/icon.svg"
        asset.parent.mkdir(parents=True)
        asset.write_text("<svg/>", encoding="utf-8")
        view = root / "lib/order/order.v.dart"
        view.parent.mkdir(parents=True)
        view.write_text(
            "final icon = SvgPicture.asset('assets/icon.svg');",
            encoding="utf-8",
        )
        test = root / "test/order_test.dart"
        test.parent.mkdir(parents=True)
        test.write_text(
            "testWidgets('orderFigmaFidelity renders the approved screen', "
            "(tester) async { const size = Size(360, 780); });",
            encoding="utf-8",
        )
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()
        return asset, digest

    def _write_contract(
        self,
        root: Path,
        *,
        fidelity_lines: list[str] | None,
        name: str = "order",
        node_id: str = "1-2",
    ) -> Path:
        contract = root / f"lib/{name}/{name}.c.dart"
        contract.parent.mkdir(parents=True, exist_ok=True)
        fidelity = ""
        if fidelity_lines is not None:
            fidelity = "/// Figma Fidelity:\n" + "".join(
                f"/// {line}\n" for line in fidelity_lines
            )
        contract.write_text(
            "/// Figma:\n"
            f"/// - Frame: {name.title()}\n"
            "/// - Node: "
            f"https://www.figma.com/design/file/Fixture?node-id={node_id}\n"
            f"{fidelity}"
            "/// State Ownership: none\n"
            f"part of '{name}.dart';\n",
            encoding="utf-8",
        )
        return contract

    def _audited_fidelity(self, lock_name: str) -> list[str]:
        return [
            "- Viewport: 360 x 780",
            f"- Asset Lock: {lock_name}",
            "- Regression Test: orderFigmaFidelity renders the approved screen",
        ]

    def test_asset_lock_contains_only_exact_export_facts(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            _, digest = self._fixture(root)
            lock = self._write_asset_lock(root, asset_hash=digest)

            checks = audit_asset_lock(root, lock)

        self.assertEqual([check.name for check in checks], ["exact_figma_assets"])
        self.assertTrue(checks[0].passed)

    def test_asset_hash_failure_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._fixture(root)
            lock = self._write_asset_lock(root, asset_hash="0" * 64)

            checks = audit_asset_lock(root, lock)

        self.assertFalse(checks[0].passed)
        self.assertIn("hash:assets/icon.svg", checks[0].detail)

    def test_asset_lock_rejects_semantic_profile_fields(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            _, digest = self._fixture(root)
            lock = self._write_asset_lock(root, asset_hash=digest)
            content = json.loads(lock.read_text(encoding="utf-8"))
            content["primary_node"] = "1:2"
            lock.write_text(json.dumps(content), encoding="utf-8")

            with self.assertRaisesRegex(
                AuditConfigError, "unsupported fields: primary_node"
            ):
                audit_asset_lock(root, lock)

    def test_asset_lock_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            _, digest = self._fixture(root)
            lock = self._write_asset_lock(
                root,
                asset_hash=digest,
                asset_path="../outside.svg",
            )

            with self.assertRaisesRegex(AuditConfigError, "repository-relative"):
                audit_asset_lock(root, lock)

    def test_discovery_runs_contract_and_lock_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            _, digest = self._fixture(root)
            lock = self._write_asset_lock(root, asset_hash=digest)
            self._write_contract(
                root,
                fidelity_lines=self._audited_fidelity(lock.name),
            )

            checks = audit_discovered(root)

        self.assertTrue(all(check.passed for check in checks))
        self.assertEqual(checks[0].name, "figma_fidelity_coverage")
        self.assertIn(
            "lib_order_order:exact_figma_assets",
            [check.name for check in checks],
        )

    def test_discovery_rejects_primary_contract_without_disposition(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._write_contract(root, fidelity_lines=None)

            checks = audit_discovered(root)

        self.assertFalse(checks[0].passed)
        self.assertIn("invalid-disposition", checks[0].detail)

    def test_discovery_reports_explicit_exclusion(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            self._write_contract(
                root,
                fidelity_lines=[
                    "excluded | visual fidelity has not been audited"
                ],
            )

            checks = audit_discovered(root)

        self.assertTrue(checks[0].passed)
        self.assertEqual(len(checks), 2)
        self.assertIn("visual fidelity has not been audited", checks[1].detail)

    def test_discovery_rejects_reused_asset_lock(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            _, digest = self._fixture(root)
            lock = self._write_asset_lock(root, asset_hash=digest)
            self._write_contract(
                root,
                fidelity_lines=self._audited_fidelity(lock.name),
            )
            self._write_contract(
                root,
                name="account",
                node_id="3-4",
                fidelity_lines=self._audited_fidelity(lock.name),
            )

            checks = audit_discovered(root)

        self.assertFalse(checks[0].passed)
        self.assertIn("reused-asset-lock", checks[0].detail)

    def test_discovery_requires_declared_regression_test_and_viewport(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            _, digest = self._fixture(root)
            lock = self._write_asset_lock(root, asset_hash=digest)
            self._write_contract(
                root,
                fidelity_lines=[
                    "- Viewport: 412 x 915",
                    f"- Asset Lock: {lock.name}",
                    "- Regression Test: missingFigmaTest",
                ],
            )

            checks = audit_discovered(root)

        regression = next(
            check for check in checks if check.name.endswith(":regression_test")
        )
        self.assertFalse(regression.passed)
        self.assertIn("missingFigmaTest", regression.detail)
        self.assertIn("Size(412, 915)", regression.detail)

    def test_asset_path_literal_must_be_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            _, digest = self._fixture(root)
            lock = self._write_asset_lock(root, asset_hash=digest)
            (root / "lib/order/order.v.dart").write_text(
                "const iconPath = 'assets/icon.svg';",
                encoding="utf-8",
            )
            self._write_contract(
                root,
                fidelity_lines=self._audited_fidelity(lock.name),
            )

            checks = audit_discovered(root)

        rendered = next(
            check
            for check in checks
            if check.name.endswith(":locked_assets_rendered")
        )
        self.assertFalse(rendered.passed)
        self.assertIn("unrendered:assets/icon.svg", rendered.detail)


if __name__ == "__main__":
    unittest.main()

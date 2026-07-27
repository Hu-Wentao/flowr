#!/usr/bin/env python3
"""Tests for the Figma SVG scan, normalization, and receipt pipeline."""

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

from figma_svg_pipeline import (  # noqa: E402
    SVG_RECEIPT_SCHEMA,
    SvgPipelineError,
    _normalize,
    inspect_svg,
    load_receipt,
    verify_receipt,
)


class FigmaSvgPipelineTest(unittest.TestCase):
    def _svg(self, root: Path, body: str, name: str = "icon.svg") -> Path:
        path = root / "raw" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def test_scan_reports_safe_colors_and_geometry_review(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            path = self._svg(
                root,
                '<svg width="24" height="24" viewBox="0 0 8 14" '
                'preserveAspectRatio="none" overflow="visible">'
                '<path fill="var(--fill-0, #343A45)"/></svg>',
            )

            inspection = inspect_svg(path)

        codes = {finding.code for finding in inspection.findings}
        self.assertEqual(inspection.safe_color_replacements, 1)
        self.assertIn("normalizable_css_color", codes)
        self.assertIn("aspect_ratio_mismatch", codes)
        self.assertIn("stretched_aspect_ratio", codes)
        self.assertIn("visible_overflow", codes)

    def test_normalize_preserves_source_and_writes_dual_hash_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = self._svg(
                root,
                '<svg width="16" height="16" viewBox="0 0 16 16">'
                '<path fill="var(--fill-0, #ABCDEF)"/></svg>',
            )
            original = source.read_bytes()
            receipt = root / "config/icon-figma-svg-normalization.json"

            payload = _normalize(
                root,
                [source],
                root / "assets/runtime",
                receipt,
            )

            runtime = root / "assets/runtime/icon.svg"
            self.assertEqual(source.read_bytes(), original)
            self.assertIn('fill="#ABCDEF"', runtime.read_text(encoding="utf-8"))
            asset = payload["assets"][0]
            self.assertEqual(payload["schema"], SVG_RECEIPT_SCHEMA)
            self.assertEqual(
                asset["source_export_sha256"],
                hashlib.sha256(original).hexdigest(),
            )
            self.assertEqual(
                asset["runtime_asset_sha256"],
                hashlib.sha256(runtime.read_bytes()).hexdigest(),
            )
            self.assertEqual(verify_receipt(root, receipt), [])

    def test_project_relative_output_and_receipt_are_rooted_at_project(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = self._svg(
                root,
                '<svg width="16" height="16" viewBox="0 0 16 16">'
                '<path stroke="var(--stroke-0, #123456)"/></svg>',
            )

            _normalize(
                root,
                [source],
                Path("assets/runtime"),
                Path("config/receipt.json"),
            )

            self.assertTrue((root / "assets/runtime/icon.svg").is_file())
            self.assertEqual(
                verify_receipt(root, Path("config/receipt.json")),
                [],
            )

    def test_normalize_refuses_unresolved_variables_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = self._svg(
                root,
                '<svg viewBox="0 0 16 16"><path fill="var(--fill-0)"/></svg>',
            )
            output = root / "assets/runtime"
            receipt = root / "config/receipt.json"

            with self.assertRaisesRegex(
                SvgPipelineError,
                "blocking findings",
            ):
                _normalize(root, [source], output, receipt)

            self.assertFalse(output.exists())
            self.assertFalse(receipt.exists())

    def test_normalize_refuses_receipt_runtime_path_collision(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            source = self._svg(
                root,
                '<svg width="16" height="16" viewBox="0 0 16 16">'
                '<path fill="var(--fill-0, #ABCDEF)"/></svg>',
            )

            with self.assertRaisesRegex(
                SvgPipelineError,
                "receipt must not overwrite",
            ):
                _normalize(
                    root,
                    [source],
                    Path("assets/runtime"),
                    Path("assets/runtime/icon.svg"),
                )

            self.assertFalse((root / "assets/runtime").exists())

    def test_receipt_verification_detects_runtime_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            runtime = root / "assets/icon.svg"
            runtime.parent.mkdir(parents=True)
            runtime.write_text("<svg/>", encoding="utf-8")
            receipt = root / "receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "schema": SVG_RECEIPT_SCHEMA,
                        "assets": [
                            {
                                "name": "icon",
                                "source_export_sha256": "1" * 64,
                                "runtime_asset_path": "assets/icon.svg",
                                "runtime_asset_sha256": hashlib.sha256(
                                    runtime.read_bytes()
                                ).hexdigest(),
                                "normalizations": [
                                    "resolve-css-color-fallbacks:1"
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(load_receipt(root, receipt)[0]["name"], "icon")
            runtime.write_text("<svg><path/></svg>", encoding="utf-8")

            errors = verify_receipt(root, receipt)

        self.assertEqual(errors, ["hash:assets/icon.svg"])

    def test_receipt_rejects_runtime_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            receipt = root / "receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "schema": SVG_RECEIPT_SCHEMA,
                        "assets": [
                            {
                                "name": "icon",
                                "source_export_sha256": "1" * 64,
                                "runtime_asset_path": "../icon.svg",
                                "runtime_asset_sha256": "2" * 64,
                                "normalizations": [
                                    "resolve-css-color-fallbacks:1"
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                SvgPipelineError,
                "repository-relative",
            ):
                load_receipt(root, receipt)

    def test_receipt_rejects_unsupported_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            receipt = root / "receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "schema": SVG_RECEIPT_SCHEMA,
                        "assets": [
                            {
                                "name": "icon",
                                "source_export_sha256": "1" * 64,
                                "runtime_asset_path": "assets/icon.svg",
                                "runtime_asset_sha256": "2" * 64,
                                "normalizations": ["rewrite-geometry"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                SvgPipelineError,
                "supported rewrite",
            ):
                load_receipt(root, receipt)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression tests for the reusable Figma visual-fidelity instructions."""

from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
SKILL = SKILL_ROOT / "SKILL.md"
GUIDANCE = SKILL_ROOT / "references/audit_figma_fidelity.md"
ADAPTER = SKILL_ROOT / "references/figma_flutter_design_to_code.md"


class FigmaFidelityGuidanceTest(unittest.TestCase):
    """Protect the failure-family invariants from documentation drift."""

    @staticmethod
    def _normalized(path: Path) -> str:
        return " ".join(path.read_text(encoding="utf-8").split())

    def test_skill_routes_visual_approval_to_fidelity_guidance(self) -> None:
        source = self._normalized(SKILL)

        self.assertIn(
            "placement-box versus visual-glyph dimensions",
            source,
        )
        self.assertIn(
            "a structural audit pass is not visual approval",
            source,
        )
        self.assertIn("SVG scan and safe normalization pipeline", source)
        self.assertIn("never auto-repairs geometry", source)
        self.assertIn("figma_flutter_design_to_code.md", source)
        self.assertIn("evidence collection", source)

    def test_guidance_separates_icon_slot_from_leaf_glyph(self) -> None:
        source = self._normalized(GUIDANCE)

        self.assertIn("outer placement or hit-area box", source)
        self.assertIn("inner visual glyph", source)
        self.assertIn("do not stretch the leaf SVG to fill", source)
        self.assertIn("Never normalize unrelated glyphs", source)

    def test_guidance_requires_runtime_typography_and_visual_evidence(self) -> None:
        source = self._normalized(GUIDANCE)

        self.assertIn("font family", source)
        self.assertIn("system-font fallback is a known visual deviation", source)
        self.assertIn("Capture the implemented screen", source)
        self.assertIn(
            "Widget-existence, route, asset-hash, and container-size",
            source,
        )
        self.assertIn(
            "passing structural audit as proof",
            source,
        )

    def test_guidance_requires_traceable_non_geometric_svg_pipeline(self) -> None:
        source = self._normalized(GUIDANCE)

        self.assertIn("figma_svg_pipeline.py", source)
        self.assertIn("never rewrites paths", source)
        self.assertIn("Never use the same path", source)
        self.assertIn("source_export_sha256", source)
        self.assertIn("runtime_asset_sha256", source)
        self.assertIn("present in an approved screen's asset lock", source)

    def test_flutter_adapter_constrains_generic_figma_guidance(self) -> None:
        source = self._normalized(ADAPTER)

        self.assertIn("without attempting to bypass", source)
        self.assertIn("context acquisition", source)
        self.assertIn("not as Flutter implementation rules", source)
        self.assertIn(
            "Do not apply a blanket “leaf image fills its fixed-size container”",
            source,
        )
        self.assertIn("outer slot or hit area", source)
        self.assertIn("inner glyph as separate nodes", source)
        self.assertIn("only when the inspected leaf bounds and slot bounds", source)
        self.assertIn("required runtime font is unavailable", source)
        self.assertIn("do not replace this visual gate", source)


if __name__ == "__main__":
    unittest.main()

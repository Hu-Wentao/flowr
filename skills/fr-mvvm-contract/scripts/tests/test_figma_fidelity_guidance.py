#!/usr/bin/env python3
"""Regression tests for the reusable Figma visual-fidelity instructions."""

from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
SKILL = SKILL_ROOT / "SKILL.md"
GUIDANCE = SKILL_ROOT / "references/audit_figma_fidelity.md"


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


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression tests for persistent navigation-shell data freshness rules."""

from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
SKILL = SKILL_ROOT / "SKILL.md"
GUIDANCE = SKILL_ROOT / "references/navigation-shells.md"
VALIDATION = SKILL_ROOT / "references/validate_navigation_shell.md"


class NavigationShellGuidanceTest(unittest.TestCase):
    """Protect query reactivation invariants from documentation drift."""

    @staticmethod
    def _normalized(path: Path) -> str:
        return " ".join(path.read_text(encoding="utf-8").split())

    def test_skill_requires_query_refresh_on_branch_reactivation(self) -> None:
        source = self._normalized(SKILL)

        self.assertIn("Retained branch state does not keep query data fresh", source)
        self.assertIn("inactive-to-active transition", source)
        self.assertIn("Do not duplicate the initial Startup Event", source)
        self.assertIn("latest-result-safe", source)

    def test_guidance_separates_initial_load_from_reactivation(self) -> None:
        source = self._normalized(GUIDANCE)

        self.assertIn("inactive-to-active transition", source)
        self.assertIn("Startup Event exactly once", source)
        self.assertIn("ordinary rebuild", source)
        self.assertIn("Do not recreate the branch Provider", source)
        self.assertIn("exactly one additional request", source)

    def test_validation_requires_api_call_count_coverage(self) -> None:
        source = self._normalized(VALIDATION)

        self.assertIn("without duplicating its initial load", source)
        self.assertIn("latest-result-safe", source)
        self.assertIn("API-call coverage", source)


if __name__ == "__main__":
    unittest.main()

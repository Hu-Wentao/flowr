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

    def test_guidance_assigns_guarded_root_action_to_shell_owner(self) -> None:
        source = self._normalized(GUIDANCE)

        self.assertIn("With no permission, validation, API", source)
        self.assertIn("Shell-owned component ViewModel", source)
        self.assertIn("passive bottom-navigation Widget", source)
        self.assertIn("target Page ViewModel", source)
        self.assertIn("ignore-while-active", source)

    def test_validation_separates_shell_and_component_validators(self) -> None:
        source = self._normalized(VALIDATION)

        self.assertIn("Keep validator responsibilities separate", source)
        self.assertIn("validate_navigation_shell.py", source)
        self.assertIn("owning component contract/final validator", source)
        self.assertIn("blocked and approved outcomes", source)
        self.assertIn("repeat taps while active", source)
        self.assertIn("root-fullscreen coverage", source)
        self.assertIn("re-entry after returning", source)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression tests for guarded-entry interaction guidance."""

from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
SKILL = SKILL_ROOT / "SKILL.md"
GUIDANCE = SKILL_ROOT / "references/frontend-interactions.md"


class FrontendInteractionGuidanceTest(unittest.TestCase):
    @staticmethod
    def _normalized(path: Path) -> str:
        return " ".join(path.read_text(encoding="utf-8").split())

    def test_skill_distinguishes_unconditional_and_guarded_navigation(self) -> None:
        source = self._normalized(SKILL)

        self.assertIn("unconditional known typed Page navigation", source)
        self.assertIn("Trigger -> Event -> ViewModel preflight", source)
        self.assertIn("observable approved/blocked outcome", source)
        self.assertIn("nullable semantic navigation signal", source)
        self.assertIn("never await a gate in a StatefulWidget", source)
        self.assertIn("Default to `ignore-while-active`", source)

    def test_guidance_forbids_widget_owned_async_gate_navigation(self) -> None:
        source = self._normalized(GUIDANCE)

        self.assertIn("StatefulWidget` callback that awaits a gate", source)
        self.assertIn("Inject the permission or policy gateway", source)
        self.assertIn("real admission result separate", source)
        self.assertIn("blocked decision and an exception", source)
        self.assertIn("Repeated taps while active do nothing", source)
        self.assertIn("Treat each declared phase as one atomic state transition", source)
        self.assertIn("real non-navigation approved outcome", source)
        self.assertIn("does not completely prove mutual exclusion", source)
        self.assertIn("blocked path returns without the approved signal", source)
        self.assertIn("exception path", source)
        self.assertIn("repeat tap while active", source)
        self.assertIn("FrListener<ProtectedEntryViewModel, ProtectedEntryModel>", source)

    def test_guidance_allows_explicit_api_less_local_interactions(self) -> None:
        source = self._normalized(GUIDANCE)

        self.assertIn("non-BFF local component may also declare structured", source)
        self.assertIn("omit `Interactions:` or retain `Interactions: none`", source)
        self.assertIn("Local Flows use only `Uses: local`", source)
        self.assertIn("do not require a BFF endpoint, BFF Service, SDK, or `bff.md`", source)
        self.assertIn("entryOutcome = ProtectedEntryOutcome.approved", source)
        self.assertIn("navigationSignal = ProtectedEntryNavigation.destination", source)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for shared UI capability discovery."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
DISCOVER = SCRIPTS / "discover_ui_reuse.py"
UV_RUN_SCRIPT = ("uv", "run", "--script")


class DiscoverUiReuseTest(unittest.TestCase):
    def run_discover(self, root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                *UV_RUN_SCRIPT,
                str(DISCOVER),
                "--project-root",
                str(root),
                "--capability",
                "locale selection",
                *extra,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_discovers_component_and_widget_public_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = root / "lib/components/app_locale"
            component.mkdir(parents=True)
            (component / "app_locale.dart").write_text(
                "part 'app_locale.c.dart';\npart 'app_locale.v.dart';\n",
                encoding="utf-8",
            )
            (component / "app_locale.c.dart").write_text(
                "part of 'app_locale.dart';\n\n"
                "/// Capabilities:\n"
                "/// - Application locale selection and persistence.\n"
                "/// Public Views:\n"
                "/// - [AppLocaleOnboardingView] — header selector.\n"
                "class AppLocaleOnboardingView {}\n",
                encoding="utf-8",
            )
            widgets = root / "lib/widgets"
            widgets.mkdir(parents=True)
            (widgets / "locale_display.dart").write_text(
                "/// Capabilities:\n"
                "/// - Locale selection presentation.\n"
                "/// Public Widgets:\n"
                "/// - [LocaleLabel] — locale label.\n"
                "class LocaleLabel {}\n",
                encoding="utf-8",
            )

            result = self.run_discover(root)

        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["components"][0]["module"], "app_locale")
        self.assertEqual(
            data["components"][0]["publicViews"], ["AppLocaleOnboardingView"]
        )
        self.assertEqual(data["widgets"][0]["publicWidgets"], ["LocaleLabel"])

    def test_strict_rejects_missing_public_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = root / "lib/components/app_locale"
            component.mkdir(parents=True)
            (component / "app_locale.dart").write_text(
                "part 'app_locale.c.dart';\n", encoding="utf-8"
            )
            (component / "app_locale.c.dart").write_text(
                "part of 'app_locale.dart';\n\n"
                "/// Capabilities:\n"
                "/// - Locale selection.\n"
                "/// Public Views:\n"
                "/// - [MissingLocaleView] — unavailable.\n",
                encoding="utf-8",
            )

            result = self.run_discover(root, "--strict")

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("MissingLocaleView", result.stdout)


if __name__ == "__main__":
    unittest.main()

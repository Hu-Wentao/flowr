#!/usr/bin/env python3
"""Tests for the safe shared Widget extraction workflow."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "extract_shared_ui.py"
UV_RUN_SCRIPT = ("uv", "run", "--script")


class ExtractSharedUiTest(unittest.TestCase):
    def run_tool(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [*UV_RUN_SCRIPT, str(SCRIPT), "--project-root", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def make_project(self, root: Path, source: str) -> None:
        (root / "lib/app/login").mkdir(parents=True)
        (root / "pubspec.yaml").write_text("name: sample_app\n", encoding="utf-8")
        (root / "lib/app/login/login.v.dart").write_text(source, encoding="utf-8")

    def test_dry_run_classifies_presentation_widget_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = "import 'package:flutter/widgets.dart';\n\nclass LanguageToggle extends StatelessWidget { const LanguageToggle({super.key}); }\n"
            self.make_project(root, source)
            result = self.run_tool(root, "--source", "lib/app/login/login.v.dart", "--symbol", "LanguageToggle", "--name", "language_toggle", "--capability", "语言切换")
            data = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(data["classification"], "widget")
            self.assertFalse((root / "lib/widgets/language_toggle.dart").exists())

    def test_apply_moves_widget_and_imports_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = "import 'package:flutter/widgets.dart';\n\nclass LanguageToggle extends StatelessWidget { const LanguageToggle({super.key}); }\nclass LoginBody { LanguageToggle build() => const LanguageToggle(); }\n"
            self.make_project(root, source)
            result = self.run_tool(root, "--source", "lib/app/login/login.v.dart", "--symbol", "LanguageToggle", "--name", "language_toggle", "--capability", "语言切换", "--apply")
            self.assertEqual(result.returncode, 0, result.stderr)
            target = (root / "lib/widgets/language_toggle.dart").read_text(encoding="utf-8")
            remaining = (root / "lib/app/login/login.v.dart").read_text(encoding="utf-8")
            self.assertIn("Public Widgets:", target)
            self.assertIn("class LanguageToggle", target)
            self.assertNotIn("class LanguageToggle", remaining)
            self.assertIn("package:sample_app/widgets/language_toggle.dart", remaining)

    def test_blocks_component_owned_widget(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_project(root, "class LanguageToggle { void change() => vm.add(event); }\n")
            result = self.run_tool(root, "--source", "lib/app/login/login.v.dart", "--symbol", "LanguageToggle", "--name", "language_toggle", "--capability", "语言切换", "--apply")
            self.assertEqual(result.returncode, 2)
            self.assertIn("gen_component", result.stderr)
            self.assertFalse((root / "lib/widgets/language_toggle.dart").exists())

    def test_apply_validates_consumers_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = "class LanguageToggle {}\n"
            self.make_project(root, source)
            result = self.run_tool(root, "--source", "lib/app/login/login.v.dart", "--consumer", "lib/app/missing.dart", "--symbol", "LanguageToggle", "--name", "language_toggle", "--capability", "语言切换", "--apply")
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root / "lib/widgets/language_toggle.dart").exists())
            self.assertEqual((root / "lib/app/login/login.v.dart").read_text(encoding="utf-8"), source)


if __name__ == "__main__":
    unittest.main()

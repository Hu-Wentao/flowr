#!/usr/bin/env python3
"""Tests for the unified FlowR route resolver."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[4]
RESOLVER = REPO_ROOT / ".agents/skills/flowr-usage/scripts/resolve.py"
UV_RUN_SCRIPT = ("uv", "run", "--script")


def run_resolver(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the resolver against a target package root."""

    return subprocess.run(
        [*UV_RUN_SCRIPT, str(RESOLVER), *args, "--cwd", str(root)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def write_package(root: Path, pubspec: str) -> None:
    """Create the minimum generic skill files needed by an isolated package."""

    (root / ".git").mkdir()
    references = root / ".agents/skills/flowr-usage/references"
    references.mkdir(parents=True)
    (references / "core.md").write_text("# Core only\n", encoding="utf-8")
    (references / "flutter.md").write_text("# Flutter only\n", encoding="utf-8")
    (root / "pubspec.yaml").write_text(pubspec, encoding="utf-8")


class ResolveTest(unittest.TestCase):
    """Package detection and profile loading behavior."""

    def test_project_flutter_route_loads_configured_profile(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flowr_flutter_") as raw_root:
            root = Path(raw_root)
            write_package(
                root,
                """name: flutter_package
environment:
  sdk: ^3.0.0
dependencies:
  flutter:
    sdk: flutter
  flowr: ^6.0.0
""",
            )
            config_root = root / ".agents/skills-config/flowr-usage"
            config_root.mkdir(parents=True)
            (config_root / "config.yaml").write_text(
                """schema: flowr-usage.config.v1
profile: example
tasks:
  flutter:
    profile: example/flutter.md
""",
                encoding="utf-8",
            )
            profile_path = config_root / "example/flutter.md"
            profile_path.parent.mkdir()
            profile_path.write_text("# Example Flutter profile\n", encoding="utf-8")

            result = run_resolver(root, "--task", "auto")

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("task: flutter", result.stdout)
            self.assertIn("profile: example", result.stdout)
            self.assertIn(
                ".agents/skills-config/flowr-usage/example/flutter.md", result.stdout
            )

    def test_flowr_dart_only_auto_loads_core_without_flutter(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flowr_core_") as raw_root:
            root = Path(raw_root)
            write_package(
                root,
                """name: core_package
environment:
  sdk: ^3.0.0
dependencies:
  flowr_dart: ^6.0.0
""",
            )

            result = run_resolver(root, "--task", "auto", "--emit", "instructions")

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("- Task: `core`", result.stdout)
            self.assertIn("# Core only", result.stdout)
            self.assertNotIn("Flutter only", result.stdout)
            self.assertNotIn("Project Profile Instructions", result.stdout)

    def test_flowr_dart_only_rejects_flutter_route(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flowr_core_") as raw_root:
            root = Path(raw_root)
            write_package(
                root,
                """name: core_package
environment:
  sdk: ^3.0.0
dependencies:
  flowr_dart: ^6.0.0
""",
            )

            result = run_resolver(root, "--task", "flutter")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("flowr_dart-only", result.stdout)

    def test_flowr_without_flutter_sdk_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="flowr_invalid_") as raw_root:
            root = Path(raw_root)
            write_package(
                root,
                """name: invalid_package
environment:
  sdk: ^3.0.0
dependencies:
  flowr: ^6.0.0
""",
            )

            result = run_resolver(root, "--task", "auto")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("without a Flutter SDK dependency", result.stdout)


if __name__ == "__main__":
    unittest.main()

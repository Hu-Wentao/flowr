#!/usr/bin/env python3
"""Tests for fr-mvvm-contract project profile resolver."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[3]
RESOLVE_SCRIPT = REPO_ROOT / "skills/fr-mvvm-contract/scripts/resolve.py"


def run_resolver(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the resolver from the repository root."""

    return subprocess.run(
        [sys.executable, str(RESOLVE_SCRIPT), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def manifest_value(manifest: str, key: str) -> str:
    """Read a top-level scalar from the simple manifest."""

    prefix = f"{key}: "
    for line in manifest.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix)
    raise AssertionError(f"missing manifest key: {key}\n{manifest}")


class ResolveTest(unittest.TestCase):
    """Resolver behavior tests."""

    def test_adapt_project_uses_bundled_scaffold_baseline(self) -> None:
        result = run_resolver("--task", "adapt_project")

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("task: adapt_project", result.stdout)
        self.assertIn(
            "skills/fr-mvvm-contract/references/adapt_project.md",
            result.stdout,
        )
        self.assertIn("bundled ACDD scaffold", result.stdout)
        self.assertIn("Preserve existing behavior", result.stdout)

    def test_adapt_project_falls_back_when_existing_profile_omits_task(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_adapt_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "config.yaml").write_text(
                "\n".join(
                    [
                        "schema: fr-mvvm-contract.config.v1",
                        "profile: existing",
                        "tasks:",
                        "  gen_page:",
                        "    base: references/gen_page.md",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_resolver("--task", "adapt_project", "--cwd", str(root))

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("task: adapt_project", result.stdout)
        self.assertIn("profile: existing", result.stdout)
        self.assertIn("references/adapt_project.md", result.stdout)

    def test_gen_page_manifest_writes_cache(self) -> None:
        result = run_resolver("--task", "gen_page")

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("status: ready", result.stdout)
        self.assertIn("profile: generic", result.stdout)
        self.assertIn("instructions_id: fr-mvvm-contract/gen_page@", result.stdout)
        self.assertIn(
            "skills/fr-mvvm-contract/references/gen_page.md",
            result.stdout,
        )
        path = None
        for line in result.stdout.splitlines():
            if line.startswith("  path: "):
                path = line.removeprefix("  path: ")
                break
        self.assertIsNotNone(path, msg=result.stdout)
        cache_path = REPO_ROOT / str(path)
        self.assertTrue(cache_path.exists(), msg=str(cache_path))
        cache_text = cache_path.read_text(encoding="utf-8")
        self.assertIn("# Resolved fr-mvvm-contract Instructions", cache_text)
        self.assertNotIn("## Project Profile Instructions", cache_text)

    def test_gen_page_instructions_id_is_stable(self) -> None:
        first = run_resolver("--task", "gen_page")
        second = run_resolver("--task", "gen_page")

        self.assertEqual(first.returncode, 0, msg=first.stdout + first.stderr)
        self.assertEqual(second.returncode, 0, msg=second.stdout + second.stderr)
        self.assertEqual(
            manifest_value(first.stdout, "instructions_id"),
            manifest_value(second.stdout, "instructions_id"),
        )

    def test_emit_instructions_prints_only_instructions(self) -> None:
        result = run_resolver("--task", "gen_component", "--emit", "instructions")

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertTrue(
            result.stdout.startswith("# Resolved fr-mvvm-contract Instructions"),
            msg=result.stdout,
        )
        self.assertNotIn("## Project Profile Instructions", result.stdout)
        self.assertNotIn("status: ready", result.stdout)

    def test_generic_fallback_works_without_project_config(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_generic_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            references = root / ".agents/skills/fr-mvvm-contract/references"
            references.mkdir(parents=True)
            (references / "gen_component.md").write_text(
                "# Generic component fallback\n", encoding="utf-8"
            )

            result = run_resolver(
                "--task",
                "gen_component",
                "--cwd",
                str(root),
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("profile: generic", result.stdout)
            self.assertIn("status: ready", result.stdout)
            self.assertIn("Using generic fr-mvvm-contract fallback", result.stdout)

    def test_bundled_skill_fallback_works_in_new_repository(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_bundled_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()

            result = run_resolver("--task", "gen_page", "--cwd", str(root))

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("profile: generic", result.stdout)
            self.assertIn("status: ready", result.stdout)
            self.assertIn(
                str(REPO_ROOT / "skills/fr-mvvm-contract/references/gen_page.md"),
                result.stdout,
            )


if __name__ == "__main__":
    unittest.main()

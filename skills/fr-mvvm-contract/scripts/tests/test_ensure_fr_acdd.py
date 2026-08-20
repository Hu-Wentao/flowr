#!/usr/bin/env python3
"""Tests for compatible fr_acdd dependency checking and upgrades."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
SCRIPT = SCRIPTS / "ensure_fr_acdd.py"


class EnsureFrAcddTest(unittest.TestCase):
    def fixture(
        self,
        root: Path,
        *,
        version: str,
        source: str = "hosted",
        resolved_source: str | None = None,
        direct: bool = True,
        flutter: bool = False,
    ) -> dict[str, str]:
        dependency = ""
        if direct:
            dependency = (
                f"  fr_acdd: ^{version}\n"
                if source == "hosted"
                else "  fr_acdd:\n    path: ../fr_acdd\n"
            )
        flutter_dependency = "  flutter:\n    sdk: flutter\n" if flutter else ""
        (root / "pubspec.yaml").write_text(
            "name: fixture\nenvironment:\n  sdk: ^3.7.0\ndependencies:\n"
            + flutter_dependency
            + dependency,
            encoding="utf-8",
        )
        (root / ".version").write_text(version, encoding="utf-8")
        (root / ".source").write_text(
            resolved_source or source, encoding="utf-8"
        )
        executable = root / "fvm"
        executable.write_text(
            "#!/usr/bin/env python3\n"
            "import json, pathlib, sys\n"
            "root = pathlib.Path.cwd()\n"
            "args = sys.argv[1:]\n"
            "if args == ['dart', 'pub', 'deps', '--json']:\n"
            "    print(json.dumps({'packages': [{'name': 'fr_acdd', "
            "'version': (root / '.version').read_text(), "
            "'source': (root / '.source').read_text()}]}))\n"
            "    raise SystemExit(0)\n"
            "if 'pub' in args and ('add' in args or 'upgrade' in args):\n"
            "    with (root / '.commands').open('a') as log:\n"
            "        log.write(' '.join(args) + '\\n')\n"
            "    if 'add' in args:\n"
            "        pubspec = root / 'pubspec.yaml'\n"
            "        text = pubspec.read_text()\n"
            "        if '  fr_acdd:' not in text:\n"
            "            pubspec.write_text(text.replace('dependencies:\\n', "
            "'dependencies:\\n  fr_acdd: ^0.7.0\\n'))\n"
            "    if 'add' in args or (root / '.upgrade-succeeds').exists():\n"
            "        (root / '.version').write_text('0.7.0')\n"
            "    raise SystemExit(0)\n"
            "if 'pub' in args and 'get' in args:\n"
            "    raise SystemExit(0)\n"
            "raise SystemExit(2)\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
        env = os.environ.copy()
        env["FR_MVVM_FVM"] = str(executable)
        return env

    def run_script(
        self, root: Path, env: dict[str, str], *extra: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "uv",
                "run",
                "--script",
                str(SCRIPT),
                "--project-root",
                str(root),
                *extra,
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_current_compatible_version_does_not_run_pub_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = self.run_script(root, self.fixture(root, version="0.7.0"))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("ready: 0.7.0", result.stdout)
            self.assertFalse((root / ".commands").exists())

    def test_old_hosted_version_is_automatically_upgraded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = self.run_script(root, self.fixture(root, version="0.6.0"))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("ready: 0.7.0", result.stdout)
            self.assertIn(
                "dart pub add fr_acdd:^0.7.0",
                (root / ".commands").read_text(encoding="utf-8"),
            )

    def test_flutter_package_uses_flutter_pub_for_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = self.run_script(
                root, self.fixture(root, version="0.6.0", flutter=True)
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(
                "flutter pub add fr_acdd:^0.7.0",
                (root / ".commands").read_text(encoding="utf-8"),
            )

    def test_inline_flutter_sdk_dependency_uses_flutter_pub(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            env = self.fixture(root, version="0.6.0", flutter=True)
            pubspec = root / "pubspec.yaml"
            pubspec.write_text(
                pubspec.read_text().replace(
                    "  flutter:\n    sdk: flutter\n",
                    "    flutter: {sdk: flutter} # SDK dependency\n",
                )
            )

            result = self.run_script(root, env)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(
                "flutter pub add fr_acdd:^0.7.0",
                (root / ".commands").read_text(encoding="utf-8"),
            )

    def test_check_mode_reports_old_version_without_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = self.run_script(
                root, self.fixture(root, version="0.6.0"), "--check"
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("version >= 0.7.0 is required", result.stdout)
            self.assertFalse((root / ".commands").exists())

    def test_path_dependency_attempts_upgrade_then_requires_source_update(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = self.run_script(
                root, self.fixture(root, version="0.6.0", source="path")
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("workspace/path/git source", result.stdout)
            self.assertIn(
                "dart pub upgrade fr_acdd",
                (root / ".commands").read_text(encoding="utf-8"),
            )

    def test_declared_path_source_wins_over_hosted_override_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = self.run_script(
                root,
                self.fixture(
                    root,
                    version="0.6.0",
                    source="path",
                    resolved_source="hosted",
                ),
            )

            self.assertEqual(result.returncode, 1)
            commands = (root / ".commands").read_text(encoding="utf-8")
            self.assertIn("dart pub upgrade fr_acdd", commands)
            self.assertNotIn("pub add", commands)
            self.assertIn("path: ../fr_acdd", (root / "pubspec.yaml").read_text())

    def test_four_space_path_declaration_is_not_rewritten_as_hosted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            env = self.fixture(
                root,
                version="0.6.0",
                source="path",
                resolved_source="hosted",
            )
            pubspec = root / "pubspec.yaml"
            pubspec.write_text(
                pubspec.read_text(encoding="utf-8").replace(
                    "  fr_acdd:\n    path:",
                    "    fr_acdd:\n      path:",
                ),
                encoding="utf-8",
            )
            result = self.run_script(root, env)

            self.assertEqual(result.returncode, 1)
            commands = (root / ".commands").read_text(encoding="utf-8")
            self.assertIn("dart pub upgrade fr_acdd", commands)
            self.assertNotIn("pub add", commands)

    def test_missing_direct_dependency_is_added_despite_workspace_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = self.run_script(
                root,
                self.fixture(
                    root,
                    version="0.7.0",
                    resolved_source="root",
                    direct=False,
                ),
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(
                "dart pub add fr_acdd:^0.7.0",
                (root / ".commands").read_text(encoding="utf-8"),
            )
            self.assertIn("fr_acdd: ^0.7.0", (root / "pubspec.yaml").read_text())


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""End-to-end regression for the Freezed/json_serializable generator chain."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which("fvm"), "fvm is required for Dart codegen")
class JsonCodegenIntegrationTest(unittest.TestCase):
    def run_command(
        self, root: Path, *command: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )

    def test_fr_state_generates_g_part_and_analyzes_without_handwritten_helpers(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_state_codegen_") as temporary:
            root = Path(temporary)
            (root / "lib").mkdir()
            (root / "pubspec.yaml").write_text(
                "name: fr_state_codegen_fixture\n"
                "environment:\n"
                "  sdk: ^3.7.0\n"
                "dependencies:\n"
                "  freezed_annotation: ^3.1.0\n"
                "  json_annotation: ^4.9.0\n"
                "dev_dependencies:\n"
                "  build_runner: ^2.10.0\n"
                "  freezed: ^3.2.0\n"
                "  json_serializable: ^6.11.0\n",
                encoding="utf-8",
            )
            model = root / "lib/confirm_password.dart"
            model.write_text(
                "import 'package:freezed_annotation/freezed_annotation.dart';\n\n"
                "part 'confirm_password.freezed.dart';\n"
                "part 'confirm_password.g.dart';\n\n"
                "const FrState = Freezed(\n"
                "  copyWith: true,\n"
                "  equal: true,\n"
                "  toStringOverride: true,\n"
                "  fromJson: false,\n"
                "  toJson: true,\n"
                ");\n\n"
                "@FrState\n"
                "abstract class ConfirmPasswordModel "
                "with _$ConfirmPasswordModel {\n"
                "  const factory ConfirmPasswordModel({\n"
                "    @Default(false) bool obscured,\n"
                "  }) = _ConfirmPasswordModel;\n"
                "}\n",
                encoding="utf-8",
            )

            get_result = self.run_command(root, "fvm", "dart", "pub", "get")
            self.assertEqual(get_result.returncode, 0, get_result.stderr)
            build_result = self.run_command(
                root,
                "fvm",
                "dart",
                "run",
                "build_runner",
                "build",
                "--delete-conflicting-outputs",
            )
            self.assertEqual(build_result.returncode, 0, build_result.stderr)

            generated_json = root / "lib/confirm_password.g.dart"
            self.assertTrue(generated_json.is_file(), build_result.stdout)
            self.assertIn(
                "_$ConfirmPasswordModelToJson",
                generated_json.read_text(encoding="utf-8"),
            )
            self.assertNotIn(
                "_$ConfirmPasswordModelToJson(", model.read_text(encoding="utf-8")
            )

            analyze_result = self.run_command(root, "fvm", "dart", "analyze")
            self.assertEqual(analyze_result.returncode, 0, analyze_result.stdout)


if __name__ == "__main__":
    unittest.main()

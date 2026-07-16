#!/usr/bin/env python3
"""Tests for the deterministic ACDD project scaffold."""

from __future__ import annotations

import argparse
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TEST_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import acdd_scaffold as scaffold  # noqa: E402


def args_for(**overrides: object) -> argparse.Namespace:
    """Return a complete argparse namespace for config tests."""

    values: dict[str, object] = {
        "name": "example_app",
        "output": "example_app",
        "org": "com.example",
        "platforms": None,
        "description": None,
        "dry_run": False,
        "apply": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class AcddScaffoldTest(unittest.TestCase):
    """Scaffold validation, planning, rendering, and execution tests."""

    def test_non_interactive_platforms_default_to_android_and_ios(self) -> None:
        with tempfile.TemporaryDirectory(prefix="acdd_config_") as raw_root:
            config = scaffold.build_config(
                args_for(output=str(Path(raw_root) / "app")),
                interactive=False,
            )

        self.assertEqual(config.platforms, ("android", "ios"))

    def test_interactive_prompts_apply_defaults(self) -> None:
        with tempfile.TemporaryDirectory(prefix="acdd_prompt_") as raw_root:
            answers = iter(
                [
                    "prompted_app",
                    str(Path(raw_root) / "prompted_app"),
                    "com.acme",
                    "",
                ]
            )
            config = scaffold.build_config(
                args_for(name=None, output=None, org=None),
                input_reader=lambda prompt: next(answers),
                interactive=True,
            )

        self.assertEqual(config.name, "prompted_app")
        self.assertEqual(config.org, "com.acme")
        self.assertEqual(config.platforms, ("android", "ios"))

    def test_missing_required_value_is_blocked_non_interactively(self) -> None:
        with self.assertRaisesRegex(scaffold.ScaffoldError, "missing --name"):
            scaffold.build_config(
                args_for(name=None),
                interactive=False,
            )

    def test_invalid_project_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(scaffold.ScaffoldError, "lower_snake_case"):
            scaffold.build_config(
                args_for(name="Invalid-Name"),
                interactive=False,
            )

    def test_all_flutter_platforms_are_supported(self) -> None:
        self.assertEqual(
            scaffold.parse_platforms("android,ios,macos,web,windows,linux"),
            ("android", "ios", "macos", "web", "windows", "linux"),
        )

    def test_unknown_platform_is_rejected(self) -> None:
        with self.assertRaisesRegex(scaffold.ScaffoldError, "unknown"):
            scaffold.parse_platforms("android,unknown")

    def test_non_empty_output_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="acdd_nonempty_") as raw_root:
            root = Path(raw_root)
            (root / "keep.txt").write_text("occupied", encoding="utf-8")
            with self.assertRaisesRegex(scaffold.ScaffoldError, "not empty"):
                scaffold.build_config(
                    args_for(output=str(root)),
                    interactive=False,
                )

    def test_dry_run_writes_nothing_and_lists_all_stages(self) -> None:
        with tempfile.TemporaryDirectory(prefix="acdd_dry_run_") as raw_root:
            output = Path(raw_root) / "new_app"
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                result = scaffold.main(
                    [
                        "--name",
                        "new_app",
                        "--output",
                        str(output),
                        "--org",
                        "com.example",
                    ]
                )

            self.assertEqual(result, 0)
            self.assertFalse(output.exists())
            plan = stream.getvalue()
            self.assertIn("platforms: android,ios", plan)
            self.assertIn("[create]", plan)
            self.assertIn("[dependencies]", plan)
            self.assertIn("[format]", plan)
            self.assertIn("lib/app_router.dart", plan)
            self.assertIn("lib/app/.gitkeep", plan)
            self.assertIn("lib/widgets/.gitkeep", plan)
            self.assertIn("Re-run with --apply", plan)

    def test_apply_uses_commands_and_renders_complete_project(self) -> None:
        with tempfile.TemporaryDirectory(prefix="acdd_apply_") as raw_root:
            output = Path(raw_root) / "generated_app"
            config = scaffold.build_config(
                args_for(
                    name="generated_app",
                    output=str(output),
                    apply=True,
                ),
                interactive=False,
            )
            stages: list[str] = []

            def fake_runner(step: scaffold.CommandStep) -> None:
                stages.append(step.stage)
                if step.stage == "create":
                    (output / "lib").mkdir(parents=True)
                    (output / "test").mkdir()
                    (output / "test/widget_test.dart").write_text(
                        "default test", encoding="utf-8"
                    )

            with contextlib.redirect_stdout(io.StringIO()):
                scaffold.apply_scaffold(config, command_runner=fake_runner)

            self.assertEqual(
                stages,
                [
                    "create",
                    "dependencies",
                    "dev_dependencies",
                    "format",
                    "analyze",
                    "test",
                ],
            )
            self.assertTrue((output / "lib/app/.gitkeep").is_file())
            self.assertTrue((output / "lib/components/.gitkeep").is_file())
            self.assertTrue((output / "lib/widgets/.gitkeep").is_file())
            self.assertTrue((output / "lib/app_router.dart").is_file())
            self.assertTrue((output / "lib/core/app_env.dart").is_file())
            self.assertTrue((output / "lib/core/app_locale.dart").is_file())
            self.assertTrue((output / "lib/core/app_theme.dart").is_file())
            self.assertTrue((output / "lib/core/providers.dart").is_file())
            self.assertFalse((output / "lib/core/app_providers.dart").exists())
            self.assertFalse((output / "lib/core/config").exists())
            self.assertFalse((output / "test/widget_test.dart").exists())
            self.assertIn(
                "package:generated_app/application.dart",
                (output / "test/application_test.dart").read_text(encoding="utf-8"),
            )
            main_text = (output / "lib/main.dart").read_text(encoding="utf-8")
            self.assertIn("await FrStorage.init();", main_text)
            self.assertNotIn("bootstrap", main_text.lower())
            application_text = (output / "lib/application.dart").read_text(
                encoding="utf-8"
            )
            self.assertIn("MaterialApp.router", application_text)
            self.assertIn("routerConfig: appRouter", application_text)
            theme_text = (output / "lib/core/app_theme.dart").read_text(
                encoding="utf-8"
            )
            self.assertIn("'seedColor': seedColor", theme_text)
            self.assertNotIn("toJson() => const {}", theme_text)
            self.assertNotIn("home:", application_text)

    def test_apply_reports_contract_directory_boundaries(self) -> None:
        with tempfile.TemporaryDirectory(prefix="acdd_paths_") as raw_root:
            output = Path(raw_root) / "generated_app"
            config = scaffold.build_config(
                args_for(output=str(output), apply=True),
                interactive=False,
            )

            def fake_runner(step: scaffold.CommandStep) -> None:
                if step.stage == "create":
                    (output / "lib").mkdir(parents=True)
                    (output / "test").mkdir()

            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                scaffold.apply_scaffold(config, command_runner=fake_runner)

            result = stream.getvalue()
            self.assertIn("lib/app/<route-segment>/", result)
            self.assertIn("lib/components/<component-name>/", result)
            self.assertIn("lib/widgets/", result)

    def test_commands_include_default_dependencies_and_sdk_dependency(self) -> None:
        with tempfile.TemporaryDirectory(prefix="acdd_commands_") as raw_root:
            config = scaffold.build_config(
                args_for(output=str(Path(raw_root) / "app")),
                interactive=False,
            )
            steps = scaffold.build_command_steps(config)

        runtime = steps[1].command
        dev = steps[2].command
        self.assertIn("fr_acdd", runtime)
        self.assertIn("fr_mvvm_theme", runtime)
        self.assertIn("fr_mvvm_locale", runtime)
        self.assertIn("fr_mvvm_env", runtime)
        self.assertIn("fr_storage", runtime)
        self.assertIn("go_router", runtime)
        self.assertIn("json_annotation", runtime)
        self.assertIn("flutter_localizations:{sdk: flutter}", runtime)
        self.assertIn("dev:freezed", dev)
        self.assertIn("dev:build_runner", dev)
        self.assertIn("dev:json_serializable", dev)

    def test_macos_adds_path_provider_and_debug_build(self) -> None:
        with tempfile.TemporaryDirectory(prefix="acdd_macos_commands_") as raw_root:
            config = scaffold.build_config(
                args_for(
                    output=str(Path(raw_root) / "app"),
                    platforms="macos,web",
                ),
                interactive=False,
            )
            steps = scaffold.build_command_steps(config)

        self.assertIn("path_provider", steps[1].command)
        self.assertEqual(steps[-1].stage, "build_macos_debug")
        self.assertEqual(
            steps[-1].command,
            ("fvm", "flutter", "build", "macos", "--debug"),
        )

    def test_macos_templates_and_native_security_are_configured(self) -> None:
        with tempfile.TemporaryDirectory(prefix="acdd_macos_render_") as raw_root:
            output = Path(raw_root) / "generated_app"
            config = scaffold.build_config(
                args_for(
                    name="generated_app",
                    output=str(output),
                    platforms="macos",
                    apply=True,
                ),
                interactive=False,
            )
            runner = output / "macos" / "Runner"
            project = output / "macos" / "Runner.xcodeproj" / "project.pbxproj"
            podfile = output / "macos" / "Podfile"
            runner.mkdir(parents=True)
            project.parent.mkdir(parents=True)
            (output / "lib").mkdir()
            (output / "test").mkdir()
            plist = {"com.apple.security.app-sandbox": True}
            for name in ("DebugProfile.entitlements", "Release.entitlements"):
                with (runner / name).open("wb") as file:
                    scaffold.plistlib.dump(plist, file)
            project.write_text(
                """\
\t\tABC123 /* Debug */ = {
\t\t\tisa = XCBuildConfiguration;
\t\t\tbaseConfigurationReference = DEF456 /* AppInfo.xcconfig */;
\t\t\tbuildSettings = {
\t\t\t\tCODE_SIGN_ENTITLEMENTS = Runner/DebugProfile.entitlements;
\t\t\t\tCODE_SIGN_STYLE = Automatic;
\t\t\t\tMACOSX_DEPLOYMENT_TARGET = 10.15;
\t\t\t};
\t\t\tname = Debug;
\t\t};
""",
                encoding="utf-8",
            )
            podfile.write_text("platform :osx, '10.15'\n", encoding="utf-8")
            scaffold.render_templates(config)
            scaffold.configure_macos(config)

            main_text = (output / "lib/main.dart").read_text(encoding="utf-8")
            project_text = project.read_text(encoding="utf-8")
            self.assertIn("getApplicationSupportDirectory", main_text)
            self.assertIn("kDebugMode", main_text)
            self.assertIn("Uint8List.fromList", main_text)
            self.assertIn("Runner/Debug.entitlements", project_text)
            self.assertIn("MACOSX_DEPLOYMENT_TARGET = 11.0", project_text)
            self.assertIn('CODE_SIGN_IDENTITY = "-"', project_text)
            self.assertEqual(
                podfile.read_text(encoding="utf-8"),
                "platform :osx, '11.0'\n",
            )
            with (runner / "Debug.entitlements").open("rb") as file:
                debug_entitlements = scaffold.plistlib.load(file)
            self.assertNotIn(
                "com.apple.security.app-sandbox", debug_entitlements
            )
            for name in ("DebugProfile.entitlements", "Release.entitlements"):
                with (runner / name).open("rb") as file:
                    entitlements = scaffold.plistlib.load(file)
                self.assertEqual(entitlements["keychain-access-groups"], [])

    def test_command_failure_identifies_stage(self) -> None:
        step = scaffold.CommandStep(
            stage="analyze",
            command=(sys.executable, "-c", "raise SystemExit(7)"),
            cwd=Path.cwd(),
        )

        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(scaffold.ScaffoldError, "stage analyze failed"):
                scaffold.default_command_runner(step)


if __name__ == "__main__":
    unittest.main()

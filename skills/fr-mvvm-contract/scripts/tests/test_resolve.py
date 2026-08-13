#!/usr/bin/env python3
"""Tests for fr-mvvm-contract project profile resolver."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TEST_DIR.parents[1]
RESOLVE_SCRIPT = TEST_DIR.parent / "resolve.py"
UV_RUN_SCRIPT = ("uv", "run", "--script")


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise AssertionError(f"test skill is not inside a Git repository: {start}")


REPO_ROOT = find_repo_root(TEST_DIR)


def run_resolver(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the resolver from the repository root."""

    return subprocess.run(
        [*UV_RUN_SCRIPT, str(RESOLVE_SCRIPT), *args],
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

    def test_check_app_info_falls_back_when_profile_omits_task(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_app_info_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "config.yaml").write_text(
                "schema: fr-mvvm-contract.config.v1\nprofile: existing\n",
                encoding="utf-8",
            )
            result = run_resolver(
                "--task", "check_app_info", "--cwd", str(root)
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("task: check_app_info", result.stdout)
        self.assertIn(
            str(SKILL_ROOT / "references/check_app_info.md"), result.stdout
        )
        self.assertIn("profile: existing", result.stdout)

    def test_extract_shared_ui_resolves_project_workflow(self) -> None:
        result = run_resolver("--task", "extract_shared_ui", "--cwd", str(REPO_ROOT))

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("task: extract_shared_ui", result.stdout)
        self.assertIn("references/extract_shared_ui.md", result.stdout)

    def test_adapt_project_uses_bundled_scaffold_baseline(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_adapt_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            result = run_resolver("--task", "adapt_project", "--cwd", str(root))

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("task: adapt_project", result.stdout)
        self.assertIn(str(SKILL_ROOT / "references/adapt_project.md"), result.stdout)
        self.assertIn("bundled ACDD scaffold", result.stdout)
        self.assertIn("Preserve existing behavior", result.stdout)

    def test_generate_openapi_resolves_project_generic_wrappers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_openapi_codegen_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "config.yaml").write_text(
                "\n".join(
                    [
                        "schema: fr-mvvm-contract.config.v1",
                        "profile: wrappers",
                        "transport:",
                        "  backend_openapi:",
                        "    local_root: docs/openapi",
                        "    dart_codegen:",
                        "      interceptor_owned_headers:",
                        "        tenant: Tenant-ID",
                        "        access: Access-ID",
                        "      generic_wrappers:",
                        "        request:",
                        "          dart_name: ReqWrapper",
                        "          schema_glob: StandardRequest*",
                        "          type_parameter_field: data",
                        "        response:",
                        "          dart_name: RspWrapper",
                        "          schema_glob: Response*",
                        "          type_parameter_field: data",
                        "          missing_type_parameter_field: optional",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_resolver(
                "--task", "generate_openapi", "--cwd", str(root)
            )
            instruction_path = next(
                line.removeprefix("  path: ")
                for line in result.stdout.splitlines()
                if line.startswith("  path: ")
            )
            instructions = (root / instruction_path).read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("dart_generic_wrappers: ReqWrapper,RspWrapper", result.stdout)
        self.assertIn(
            "dart_interceptor_owned_headers: Tenant-ID,Access-ID", result.stdout
        )
        self.assertIn("task: generate_openapi", result.stdout)
        self.assertIn("generate_openapi: uv run --script ", result.stdout)
        self.assertIn("missing: `optional`", instructions)
        self.assertIn("`Tenant-ID`, `Access-ID`", instructions)

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

    def test_figma_fidelity_resolves_project_discovery_command(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_figma_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "config.yaml").write_text(
                "\n".join(
                    [
                        "schema: fr-mvvm-contract.config.v1",
                        "profile: fixture",
                        "tasks:",
                        "  audit_figma_fidelity:",
                        "    base: references/audit_figma_fidelity.md",
                        "    commands:",
                        "      audit: uv run --script "
                        ".agents/skills/fr-mvvm-contract/scripts/"
                        "audit_figma_fidelity.py --project-root . --discover",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_resolver(
                "--task", "audit_figma_fidelity", "--cwd", str(root)
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("task: audit_figma_fidelity", result.stdout)
        self.assertIn("profile: fixture", result.stdout)
        self.assertIn("references/audit_figma_fidelity.md", result.stdout)
        self.assertIn(
            "audit: uv run --script "
            ".agents/skills/fr-mvvm-contract/scripts/"
            "audit_figma_fidelity.py --project-root . --discover",
            result.stdout,
        )

    def test_figma_fidelity_falls_back_when_profile_omits_task(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_figma_") as raw_root:
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

            result = run_resolver(
                "--task", "audit_figma_fidelity", "--cwd", str(root)
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("task: audit_figma_fidelity", result.stdout)
        self.assertIn("profile: existing", result.stdout)
        self.assertIn("references/audit_figma_fidelity.md", result.stdout)

    def test_figma_data_falls_back_when_profile_omits_task(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_figma_data_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "config.yaml").write_text(
                "schema: fr-mvvm-contract.config.v1\nprofile: existing\n",
                encoding="utf-8",
            )

            result = run_resolver(
                "--task", "audit_figma_data", "--cwd", str(root)
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("task: audit_figma_data", result.stdout)
        self.assertIn("profile: existing", result.stdout)
        self.assertIn("references/figma_fill_data.md", result.stdout)

    def test_navigation_shell_resolves_project_profile_and_command(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_navigation_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "navigation.md").write_text(
                "# Navigation fixture\n", encoding="utf-8"
            )
            (config_root / "config.yaml").write_text(
                "\n".join(
                    [
                        "schema: fr-mvvm-contract.config.v1",
                        "profile: navigation-fixture",
                        "tasks:",
                        "  validate_navigation_shell:",
                        "    base: references/validate_navigation_shell.md",
                        "    profile: navigation.md",
                        "    commands:",
                        "      validate_navigation_shell: uv run --script .agents/skills/fr-mvvm-contract/scripts/validate_navigation_shell.py --project-root . --profile .agents/skills-config/fr-mvvm-contract/navigation-shell.json",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_resolver(
                "--task", "validate_navigation_shell", "--cwd", str(root)
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("task: validate_navigation_shell", result.stdout)
        self.assertIn("profile: navigation-fixture", result.stdout)
        self.assertIn("references/validate_navigation_shell.md", result.stdout)
        self.assertIn("navigation.md", result.stdout)
        self.assertIn(
            "validate_navigation_shell: uv run --script "
            ".agents/skills/fr-mvvm-contract/scripts/"
            "validate_navigation_shell.py",
            result.stdout,
        )

    def test_gen_page_manifest_writes_cache(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_page_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            result = run_resolver("--task", "gen_page", "--cwd", str(root))

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("status: ready", result.stdout)
            self.assertIn("profile: generic", result.stdout)
            self.assertIn("description_language: English", result.stdout)
            self.assertNotIn("service_base_url", result.stdout)
            self.assertIn("instructions_id: fr-mvvm-contract/gen_page@", result.stdout)
            self.assertIn(str(SKILL_ROOT / "references/gen_page.md"), result.stdout)
            path = None
            for line in result.stdout.splitlines():
                if line.startswith("  path: "):
                    path = line.removeprefix("  path: ")
                    break
            self.assertIsNotNone(path, msg=result.stdout)
            cache_path = root / str(path)
            self.assertTrue(cache_path.exists(), msg=str(cache_path))
            cache_text = cache_path.read_text(encoding="utf-8")
            self.assertIn("# Resolved fr-mvvm-contract Instructions", cache_text)
            self.assertNotIn("## Project Profile Instructions", cache_text)

    def test_gen_page_instructions_id_is_stable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_stable_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            first = run_resolver("--task", "gen_page", "--cwd", str(root))
            second = run_resolver("--task", "gen_page", "--cwd", str(root))

        self.assertEqual(first.returncode, 0, msg=first.stdout + first.stderr)
        self.assertEqual(second.returncode, 0, msg=second.stdout + second.stderr)
        self.assertEqual(
            manifest_value(first.stdout, "instructions_id"),
            manifest_value(second.stdout, "instructions_id"),
        )

    def test_emit_instructions_prints_only_instructions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_emit_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            result = run_resolver(
                "--task",
                "gen_component",
                "--emit",
                "instructions",
                "--cwd",
                str(root),
            )

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
            self.assertIn("description_language: English", result.stdout)
            self.assertNotIn("service_base_url", result.stdout)
            self.assertIn("status: ready", result.stdout)
            self.assertIn("Using generic fr-mvvm-contract fallback", result.stdout)

    def test_contract_description_language_changes_resolved_instructions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_language_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            config_path = config_root / "config.yaml"

            def write_config(language: str) -> None:
                config_path.write_text(
                    "\n".join(
                        [
                            "schema: fr-mvvm-contract.config.v1",
                            "profile: language-test",
                            "contract:",
                            f"  description_language: {language}",
                            "tasks:",
                            "  gen_component:",
                            "    base: references/gen_component.md",
                        ]
                    ),
                    encoding="utf-8",
                )

            write_config("English")
            english = run_resolver(
                "--task", "gen_component", "--cwd", str(root)
            )
            write_config("zh-CN")
            chinese = run_resolver(
                "--task", "gen_component", "--cwd", str(root)
            )
            instructions = run_resolver(
                "--task",
                "gen_component",
                "--emit",
                "instructions",
                "--cwd",
                str(root),
            )

        self.assertEqual(english.returncode, 0, msg=english.stdout + english.stderr)
        self.assertEqual(chinese.returncode, 0, msg=chinese.stdout + chinese.stderr)
        self.assertEqual(
            instructions.returncode, 0, msg=instructions.stdout + instructions.stderr
        )
        self.assertIn("description_language: English", english.stdout)
        self.assertIn("description_language: zh-CN", chinese.stdout)
        self.assertNotEqual(
            manifest_value(english.stdout, "instructions_id"),
            manifest_value(chinese.stdout, "instructions_id"),
        )
        self.assertIn("Write descriptive contract values in zh-CN", instructions.stdout)
        self.assertIn("Keep stable contract labels", instructions.stdout)

    def test_contract_description_language_must_be_non_empty(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_language_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "config.yaml").write_text(
                "\n".join(
                    [
                        "schema: fr-mvvm-contract.config.v1",
                        "profile: language-test",
                        "contract:",
                        "  description_language: ''",
                        "tasks:",
                        "  gen_component:",
                        "    base: references/gen_component.md",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_resolver(
                "--task", "gen_component", "--cwd", str(root)
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "contract.description_language must be a non-empty string",
            result.stdout,
        )

    def test_transport_envelopes_are_resolved_from_project_profile(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_envelope_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "config.yaml").write_text(
                "\n".join(
                    [
                        "schema: fr-mvvm-contract.config.v1",
                        "profile: envelope-test",
                        "transport:",
                        "  request_data_envelope:",
                        "    mode: interceptor",
                        "    retrofit_extra:",
                        "      key: requestDataEnvelopeExtra",
                        "      import: package:example/request_envelope.dart",
                        "  bff_response_envelope:",
                        "    state_field: state",
                        "    code_field: code",
                        "    message_field: message",
                        "    data_field: data",
                        "tasks:",
                        "  gen_component:",
                        "    base: references/gen_component.md",
                    ]
                ),
                encoding="utf-8",
            )
            manifest = run_resolver("--task", "gen_component", "--cwd", str(root))
            instructions = run_resolver(
                "--task", "gen_component", "--emit", "instructions", "--cwd", str(root)
            )

        self.assertEqual(manifest.returncode, 0, msg=manifest.stdout + manifest.stderr)
        self.assertEqual(instructions.returncode, 0, msg=instructions.stdout + instructions.stderr)
        self.assertIn("request_data_envelope: interceptor", manifest.stdout)
        self.assertIn("bff_response_envelope: configured", manifest.stdout)
        self.assertIn(
            "does not generate Retrofit Service code", instructions.stdout
        )
        self.assertIn("wrappers and DTOs generated from OpenAPI", instructions.stdout)
        self.assertIn("`state`, `code`, `message`, and `data`", instructions.stdout)

    def test_request_data_envelope_rejects_unknown_mode(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_envelope_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "config.yaml").write_text(
                "\n".join(
                    [
                        "schema: fr-mvvm-contract.config.v1",
                        "profile: envelope-test",
                        "transport:",
                        "  request_data_envelope:",
                        "    mode: service",
                        "    retrofit_extra:",
                        "      key: requestDataEnvelopeExtra",
                        "      import: package:example/request_envelope.dart",
                        "tasks:",
                        "  gen_component:",
                        "    base: references/gen_component.md",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_resolver("--task", "gen_component", "--cwd", str(root))

        self.assertEqual(result.returncode, 1)
        self.assertIn("mode must be interceptor", result.stdout)

    def test_obsolete_service_base_url_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_service_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            config_path = config_root / "config.yaml"
            config_path.write_text(
                "\n".join(
                    [
                        "schema: fr-mvvm-contract.config.v1",
                        "profile: service-test",
                        "service:",
                        "  base_url: https://api.example.com",
                        "tasks:",
                        "  gen_component:",
                        "    base: references/gen_component.md",
                    ]
                ),
                encoding="utf-8",
            )
            result = run_resolver("--task", "gen_component", "--cwd", str(root))

        self.assertEqual(result.returncode, 1)
        self.assertIn("service.base_url is obsolete", result.stdout)
        self.assertIn("createAppDio(AppEnv)", result.stdout)

    def test_bundled_skill_fallback_works_in_new_repository(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_bundled_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()

            result = run_resolver("--task", "gen_page", "--cwd", str(root))

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("profile: generic", result.stdout)
            self.assertIn("status: ready", result.stdout)
            self.assertIn(
                str(SKILL_ROOT / "references/gen_page.md"),
                result.stdout,
            )

    def test_package_bff_has_generic_package_command(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_package_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()

            result = run_resolver("--task", "package_bff", "--cwd", str(root))

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("task: package_bff", result.stdout)
        self.assertIn("profile: generic", result.stdout)
        self.assertIn("package: uv run --script ", result.stdout)
        self.assertIn("package_bff.py", result.stdout)
        self.assertNotIn("  sync:", result.stdout)

    def test_backend_openapi_root_is_resolved_into_project_instructions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_openapi_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "config.yaml").write_text(
                "\n".join(
                    [
                        "schema: fr-mvvm-contract.config.v1",
                        "profile: docs-authority",
                        "transport:",
                        "  backend_openapi:",
                        "    local_root: build/docs/api/app-backend",
                        "tasks:",
                        "  validate:",
                        "    base: references/validate.md",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_resolver(
                "--task", "validate", "--emit", "instructions", "--cwd", str(root)
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("## Backend OpenAPI Authority", result.stdout)
        self.assertIn("build/docs/api/app-backend", result.stdout)
        self.assertIn("`openapi/example.openapi.json`", result.stdout)
        self.assertIn("not BFF package or synchronization payloads", result.stdout)

    def test_backend_openapi_root_must_stay_inside_repository(self) -> None:
        for configured_root in ("../docs", "/tmp/docs"):
            with self.subTest(configured_root=configured_root):
                with tempfile.TemporaryDirectory(
                    prefix="fr_resolve_openapi_escape_"
                ) as raw_root:
                    root = Path(raw_root)
                    (root / ".git").mkdir()
                    config_root = root / ".agents/skills-config/fr-mvvm-contract"
                    config_root.mkdir(parents=True)
                    (config_root / "config.yaml").write_text(
                        "\n".join(
                            [
                                "schema: fr-mvvm-contract.config.v1",
                                "profile: invalid-docs-root",
                                "transport:",
                                "  backend_openapi:",
                                f"    local_root: {configured_root}",
                                "tasks:",
                                "  validate:",
                                "    base: references/validate.md",
                            ]
                        ),
                        encoding="utf-8",
                    )

                    result = run_resolver("--task", "validate", "--cwd", str(root))

                self.assertEqual(result.returncode, 1)
                self.assertIn("transport.backend_openapi.local_root", result.stdout)

    def test_validate_routes_has_generic_module_command(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_routes_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()

            result = run_resolver("--task", "validate_routes", "--cwd", str(root))

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("task: validate_routes", result.stdout)
        self.assertIn("references/validate_routes.md", result.stdout)
        self.assertIn("validate_routes: uv run --script ", result.stdout)
        self.assertIn("scripts/validate_routes.py", result.stdout)
        self.assertIn("--module-file", result.stdout)

    def test_validate_routes_falls_back_when_profile_omits_task(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_routes_") as raw_root:
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

            result = run_resolver("--task", "validate_routes", "--cwd", str(root))

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("profile: existing", result.stdout)
        self.assertIn("scripts/validate_routes.py", result.stdout)

    def test_package_bff_falls_back_when_existing_profile_omits_task(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_package_") as raw_root:
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

            result = run_resolver("--task", "package_bff", "--cwd", str(root))

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("profile: existing", result.stdout)
        self.assertIn("package_bff.py", result.stdout)

    def test_project_package_and_sync_commands_override_generic_command(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_sync_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (config_root / "package_bff.md").write_text(
                "# Project BFF delivery\n", encoding="utf-8"
            )
            marker = root / "resolver-must-not-run-sync"
            (config_root / "config.yaml").write_text(
                "\n".join(
                    [
                        "schema: fr-mvvm-contract.config.v1",
                        "profile: delivery-repo",
                        "tasks:",
                        "  package_bff:",
                        "    base: references/package_bff.md",
                        "    profile: package_bff.md",
                        "    commands:",
                        "      package: ./tool/package_contracts.sh",
                        f"      sync: touch {marker}",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_resolver("--task", "package_bff", "--cwd", str(root))
            marker_created = marker.exists()

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("profile: delivery-repo", result.stdout)
        self.assertIn("package: ./tool/package_contracts.sh", result.stdout)
        self.assertIn(f"sync: touch {marker}", result.stdout)
        self.assertFalse(marker_created, "resolver must never execute sync commands")

    def test_authorized_sync_is_not_skipped_for_current_source_bff(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_sync_policy_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            result = run_resolver(
                "--task",
                "package_bff",
                "--emit",
                "instructions",
                "--cwd",
                str(root),
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(
            "run the resolved `sync` command",
            result.stdout,
        )
        self.assertIn("unconditionally after packaging", result.stdout)
        self.assertIn(
            "prove source freshness, not destination parity",
            result.stdout,
        )

    def test_shared_authority_requires_verified_remote_publication(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_publish_gate_") as raw:
            root = Path(raw)
            (root / ".git").mkdir()
            result = run_resolver(
                "--task",
                "package_bff",
                "--emit",
                "instructions",
                "--cwd",
                str(root),
            )

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertNotIn("`committed-local`", result.stdout)
        self.assertIn("exact remote ref", result.stdout)
        self.assertIn("complete only in `published` state", result.stdout)
        self.assertIn("Never describe a local commit", result.stdout)
        self.assertIn("itself authorization for the required push", result.stdout)
        self.assertIn("do not ask for a second push confirmation", result.stdout)

    def test_different_project_delivery_profiles_have_different_ids(self) -> None:
        manifests: list[str] = []
        for profile, sync in (
            ("alpha", "./tool/sync_alpha.sh"),
            ("beta", "./tool/sync_beta.sh"),
        ):
            with tempfile.TemporaryDirectory(prefix=f"fr_resolve_{profile}_") as raw:
                root = Path(raw)
                (root / ".git").mkdir()
                config_root = root / ".agents/skills-config/fr-mvvm-contract"
                config_root.mkdir(parents=True)
                (config_root / f"{profile}.md").write_text(
                    f"# {profile} delivery\n", encoding="utf-8"
                )
                (config_root / "config.yaml").write_text(
                    "\n".join(
                        [
                            "schema: fr-mvvm-contract.config.v1",
                            f"profile: {profile}",
                            "tasks:",
                            "  package_bff:",
                            "    base: references/package_bff.md",
                            f"    profile: {profile}.md",
                            "    commands:",
                            f"      sync: {sync}",
                        ]
                    ),
                    encoding="utf-8",
                )
                result = run_resolver(
                    "--task", "package_bff", "--cwd", str(root)
                )
                self.assertEqual(
                    result.returncode, 0, msg=result.stdout + result.stderr
                )
                manifests.append(result.stdout)

        self.assertNotEqual(
            manifest_value(manifests[0], "instructions_id"),
            manifest_value(manifests[1], "instructions_id"),
        )
        self.assertIn("profile: alpha", manifests[0])
        self.assertIn("sync: ./tool/sync_alpha.sh", manifests[0])
        self.assertIn("profile: beta", manifests[1])
        self.assertIn("sync: ./tool/sync_beta.sh", manifests[1])

    def test_package_profile_path_cannot_escape_config_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fr_resolve_escape_") as raw_root:
            root = Path(raw_root)
            (root / ".git").mkdir()
            config_root = root / ".agents/skills-config/fr-mvvm-contract"
            config_root.mkdir(parents=True)
            (root / ".agents/skills-config/outside.md").write_text(
                "# outside\n", encoding="utf-8"
            )
            (config_root / "config.yaml").write_text(
                "\n".join(
                    [
                        "schema: fr-mvvm-contract.config.v1",
                        "profile: escape",
                        "tasks:",
                        "  package_bff:",
                        "    base: references/package_bff.md",
                        "    profile: ../outside.md",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_resolver("--task", "package_bff", "--cwd", str(root))

        self.assertEqual(result.returncode, 1)
        self.assertIn("escapes", result.stdout)


if __name__ == "__main__":
    unittest.main()

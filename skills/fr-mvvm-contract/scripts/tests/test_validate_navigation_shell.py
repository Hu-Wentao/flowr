#!/usr/bin/env python3
"""Tests for persistent navigation-shell validation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPT_DIR = TEST_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_navigation_shell import (  # noqa: E402
    NavigationShellConfigError,
    validate,
)


class ValidateNavigationShellTest(unittest.TestCase):
    def _fixture(self, root: Path) -> Path:
        files = {
            "lib/app_router.dart": (
                "StatefulShellRoute.indexedStack(\n"
                "  builder: (_, __, navigationShell) => "
                "AgentShellScaffold(navigationShell: navigationShell),\n"
                ");\n"
            ),
            "lib/widgets/agent_shell_scaffold.dart": (
                "class AgentShellScaffold extends StatelessWidget {\n"
                "  final StatefulNavigationShell navigationShell;\n"
                "  Widget build(context) => Scaffold(\n"
                "    appBar: AgentShellHeader(),\n"
                "    body: navigationShell,\n"
                "    bottomNavigationBar: AgentBottomNavigation(\n"
                "      currentIndex: navigationShell.currentIndex,\n"
                "      onDestinationSelected: (index) => "
                "navigationShell.goBranch(index),\n"
                "    ),\n"
                "  );\n"
                "}\n"
            ),
            "lib/widgets/agent_bottom_navigation.dart": (
                "class AgentBottomNavigation extends StatelessWidget {\n"
                "  const AgentBottomNavigation({required this.currentIndex, "
                "required this.onDestinationSelected});\n"
                "  final int currentIndex;\n"
                "  final ValueChanged<int> onDestinationSelected;\n"
                "}\n"
            ),
            "lib/app/home/home.page.dart": (
                "@TypedGoRoute<HomePage>(path: '/home')\n"
                "class HomePage extends GoRouteData {}\n"
            ),
            "lib/app/home/home.v.dart": "class HomeView extends StatelessWidget {}\n",
            "lib/app/customers/customers.page.dart": (
                "@TypedGoRoute<CustomersPage>(path: '/customers')\n"
                "class CustomersPage extends GoRouteData {}\n"
            ),
            "lib/app/customers/customers.v.dart": (
                "class CustomersView extends StatelessWidget {}\n"
            ),
            "test/navigation_shell_test.dart": (
                "persistentNavigationShell onePumpBranchSwitch "
                "preservesBranchState deepLinkSelectsBranch rootOverlayCoversShell"
            ),
        }
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        profile = {
            "schema": "fr-mvvm-contract.navigation-shell.v1",
            "shells": [
                {
                    "id": "main",
                    "strategy": "stateful-indexed-stack",
                    "branch_switch_transition": "none",
                    "preserve_branch_state": True,
                    "router_path": "lib/app_router.dart",
                    "shell_path": "lib/widgets/agent_shell_scaffold.dart",
                    "shell_widget": "AgentShellScaffold",
                    "navigation_path": "lib/widgets/agent_bottom_navigation.dart",
                    "navigation_widget": "AgentBottomNavigation",
                    "selection_callback": "onDestinationSelected",
                    "top_region_widget": "AgentShellHeader",
                    "branches": [
                        {
                            "id": "home",
                            "route": "/home",
                            "page": "HomePage",
                            "route_path": "lib/app/home/home.page.dart",
                            "view_path": "lib/app/home/home.v.dart",
                        },
                        {
                            "id": "customers",
                            "route": "/customers",
                            "page": "CustomersPage",
                            "route_path": "lib/app/customers/customers.page.dart",
                            "view_path": "lib/app/customers/customers.v.dart",
                        },
                    ],
                    "tests": {
                        "globs": ["test/**/*.dart"],
                        "contains": [
                            "persistentNavigationShell",
                            "onePumpBranchSwitch",
                            "preservesBranchState",
                            "deepLinkSelectsBranch",
                            "rootOverlayCoversShell",
                        ],
                    },
                }
            ],
        }
        profile_path = root / "navigation-shell.json"
        profile_path.write_text(json.dumps(profile), encoding="utf-8")
        return profile_path

    def test_valid_shell_passes_all_checks(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            checks = validate(root, self._fixture(root))

        self.assertEqual(len(checks), 6)
        self.assertTrue(all(check.passed for check in checks))

    def test_branch_owned_scaffold_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            profile = self._fixture(root)
            (root / "lib/app/customers/customers.v.dart").write_text(
                "Widget build(context) => Scaffold();", encoding="utf-8"
            )
            checks = validate(root, profile)

        branch = next(
            check for check in checks if check.name == "main.branch_content_only"
        )
        self.assertFalse(branch.passed)
        self.assertIn("forbidden-text:Scaffold(", branch.detail)

    def test_navigation_must_not_import_or_call_branch_page(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            profile = self._fixture(root)
            navigation = root / "lib/widgets/agent_bottom_navigation.dart"
            navigation.write_text(
                navigation.read_text(encoding="utf-8")
                + "void open(context) => const HomePage().go(context);",
                encoding="utf-8",
            )
            checks = validate(root, profile)

        passive = next(
            check for check in checks if check.name == "main.passive_navigation"
        )
        self.assertFalse(passive.passed)
        self.assertIn("forbidden-text:HomePage", passive.detail)
        self.assertIn("forbidden-text:.go(context)", passive.detail)

    def test_profile_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            profile = self._fixture(root)
            data = json.loads(profile.read_text(encoding="utf-8"))
            data["shells"][0]["shell_path"] = "../outside.dart"
            profile.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaisesRegex(
                NavigationShellConfigError, "repository-relative"
            ):
                validate(root, profile)


if __name__ == "__main__":
    unittest.main()

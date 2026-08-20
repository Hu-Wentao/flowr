from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
UV_RUN_SCRIPT = ("uv", "run", "--script")
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from contract_core import ContractError  # noqa: E402
from figma_contract import parse_figma_contract_nodes  # noqa: E402
from prepare_figma_binding import parse_figma_url, prepare_binding  # noqa: E402


class PrepareFigmaBindingTest(unittest.TestCase):
    def draft(
        self,
        root: Path,
        name: str = "order_content",
        figma_url: str = ("https://www.figma.com/design/fileKey/FlowR?node-id=12-34"),
        *,
        component_only: bool = True,
    ) -> Path:
        directory = root / "lib" / "app" / name
        command = [
            *UV_RUN_SCRIPT,
            str(SCRIPTS / "draft_contract.py"),
            "--name",
            name,
            "--dir",
            str(directory),
            "--figma-url",
            figma_url,
            "--figma-frame",
            name.replace("_", " ").title(),
            "--figma-page-title",
            name.replace("_", " ").title(),
        ]
        if component_only:
            command.append("--component-only")
        else:
            command.extend(
                [
                    "--route",
                    f"/{name.replace('_', '-')}",
                    "--preview-width",
                    "360",
                    "--preview-height",
                    "780",
                    "--preview-wrapper",
                    f"{name.replace('_', '')}PreviewWrapper",
                ]
            )
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        return directory / f"{name}.c.dart"

    def add_figma_ownership(
        self,
        contract: Path,
        *,
        states: list[str] | None = None,
        references: list[str] | None = None,
        excluded: list[str] | None = None,
    ) -> None:
        sections: list[str] = []
        for title, entries in (
            ("Figma States", states),
            ("Figma References", references),
            ("Figma Excluded", excluded),
        ):
            if entries:
                sections.append(f"/// {title}:")
                sections.extend(f"/// {entry}" for entry in entries)
        source = contract.read_text(encoding="utf-8")
        contract.write_text(
            source.replace(
                "/// State Ownership:",
                "\n".join([*sections, "/// State Ownership:"]),
                1,
            ),
            encoding="utf-8",
        )

    def test_primary_binding_associates_node_frame_and_visible_page_title(self) -> None:
        nodes = parse_figma_contract_nodes(
            {
                "Figma": [
                    "- Frame: Untitled 42",
                    "- Page Title: Settings",
                    "- Node: https://www.figma.com/design/fileKey/FlowR?node-id=12-34",
                ]
            }
        )

        self.assertEqual(nodes.primary.node_id, "12:34")
        self.assertEqual(nodes.primary.name, "Untitled 42")
        self.assertEqual(nodes.primary.page_title, "Settings")

    def test_legacy_primary_binding_without_page_title_remains_readable(self) -> None:
        nodes = parse_figma_contract_nodes(
            {
                "Figma": [
                    "- Frame: Settings",
                    "- Node: https://www.figma.com/design/fileKey/FlowR?node-id=12-34",
                ]
            }
        )

        self.assertEqual(nodes.primary.node_id, "12:34")
        self.assertEqual(nodes.primary.name, "Settings")
        self.assertIsNone(nodes.primary.page_title)

    def test_prepares_project_relative_contract_binding_and_safe_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = self.draft(root)
            binding = prepare_binding(
                project_root=root,
                contract_files=[contract],
            )
            contract_source = contract.read_text(encoding="utf-8")

        self.assertIn("/// - Page Title: Order Content", contract_source)
        self.assertEqual(binding.fileKey, "fileKey")
        self.assertEqual(binding.nodeId, "12:34")
        self.assertEqual(binding.figmaRole, "primary")
        self.assertEqual(binding.componentNames, ["OrderContentView"])
        self.assertEqual(
            binding.contractPaths,
            ["lib/app/order_content/order_content.c.dart"],
        )
        self.assertEqual(binding.pagePaths, [])
        self.assertEqual(
            binding.visiblePathLines,
            ["lib/app/order_content/order_content.c.dart"],
        )
        self.assertEqual(binding.visibleCardName, "FlowR · Dart Paths · 12:34")
        self.assertEqual(
            json.loads(binding.bindingValue),
            {
                "version": 1,
                "contracts": ["lib/app/order_content/order_content.c.dart"],
            },
        )
        self.assertIn("setSharedPluginData", binding.writeCode)
        self.assertIn("figma.createAutoLayout('VERTICAL')", binding.writeCode)
        self.assertIn("host.children.find", binding.writeCode)
        self.assertIn("await card.screenshot", binding.writeCode)
        self.assertIn("visibleCardId", binding.writeCode)
        self.assertIn("visible Dart paths verification failed", binding.verifyCode)
        self.assertIn("await card.screenshot", binding.verifyCode)
        self.assertIn("verified: true", binding.verifyCode)
        self.assertLess(
            binding.writeCode.index("setSharedPluginData"),
            binding.writeCode.index("getSharedPluginData"),
        )
        self.assertNotIn("contract_path", binding.writeCode + binding.verifyCode)
        self.assertNotIn(str(root), binding.writeCode + binding.verifyCode)

    def test_page_binding_targets_frame_and_shows_contract_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = self.draft(root, component_only=False)
            binding = prepare_binding(
                project_root=root,
                contract_files=[contract],
            )

        self.assertEqual(
            binding.pagePaths,
            ["lib/app/order_content/order_content.page.dart"],
        )
        self.assertEqual(
            binding.visiblePathLines,
            ["lib/app/order_content/order_content.c.dart"],
        )
        self.assertNotIn("Contract lib/", binding.writeCode)
        self.assertIn("must target a concrete Figma Frame", binding.writeCode)
        self.assertIn("targetTop - card.height - 16", binding.writeCode)
        self.assertIn("contract card is not above its page", binding.verifyCode)
        for path in binding.visiblePathLines:
            self.assertIn(path, binding.writeCode)
            self.assertIn(path, binding.verifyCode)

    def test_rejects_multiple_page_adapters_in_one_visible_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            content = self.draft(root, "order_content", component_only=False)
            header = self.draft(root, "order_header", component_only=False)
            with self.assertRaisesRegex(ContractError, "one at a time"):
                prepare_binding(
                    project_root=root,
                    contract_files=[content, header],
                )

    def test_split_replaces_binding_with_sorted_complete_contract_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            content = self.draft(root, "order_content")
            header = self.draft(root, "order_header")
            binding = prepare_binding(
                project_root=root,
                contract_files=[content, header, content],
            )

        self.assertEqual(
            binding.contractPaths,
            [
                "lib/app/order_content/order_content.c.dart",
                "lib/app/order_header/order_header.c.dart",
            ],
        )
        self.assertEqual(
            binding.componentNames,
            ["OrderContentView", "OrderHeaderView"],
        )
        self.assertEqual(json.loads(binding.bindingValue)["version"], 1)
        self.assertEqual(
            json.loads(binding.bindingValue)["contracts"],
            binding.contractPaths,
        )

    def test_cli_emits_use_figma_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = self.draft(root)
            header = self.draft(root, "order_header")
            result = subprocess.run(
                [
                    *UV_RUN_SCRIPT,
                    str(SCRIPTS / "prepare_figma_binding.py"),
                    "--project-root",
                    str(root),
                    "--contract-file",
                    str(contract),
                    "--contract-file",
                    str(header),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["namespace"], "flowr")
        self.assertEqual(payload["key"], "contract_binding")
        self.assertEqual(payload["bindingVersion"], 1)
        self.assertEqual(payload["figmaRole"], "primary")
        self.assertEqual(len(payload["contractPaths"]), 2)
        self.assertEqual(payload["pagePaths"], [])
        self.assertEqual(len(payload["visiblePathLines"]), 2)
        self.assertEqual(payload["visibleCardName"], "FlowR · Dart Paths · 12:34")
        self.assertEqual(payload["nodeId"], "12:34")
        self.assertIn("getSharedPluginData", payload["verifyCode"])

    def test_binds_declared_state_frame_with_same_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = self.draft(
                root,
                figma_url="https://www.figma.com/design/fileKey/FlowR?node-id=12-34&m=dev",
                component_only=False,
            )
            self.add_figma_ownership(
                contract,
                states=[
                    "- editing | 56-78 | focused input with keyboard",
                    "- invalid | 90-12 | server validation error",
                ],
            )
            binding = prepare_binding(
                project_root=root,
                contract_files=[contract],
                target_node_id="56-78",
            )

        self.assertEqual(binding.nodeId, "56:78")
        self.assertEqual(binding.figmaRole, "state")
        self.assertEqual(
            binding.figmaUrl,
            "https://www.figma.com/design/fileKey/FlowR?node-id=56-78&m=dev",
        )
        self.assertEqual(
            binding.contractPaths,
            ["lib/app/order_content/order_content.c.dart"],
        )
        self.assertIn("FlowR · Dart Paths · 56:78", binding.writeCode)
        self.assertIn("must target a concrete Figma Frame", binding.verifyCode)

    def test_reference_and_excluded_nodes_are_not_bindable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = self.draft(root)
            self.add_figma_ownership(
                contract,
                references=[
                    "- topNav | https://figma.com/design/fileKey/FlowR?node-id=56-78 | shared visual reference only"
                ],
                excluded=[
                    "- dashboard | https://figma.com/design/fileKey/FlowR?node-id=90-12 | outside feature scope"
                ],
            )
            for node_id, role in (("56:78", "reference"), ("90:12", "excluded")):
                with self.subTest(node_id=node_id):
                    with self.assertRaisesRegex(ContractError, role):
                        prepare_binding(
                            project_root=root,
                            contract_files=[contract],
                            target_node_id=node_id,
                        )

    def test_rejects_duplicate_node_across_ownership_categories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = self.draft(root)
            self.add_figma_ownership(
                contract,
                states=["- editing | 56-78 | focused input"],
                references=[
                    "- duplicate | https://figma.com/design/fileKey/FlowR?node-id=56-78 | visual reference"
                ],
            )
            with self.assertRaisesRegex(ContractError, "exactly one"):
                prepare_binding(project_root=root, contract_files=[contract])

    def test_rejects_malformed_state_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = self.draft(root)
            self.add_figma_ownership(
                contract,
                states=["- editing 56-78"],
            )
            with self.assertRaisesRegex(ContractError, "must use"):
                prepare_binding(project_root=root, contract_files=[contract])

    def test_accepts_legacy_full_state_url_for_existing_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = self.draft(root)
            self.add_figma_ownership(
                contract,
                states=[
                    "- editing | https://figma.com/design/fileKey/FlowR?node-id=56-78 | legacy state binding"
                ],
            )
            binding = prepare_binding(
                project_root=root,
                contract_files=[contract],
                target_node_id="56-78",
            )

        self.assertEqual(binding.nodeId, "56:78")
        self.assertEqual(binding.figmaRole, "state")

    def test_rejects_contracts_for_different_figma_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            content = self.draft(root, "order_content")
            header = self.draft(
                root,
                "order_header",
                "https://figma.com/design/fileKey/FlowR?node-id=56-78",
            )
            with self.assertRaisesRegex(ContractError, "same Figma node"):
                prepare_binding(
                    project_root=root,
                    contract_files=[content, header],
                )

    def test_branch_url_uses_branch_key(self) -> None:
        self.assertEqual(
            parse_figma_url(
                "https://figma.com/design/main/branch/branchKey/FlowR?node-id=1-2"
            ),
            ("branchKey", "1:2"),
        )

    def test_rejects_missing_node_id(self) -> None:
        with self.assertRaisesRegex(ContractError, "node-id"):
            parse_figma_url("https://figma.com/design/fileKey/FlowR")

    def test_rejects_contract_outside_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as project_temporary:
            with tempfile.TemporaryDirectory() as other_temporary:
                other_root = Path(other_temporary)
                contract = self.draft(other_root)
                with self.assertRaisesRegex(ContractError, "project root"):
                    prepare_binding(
                        project_root=Path(project_temporary),
                        contract_files=[contract],
                    )


if __name__ == "__main__":
    unittest.main()

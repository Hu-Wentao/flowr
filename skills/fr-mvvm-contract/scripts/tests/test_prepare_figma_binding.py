from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from contract_core import ContractError  # noqa: E402
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
            sys.executable,
            str(SCRIPTS / "draft_contract.py"),
            "--name",
            name,
            "--dir",
            str(directory),
            "--figma-url",
            figma_url,
        ]
        if component_only:
            command.append("--component-only")
        else:
            command.extend(["--route", f"/{name.replace('_', '-')}"])
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        return directory / f"{name}.c.dart"

    def test_prepares_project_relative_contract_binding_and_safe_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = self.draft(root)
            binding = prepare_binding(
                project_root=root,
                contract_files=[contract],
            )

        self.assertEqual(binding.fileKey, "fileKey")
        self.assertEqual(binding.nodeId, "12:34")
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
                    sys.executable,
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
        self.assertEqual(len(payload["contractPaths"]), 2)
        self.assertEqual(payload["pagePaths"], [])
        self.assertEqual(len(payload["visiblePathLines"]), 2)
        self.assertEqual(payload["visibleCardName"], "FlowR · Dart Paths · 12:34")
        self.assertEqual(payload["nodeId"], "12:34")
        self.assertIn("getSharedPluginData", payload["verifyCode"])

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

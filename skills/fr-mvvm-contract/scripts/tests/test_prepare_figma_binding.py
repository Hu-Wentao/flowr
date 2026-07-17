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
    def draft(self, root: Path) -> Path:
        directory = root / "lib" / "app" / "order_content"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "draft_contract.py"),
                "--name",
                "order_content",
                "--dir",
                str(directory),
                "--figma-url",
                "https://www.figma.com/design/fileKey/FlowR?node-id=12-34",
                "--component-only",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return directory / "order_content.c.dart"

    def test_prepares_project_relative_contract_binding_and_safe_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = self.draft(root)
            binding = prepare_binding(
                project_root=root,
                contract_file=contract,
            )

        self.assertEqual(binding.fileKey, "fileKey")
        self.assertEqual(binding.nodeId, "12:34")
        self.assertEqual(binding.componentName, "OrderContentView")
        self.assertEqual(
            binding.contractPath,
            "lib/app/order_content/order_content.c.dart",
        )
        self.assertIn("setSharedPluginData", binding.writeCode)
        self.assertIn("mutatedNodeIds: [node.id]", binding.writeCode)
        self.assertIn("verified: true", binding.verifyCode)
        self.assertNotIn(str(root), binding.writeCode + binding.verifyCode)

    def test_cli_emits_use_figma_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = self.draft(root)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "prepare_figma_binding.py"),
                    "--project-root",
                    str(root),
                    "--contract-file",
                    str(contract),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["namespace"], "flowr")
        self.assertEqual(payload["key"], "contract_path")
        self.assertEqual(payload["nodeId"], "12:34")
        self.assertIn("getSharedPluginData", payload["verifyCode"])

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
                        contract_file=contract,
                    )


if __name__ == "__main__":
    unittest.main()

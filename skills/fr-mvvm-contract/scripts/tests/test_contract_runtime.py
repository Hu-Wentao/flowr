from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
for path in (SCRIPTS,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from contract_core import ContractError
from contract_parser import parse_component, parse_page


class ContractRuntimeTest(unittest.TestCase):
    def draft(self, directory: Path, *, page: bool = True) -> Path:
        command = [
            sys.executable,
            str(SCRIPTS / "draft_contract.py"),
            "--name",
            "order_content",
            "--dir",
            str(directory),
            "--figma-url",
            "https://www.figma.com/design/example?node-id=1",
        ]
        if not page:
            command.append("--component-only")
        subprocess.run(command, check=True, capture_output=True, text=True)
        return directory / "order_content.dart"

    def test_page_aggregates_sibling_component(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            page = parse_page(component.with_name("order_content.page.dart"))
            self.assertEqual(page.primary_view, "OrderContentView")
            self.assertEqual(page.component.page_args, "OrderContentPageArgs")
            self.assertEqual(page.component.events, ["OrderContentStarted"])

    def test_component_survives_page_adapter_removal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            component.with_name("order_content.page.dart").unlink()
            parsed = parse_component(component)
            self.assertEqual(parsed.view, "OrderContentView")

    def test_cross_route_component_can_be_drafted_under_components(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "lib/components/order_content"
            component = self.draft(directory, page=False)
            parsed = parse_component(component)
            contract = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )

            self.assertEqual(parsed.view, "OrderContentView")
            self.assertIn("lib/components for cross-route reuse", contract)
            self.assertFalse(component.with_name("order_content.page.dart").exists())

    def test_page_requires_explicit_primary_view_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            page = component.with_name("order_content.page.dart")
            page.write_text(page.read_text(encoding="utf-8").replace("/// Component: [OrderContentView]\n", ""), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "Component"):
                parse_page(page)

    def test_component_part_rejects_import(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            contract = component.with_name("order_content.c.dart")
            contract.write_text("import 'bad.dart';\n" + contract.read_text(encoding="utf-8"), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "must not declare"):
                parse_component(component)


if __name__ == "__main__":
    unittest.main()

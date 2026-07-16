from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
for path in (SCRIPTS,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from contract_core import ContractError  # noqa: E402
from contract_parser import parse_component, parse_page  # noqa: E402


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
            self.assertEqual(page.page_args, "OrderContentPageArgs")
            self.assertEqual(page.component.component_input, "OrderContentArgs")
            self.assertEqual(page.component.events, ["OrderContentStarted"])

            page_source = component.with_name("order_content.page.dart").read_text(
                encoding="utf-8"
            )
            contract_source = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )
            self.assertIn("class OrderContentPageArgs", page_source)
            self.assertIn("OrderContentArgs()", page_source)
            self.assertIn("class OrderContentArgs", contract_source)
            self.assertNotIn("PageArgs", contract_source)

    def test_draft_declares_json_serializable_part_for_fr_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            source = component.read_text(encoding="utf-8")
            contract = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )

            self.assertIn("@FrState", contract)
            self.assertIn("part 'order_content.freezed.dart';", source)
            self.assertIn("part 'order_content.g.dart';", source)
            self.assertNotIn(
                "Map<String, dynamic> _$OrderContentModelToJson", source + contract
            )

    def test_default_mode_drafts_required_bff_contract_without_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            source = component.read_text(encoding="utf-8")
            contract = component.with_name("order_content.c.dart").read_text(
                encoding="utf-8"
            )

            self.assertIn("package:fr_acdd/fr_acdd.dart", source)
            self.assertIn("@FrAcddPage(", contract)
            self.assertIn("mode: FrAcddMode.bff", contract)
            self.assertIn("@FrAcddDto(kind: FrAcddDtoKind.root)", contract)
            self.assertIn("@FrAcddFreezedJSON", contract)
            self.assertIn("POST <BASE>/order-content/bootstrap", contract)
            self.assertFalse(component.with_suffix(".bff.md").exists())

    def test_api_mode_has_no_bff_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "draft_contract.py"),
                    "--name",
                    "order_content",
                    "--dir",
                    str(directory),
                    "--figma-url",
                    "https://example.com",
                    "--mode",
                    "api",
                    "--api",
                    "GET /orders/:id",
                    "--component-only",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            source = (directory / "order_content.dart").read_text(encoding="utf-8")
            contract = (directory / "order_content.c.dart").read_text(encoding="utf-8")

            self.assertEqual(result.stderr, "")
            self.assertIn("/// API: GET /orders/:id", contract)
            self.assertNotIn("FrAcdd", source + contract)

    def test_legacy_bff_api_flag_remains_deprecated_compatibility_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "draft_contract.py"),
                    "--name",
                    "order_content",
                    "--dir",
                    str(directory),
                    "--figma-url",
                    "https://example.com",
                    "--api",
                    "BFF-JSON",
                    "--component-only",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("deprecated", result.stderr)
            self.assertIn(
                "FrAcddMode.bff",
                (directory / "order_content.c.dart").read_text(encoding="utf-8"),
            )

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
            self.assertEqual(
                parsed.sections["Shared Widgets"],
                ["review route widgets and lib/widgets before implementation."],
            )
            self.assertFalse(component.with_name("order_content.page.dart").exists())

    def test_page_requires_explicit_primary_view_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary))
            page = component.with_name("order_content.page.dart")
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    "/// Component: [OrderContentView]\n", ""
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "Component"):
                parse_page(page)

    def test_component_part_rejects_import(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                "import 'bad.dart';\n" + contract.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, "must not declare"):
                parse_component(component)

    def test_component_contract_rejects_page_args_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.draft(Path(temporary), page=False)
            contract = component.with_name("order_content.c.dart")
            contract.write_text(
                contract.read_text(encoding="utf-8").replace(
                    "OrderContentArgs", "OrderContentPageArgs"
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ContractError, r"must not declare \*PageArgs"):
                parse_component(component)


if __name__ == "__main__":
    unittest.main()

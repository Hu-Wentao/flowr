#!/usr/bin/env python3
"""Focused coverage for the breaking v9 frontend semantics parser."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from contract_core import ContractError  # noqa: E402
from contract_parser import parse_component  # noqa: E402
from frontend_semantics import parse_frontend_semantics  # noqa: E402
from generate_service import contract_endpoints  # noqa: E402
from read_contract import print_component  # noqa: E402


class FrontendSemanticsTest(unittest.TestCase):
    def sections(self) -> dict[str, list[str]]:
        return {
            "BFF-UI-API": [
                "GET /orders/:orderId",
                "[LoadOrderBffReq], [LoadOrderBffRsp]",
                "POST /orders/:orderId/submit",
                "[SubmitOrderBffReq], [SubmitOrderBffRsp]",
            ],
            "Behaviors": [
                "- Endpoint: [LoadOrderBffReq]",
                "UI Data: order summary and actions",
                "Source: approved order requirements",
                "Loading/Refresh: show initial loading and keep data on refresh",
                "Empty/Error: missing order is empty; failure supports retry",
                "- Endpoint: [SubmitOrderBffReq]",
                "Effect: submit the approved order",
                "Success: orderId confirms creation",
                "Failure: rejected -> restore submit state and show reason",
                "Navigation: app",
            ],
            "Request Field Sources": [
                "- Endpoint: [LoadOrderBffReq]",
                "- orderId <- OrderPage.orderId | selects the order",
                "- Endpoint: [SubmitOrderBffReq]",
                "- orderId <- OrderModel.orderId | selects the order",
                "- proof <- OrderModel.proof | authorizes submission",
            ],
            "Interactions": [
                "- Flow: load-order",
                "Trigger: startup",
                "Event: [OrderStarted]",
                "Uses: ui-api [LoadOrderBffReq]",
                "Guard: [OrderModel].isLoading == false",
                "Pending State: [OrderModel].isLoading = true; [OrderModel].error = null",
                "Success State: [OrderModel].orderId <- [LoadOrderBffRsp].orderId; [OrderModel].isLoading = false",
                "Failure State: [OrderModel].error <- error; [OrderModel].isLoading = false",
                "Concurrency: latest-wins",
                "Navigation: none",
                "- Flow: submit-order",
                "Trigger: widget [SubmitButton].tap",
                "Event: [OrderSubmitted]",
                "Uses: ui-api [SubmitOrderBffReq]",
                "Guard: [OrderModel].isSubmitting == false",
                "Pending State: [OrderModel].isSubmitting = true; [OrderModel].error = null",
                "Success State: [OrderModel].orderId <- [SubmitOrderBffRsp].orderId; [OrderModel].isSubmitting = false",
                "Failure State: [OrderModel].error <- error; [OrderModel].isSubmitting = false",
                "Concurrency: ignore-while-active",
                "Navigation: app-on-success",
            ],
        }

    def test_parses_mixed_query_and_command_records(self) -> None:
        parsed = parse_frontend_semantics(self.sections())

        self.assertEqual(
            [endpoint.request_type for endpoint in parsed.endpoints],
            ["LoadOrderBffReq", "SubmitOrderBffReq"],
        )
        self.assertEqual(
            [(behavior.endpoint, behavior.kind) for behavior in parsed.behaviors],
            [("LoadOrderBffReq", "query"), ("SubmitOrderBffReq", "command")],
        )
        self.assertEqual(parsed.request_sources[1].fields[1].field, "proof")
        self.assertEqual(parsed.interactions[0].endpoint, "LoadOrderBffReq")
        self.assertEqual(parsed.interactions[1].event, "OrderSubmitted")

    def test_request_type_is_unique_endpoint_identity(self) -> None:
        sections = self.sections()
        sections["BFF-UI-API"] += [
            "GET /orders/recent",
            "[LoadOrderBffReq], [RecentOrderBffRsp]",
        ]

        with self.assertRaisesRegex(
            ContractError, "request types are endpoint identities and must be unique"
        ):
            parse_frontend_semantics(sections)

    def test_singular_behavior_is_rejected(self) -> None:
        sections = self.sections()
        sections["Behavior"] = sections.pop("Behaviors")

        with self.assertRaisesRegex(ContractError, "singular `Behavior:` is obsolete"):
            parse_frontend_semantics(sections)

    def test_behavior_requires_exact_endpoint_scoped_field_set(self) -> None:
        sections = self.sections()
        sections["Behaviors"].remove("Navigation: app")

        with self.assertRaisesRegex(ContractError, "exactly the query or command"):
            parse_frontend_semantics(sections)

    def test_interaction_requires_complete_fixed_fields(self) -> None:
        sections = self.sections()
        sections["Interactions"].remove("Concurrency: latest-wins")

        with self.assertRaisesRegex(ContractError, "missing Concurrency"):
            parse_frontend_semantics(sections)

    def test_api_less_requires_explicit_no_interactions(self) -> None:
        parsed = parse_frontend_semantics({"BFF-UI-API": ["-"], "Interactions": ["none"]})
        self.assertEqual(parsed.endpoints, ())
        self.assertEqual(parsed.interactions, ())

        with self.assertRaisesRegex(ContractError, "explicitly declare"):
            parse_frontend_semantics({"BFF-UI-API": ["-"]})

    def test_endpoint_contract_cannot_disable_interaction_coverage(self) -> None:
        sections = self.sections()
        sections["Interactions"] = ["none"]

        with self.assertRaisesRegex(ContractError, "structured interaction flows"):
            parse_frontend_semantics(sections)

    def test_requires_flow_coverage_for_every_endpoint(self) -> None:
        sections = self.sections()
        sections["Interactions"] = sections["Interactions"][:10]

        with self.assertRaisesRegex(ContractError, "cover every UI endpoint"):
            parse_frontend_semantics(sections)

    def test_rejects_invalid_guard_and_concurrency(self) -> None:
        sections = self.sections()
        guard_index = sections["Interactions"].index(
            "Guard: [OrderModel].isLoading == false"
        )
        sections["Interactions"][guard_index] = "Guard: request is idle"
        with self.assertRaisesRegex(ContractError, "Guard must be"):
            parse_frontend_semantics(sections)

        sections = self.sections()
        concurrency_index = sections["Interactions"].index(
            "Concurrency: latest-wins"
        )
        sections["Interactions"][concurrency_index] = "Concurrency: debounce"
        with self.assertRaisesRegex(ContractError, "Concurrency must be"):
            parse_frontend_semantics(sections)

    def test_api_less_contract_may_declare_local_flow(self) -> None:
        parsed = parse_frontend_semantics(
            {
                "BFF-UI-API": ["-"],
                "Interactions": [
                    "- Flow: select-tab",
                    "Trigger: widget [TabBar].select",
                    "Event: [TabSelected]",
                    "Uses: local",
                    "Guard: none",
                    "Pending State: none",
                    "Success State: [TabModel].selectedIndex = 1",
                    "Failure State: none",
                    "Concurrency: not-applicable",
                    "Navigation: none",
                ],
            }
        )

        self.assertEqual(parsed.interactions[0].endpoint, None)
        self.assertEqual(parsed.interactions[0].success_mutations[0].target.field, "selectedIndex")

    def test_component_exposes_typed_records_to_consumers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component = root / "order.dart"
            component.write_text(
                "part 'order.c.dart';\npart 'order.v.dart';\n",
                encoding="utf-8",
            )
            contract_lines = [
                "/// State Ownership: page-owned [OrderViewModel]",
                "/// Public Views: [OrderView]",
                "/// Widget Tree: [OrderView] > [SubmitButton]",
                "/// Theme: none",
                "/// Events: [OrderStarted], [OrderSubmitted]",
                "/// ViewModels: [OrderViewModel]",
                "/// Models: [OrderModel]",
            ]
            for section, lines in self.sections().items():
                contract_lines.append(f"/// {section}:")
                for line in lines:
                    if section in {"Behaviors", "Interactions"} and not line.startswith(
                        "-"
                    ):
                        line = "- " + line
                    contract_lines.append(f"/// {line}")
            contract_lines.append("/// BFF Service: [OrderService]")
            contract_lines.append("part of 'order.dart';")
            (root / "order.c.dart").write_text(
                "\n".join(contract_lines) + "\n", encoding="utf-8"
            )
            (root / "order.v.dart").write_text(
                "part of 'order.dart';\nclass OrderView {}\n", encoding="utf-8"
            )

            parsed = parse_component(component)
            endpoints = contract_endpoints(parsed)
            self.assertEqual(endpoints[1].request_type, "SubmitOrderBffReq")
            self.assertEqual(parsed.behaviors[0].kind, "query")
            self.assertEqual(parsed.behaviors[1].kind, "command")

            output = io.StringIO()
            with redirect_stdout(output):
                print_component(parsed)
            rendered = output.getvalue()
            self.assertIn("endpoint.LoadOrderBffReq.method: GET", rendered)
            self.assertIn("behavior.SubmitOrderBffReq.kind: command", rendered)
            self.assertIn(
                "interaction.submit-order.concurrency: ignore-while-active",
                rendered,
            )


if __name__ == "__main__":
    unittest.main()

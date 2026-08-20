#!/usr/bin/env python3
"""Regression tests for semantic API approval and required BFF runtime gates."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1]
UV_RUN_SCRIPT = ("uv", "run", "--script")
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from contract_core import ContractError  # noqa: E402
from contract_parser import parse_component  # noqa: E402
from validate_contract import (  # noqa: E402
    validate_api_semantics,
    validate_contract as validate_full_contract,
    validate_runtime_integration,
)


class ContractSemanticsTest(unittest.TestCase):
    def write_fixture(
        self,
        root: Path,
        *,
        api_kind: str = "command",
        service: str | None = "[SubmitOrderService]",
    ) -> Path:
        (root / "pubspec.yaml").write_text(
            "name: semantic_fixture\n"
            "environment:\n  sdk: ^3.7.0\n"
            "dependencies:\n"
            "  dio: any\n"
            "  efficient_dio_logger: any\n"
            "  fr_acdd: any\n"
            "  json_annotation: any\n"
            "  retrofit: any\n"
            "dev_dependencies:\n"
            "  build_runner: any\n"
            "  json_serializable: any\n"
            "  retrofit_generator: any\n",
            encoding="utf-8",
        )
        directory = root / "lib/submit_order"
        directory.mkdir(parents=True)
        sdk = root / "lib/api/gen/orders_api.dart"
        sdk.parent.mkdir(parents=True)
        sdk.write_text("abstract class OrdersApi {}\n", encoding="utf-8")
        component = directory / "submit_order.dart"
        service_import = "import 'submit_order.srv.dart';\n" if service else ""
        component.write_text(
            "import 'package:fr_acdd/fr_acdd.dart';\n"
            f"{service_import}"
            "part 'submit_order.c.dart';\n"
            "part 'submit_order.v.dart';\n"
            "part 'submit_order.vm.dart';\n"
            "part 'submit_order.freezed.dart';\n"
            "part 'submit_order.g.dart';\n",
            encoding="utf-8",
        )
        if api_kind == "command":
            semantic_section = (
                "/// BFF-API:\n"
                "/// POST /orders\n"
                "/// [SubmitOrderBffReq], [SubmitOrderBffRsp]\n"
                "/// Behaviors:\n"
                "/// - Endpoint: [SubmitOrderBffReq]\n"
                "/// - Effect: create the order and reserve inventory\n"
                "/// - Success: orderCreated confirms the order was created\n"
                "/// - Failure: checkout-expired -> restore submit state and show restart checkout; inventory-changed -> restore submit state and show refresh cart\n"
                "/// - Navigation: app\n"
            )
        else:
            semantic_section = (
                "/// BFF-API:\n"
                "/// GET /orders/options\n"
                "/// [SubmitOrderBffReq], [SubmitOrderBffRsp]\n"
                "/// Behaviors:\n"
                "/// - Endpoint: [SubmitOrderBffReq]\n"
                "/// - UI Data: checkout summary and delivery options\n"
                "/// - Source: checkout service\n"
                "/// - Loading/Refresh: show loading and allow explicit refresh\n"
                "/// - Empty/Error: missing policy is blocking; show retry on failure\n"
            )
        service_declaration = f"/// BFF Service: {service}\n" if service else ""
        (directory / "submit_order.c.dart").write_text(
            "part of 'submit_order.dart';\n\n"
            "/// State Ownership: component-owned [SubmitOrderViewModel]\n"
            "/// Widget Tree: [SubmitOrderView] > [CartSummary], [SubmitButton]\n"
            "/// Theme: none\n"
            "/// Events: [SubmitOrderStarted], [SubmitOrderSubmitted]\n"
            "/// ViewModels: [SubmitOrderViewModel]\n"
            "/// Models: [SubmitOrderModel]\n"
            f"{semantic_section}"
            "/// Request Field Sources:\n"
            "/// - Endpoint: [SubmitOrderBffReq]\n"
            "/// - checkoutToken <- PrepareCheckoutBffRsp.checkoutToken | authorizes this checkout\n"
            "/// - cartId <- SubmitOrderModel.cartId | selects the cart to submit\n"
            "/// Interactions:\n"
            f"/// - Flow: {'submit-order' if api_kind == 'command' else 'load-order'}\n"
            f"/// - Trigger: {'widget [SubmitButton].tap' if api_kind == 'command' else 'external contract-test'}\n"
            f"/// - Event: [{'SubmitOrderSubmitted' if api_kind == 'command' else 'SubmitOrderStarted'}]\n"
            "/// - Uses: ui-api [SubmitOrderBffReq]\n"
            "/// - Guard: [SubmitOrderModel].isSubmitting == false\n"
            "/// - Pending State: [SubmitOrderModel].isSubmitting = true; [SubmitOrderModel].error = null\n"
            f"/// - Success State: [SubmitOrderModel].{'orderCreated <- [SubmitOrderBffRsp].orderCreated' if api_kind == 'command' else 'orderState <- [SubmitOrderBffRsp].orderState'}; [SubmitOrderModel].isSubmitting = false\n"
            "/// - Failure State: [SubmitOrderModel].error <- error; [SubmitOrderModel].isSubmitting = false\n"
            f"/// - Concurrency: {'ignore-while-active' if api_kind == 'command' else 'latest-wins'}\n"
            f"/// - Navigation: {'app-on-success' if api_kind == 'command' else 'none'}\n"
            f"{service_declaration}"
            "@FrAcddPage(mode: FrAcddMode.bff, namespace: 'submit_order')\n"
            "class SubmitOrderView {\n"
            "  Object build() => FrProvider;\n"
            "}\n\n"
            "@FrState\n"
            "class SubmitOrderModel with _$SubmitOrderModel {\n"
            "  const factory SubmitOrderModel({\n"
            "    @Default('') String cartId,\n"
            "    @Default(false) bool isSubmitting,\n"
            "    String? error,\n"
            "    @Default(false) bool orderCreated,\n"
            "    @Default('') String orderState,\n"
            "    String? nextRoute,\n"
            "  }) = _SubmitOrderModel;\n"
            "}\n\n"
            "@FrAcddDto(kind: FrAcddDtoKind.root)\n"
            "@FrAcddFreezedJSON\n"
            "abstract class SubmitOrderBffReq with _$SubmitOrderBffReq {\n"
            "  const factory SubmitOrderBffReq({\n"
            "    required String checkoutToken,\n"
            "    required String cartId,\n"
            "  }) = _SubmitOrderBffReq;\n"
            "  factory SubmitOrderBffReq.fromJson(Map<String, dynamic> json) =>\n"
            "      _$SubmitOrderBffReqFromJson(json);\n"
            "  Map<String, dynamic> toJson();\n"
            "}\n\n"
            "@FrAcddDto(kind: FrAcddDtoKind.root)\n"
            "@FrAcddFreezedJSON\n"
            "abstract class SubmitOrderBffRsp with _$SubmitOrderBffRsp {\n"
            "  const factory SubmitOrderBffRsp({\n"
            "    required bool orderCreated,\n"
            "    required String orderState,\n"
            "    String? nextRoute,\n"
            "  }) = _SubmitOrderBffRsp;\n"
            "  factory SubmitOrderBffRsp.fromJson(Map<String, dynamic> json) =>\n"
            "      _$SubmitOrderBffRspFromJson(json);\n"
            "}\n\n"
            "sealed class SubmitOrderEvent { const SubmitOrderEvent(); }\n"
            "final class SubmitOrderStarted extends SubmitOrderEvent {\n"
            "  const SubmitOrderStarted();\n"
            "}\n"
            "final class SubmitOrderSubmitted extends SubmitOrderEvent {\n"
            "  const SubmitOrderSubmitted();\n"
            "}\n",
            encoding="utf-8",
        )
        (directory / "submit_order.v.dart").write_text(
            "part of 'submit_order.dart';\n"
            "Object renderSubmit(SubmitOrderViewModel vm) => SubmitButton(\n"
            "  onPressed: () => vm.add(const SubmitOrderSubmitted()),\n"
            ");\n",
            encoding="utf-8",
        )
        (directory / "submit_order.vm.dart").write_text(
            self.valid_vm_source(), encoding="utf-8"
        )
        if service:
            (directory / "submit_order.srv.dart").write_text(
                "// GENERATED BY fr-mvvm-contract: generate_service.py\n"
                "import '../api/gen/orders_api.dart' as orders_sdk;\n"
                "import 'submit_order.dart';\n"
                "abstract class SubmitOrderService {\n"
                "  Future<SubmitOrderBffRsp> submitOrder(SubmitOrderBffReq request);\n"
                "}\n",
                encoding="utf-8",
            )
        return component

    def valid_vm_source(self) -> str:
        return (
            "part of 'submit_order.dart';\n"
            "class SubmitOrderViewModel {\n"
            "  SubmitOrderViewModel({required this.service}) {\n"
            "    on<SubmitOrderSubmitted>(_onSubmitted, transformer: droppable());\n"
            "  }\n"
            "  final SubmitOrderService service;\n"
            "  SubmitOrderModel get state => throw UnimplementedError();\n"
            "  void emit(SubmitOrderModel model) {}\n"
            "  void add(Object event) {}\n"
            "  void on<T>(Object handler, {Object? transformer}) {}\n"
            "  Future<void> _onSubmitted(\n"
            "    SubmitOrderSubmitted event,\n"
            "    Object emit,\n"
            "  ) async {\n"
            "    if (state.isSubmitting) return;\n"
            "    this.emit(state.copyWith(isSubmitting: true, error: null));\n"
            "    try {\n"
            "      final request = SubmitOrderBffReq(\n"
            "        checkoutToken: 'checkout-token',\n"
            "        cartId: state.cartId,\n"
            "      );\n"
            "      final response = await service.submitOrder(request);\n"
            "      this.emit(state.copyWith(\n"
            "        orderCreated: response.orderCreated,\n"
            "        nextRoute: response.orderCreated ? '/home' : null,\n"
            "        isSubmitting: false,\n"
            "      ));\n"
            "    } catch (error) {\n"
            "      this.emit(state.copyWith(\n"
            "        error: error.toString(),\n"
            "        isSubmitting: false,\n"
            "      ));\n"
            "    }\n"
            "  }\n"
            "}\n"
        )

    def validate_contract(self, component: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                *UV_RUN_SCRIPT,
                str(SCRIPTS / "validate_contract.py"),
                "--component-file",
                str(component),
                "--phase",
                "contract",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def mutate_contract(self, component: Path, old: str, new: str) -> None:
        contract = component.with_name("submit_order.c.dart")
        source = contract.read_text(encoding="utf-8")
        self.assertIn(old, source)
        contract.write_text(source.replace(old, new, 1), encoding="utf-8")

    def write_direct_backend_contract(self, component: Path) -> None:
        component.with_suffix(".bff.md").write_text(
            "## 后端业务流程与业务逻辑 API\n\n"
            "### 业务逻辑 API\n\n"
            "- [create] POST /orders | Parameters: body "
            "ReqWrapper<CreateOrderReq> | Response: RspWrapper<CreateOrderRsp>\n\n"
            "### 业务流程\n\n"
            "- [create] 创建订单\n"
            "## 前端 UI 数据接口\n",
            encoding="utf-8",
        )

    def replace_request_dto_with_sdk_alias(self, component: Path) -> None:
        contract = component.with_name("submit_order.c.dart")
        source = contract.read_text(encoding="utf-8")
        class_offset = source.index("abstract class SubmitOrderBffReq")
        start = source.rfind("@FrAcddDto", 0, class_offset)
        end = source.index("@FrAcddDto", class_offset)
        contract.write_text(
            source[:start]
            + "typedef SubmitOrderBffReq = orders_sdk.CreateOrderReq;\n\n"
            + source[end:],
            encoding="utf-8",
        )
        shell = component.read_text(encoding="utf-8")
        component.write_text(
            shell.replace(
                "import 'package:fr_acdd/fr_acdd.dart';\n",
                "import 'package:fr_acdd/fr_acdd.dart';\n"
                "import '../api/gen/orders_api.dart' as orders_sdk;\n",
            ),
            encoding="utf-8",
        )
        sdk = component.parents[1] / "api/gen/orders_api.dart"
        sdk.write_text(
            "class CreateOrderReq {\n"
            "  const CreateOrderReq({this.checkoutToken, this.cartId});\n"
            "  final String? checkoutToken;\n"
            "  final String? cartId;\n"
            "}\n",
            encoding="utf-8",
        )

    def assert_contract_error(self, component: Path, expected: str) -> None:
        result = self.validate_contract(component)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(expected, result.stderr)

    def test_complete_command_and_query_contracts_pass(self) -> None:
        for api_kind in ("command", "query"):
            with (
                self.subTest(api_kind=api_kind),
                tempfile.TemporaryDirectory() as temporary,
            ):
                component = self.write_fixture(Path(temporary), api_kind=api_kind)
                result = self.validate_contract(component)

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_same_backend_path_rejects_custom_request_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            self.write_direct_backend_contract(component)

            self.assert_contract_error(component, "replacement wrapper DTO")

    def test_same_backend_path_accepts_exact_sdk_request_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            self.write_direct_backend_contract(component)
            self.replace_request_dto_with_sdk_alias(component)

            result = self.validate_contract(component)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_command_contract_requires_every_closed_loop_field(self) -> None:
        fields = (
            "Effect",
            "Success",
            "Failure",
            "Navigation",
        )
        for field in fields:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                component = self.write_fixture(Path(temporary))
                contract = component.with_name("submit_order.c.dart")
                source = contract.read_text(encoding="utf-8")
                source = (
                    "\n".join(
                        line
                        for line in source.splitlines()
                        if not line.startswith(f"/// - {field}:")
                    )
                    + "\n"
                )
                contract.write_text(source, encoding="utf-8")
                self.assert_contract_error(component, field)

    def test_draft_and_bootstrap_placeholders_fail(self) -> None:
        mutations = {
            "/// - Effect: create the order and reserve inventory": (
                "/// - Effect: <PENDING_EFFECT>",
                "PENDING_EFFECT",
            ),
            "/// POST /orders": (
                "/// POST /submit-order/bootstrap",
                "forbidden generated placeholder",
            ),
        }
        for original, (replacement, expected) in mutations.items():
            with (
                self.subTest(replacement=replacement),
                tempfile.TemporaryDirectory() as temporary,
            ):
                component = self.write_fixture(Path(temporary))
                self.mutate_contract(component, original, replacement)
                self.assert_contract_error(component, expected)

    def test_legacy_api_type_and_sections_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            self.mutate_contract(
                component,
                "/// BFF-API:",
                "/// API Type: business\n/// BFF-API:",
            )
            self.assert_contract_error(component, "API Type is obsolete")

        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            self.mutate_contract(
                component,
                "/// Behaviors:",
                "/// Data:\n/// Behaviors:",
            )
            self.assert_contract_error(component, "legacy semantic sections")

    def test_mixed_query_and_command_behavior_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            self.mutate_contract(
                component,
                "/// - Effect: create the order and reserve inventory",
                "/// - UI Data: order summary\n"
                "/// - Effect: create the order and reserve inventory",
            )
            self.assert_contract_error(component, "exactly the query or command")

    def test_request_fields_require_exact_source_and_purpose(self) -> None:
        mutations = {
            "/// - cartId <- SubmitOrderModel.cartId | selects the cart to submit\n": (
                "",
                "missing source and purpose",
            ),
            "SubmitOrderModel.cartId | selects the cart to submit": (
                "<PENDING_SOURCE> | selects the cart to submit",
                "still contains draft placeholder",
            ),
            "cartId <- SubmitOrderModel.cartId": (
                "unknownField <- SubmitOrderModel.cartId",
                "missing source and purpose",
            ),
        }
        for original, (replacement, expected) in mutations.items():
            with (
                self.subTest(original=original),
                tempfile.TemporaryDirectory() as temporary,
            ):
                component = self.write_fixture(Path(temporary))
                self.mutate_contract(component, original, replacement)
                self.assert_contract_error(component, expected)

    def test_command_response_needs_business_result_and_matching_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            contract = component.with_name("submit_order.c.dart")
            source = contract.read_text(encoding="utf-8")
            source = (
                source.replace(
                    "    required bool orderCreated,\n    required String orderState,\n",
                    "    required String successMessage,\n"
                    "    required String nextScreen,\n",
                )
                .replace(
                    "orderCreated confirms the order was created",
                    "nextScreen selects the next screen",
                )
                .replace(
                    "[SubmitOrderBffRsp].orderCreated",
                    "[SubmitOrderBffRsp].successMessage",
                )
            )
            contract.write_text(source, encoding="utf-8")
            self.assert_contract_error(component, "only UI/navigation fields")

        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            self.mutate_contract(
                component,
                "orderCreated confirms the order was created",
                "server accepted the operation",
            )
            self.assert_contract_error(component, "must reference a non-UI field")

    def test_failure_cases_require_recovery_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            self.mutate_contract(
                component,
                "checkout-expired -> restore submit state and show restart checkout; inventory-changed -> restore submit state and show refresh cart",
                "checkout-expired, inventory-changed",
            )
            self.assert_contract_error(component, "App recovery/display")

    def test_omitted_bff_service_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary), service=None)
            result = self.validate_contract(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("contract-only delivery", result.stderr)

    def test_data_boundary_todo_is_rejected_before_contract_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            contract = component.with_name("submit_order.c.dart")
            source = contract.read_text(encoding="utf-8")
            contract.write_text(
                source.replace(
                    "/// BFF-API:\n",
                    "/// Data Boundary:\n"
                    "/// - TODO(data-boundary): order search — confirm the "
                    "approved OpenAPI operation.\n"
                    "/// BFF-API:\n",
                    1,
                ),
                encoding="utf-8",
            )

            result = self.validate_contract(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("TODO(data-boundary)", result.stderr)

    def test_pending_figma_data_is_rejected_before_contract_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            contract = component.with_name("submit_order.c.dart")
            source = contract.read_text(encoding="utf-8")
            contract.write_text(
                source.replace(
                    "/// State Ownership:",
                    "/// Figma Data:\n"
                    "/// - [order.summary.total] | Node: 1:2 | Kind: remote | "
                    "Binding: pending | Render: SubmitOrderModel.total | "
                    "Source: TODO(figma-data): confirm order total source | "
                    "Fixture: order.summary.total\n"
                    "/// State Ownership:",
                    1,
                ),
                encoding="utf-8",
            )

            result = self.validate_contract(component)

        self.assertEqual(result.returncode, 2)
        self.assertIn("pending Figma Data", result.stderr)

    def test_obsolete_runtime_and_none_service_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary))
            self.mutate_contract(
                component,
                "@FrAcddPage",
                "/// BFF Runtime: contract-only\n@FrAcddPage",
            )
            self.assert_contract_error(component, "BFF Runtime is obsolete")

        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(Path(temporary), service="none")
            self.assert_contract_error(component, "BFF v9 requires")

    def test_required_runtime_complete_integration_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(
                Path(temporary), service="[SubmitOrderService]"
            )
            parsed = parse_component(component)
            contract = component.with_name("submit_order.c.dart").read_text(
                encoding="utf-8"
            )
            validate_api_semantics(parsed, contract)
            validate_runtime_integration(parsed, contract)

    def test_required_runtime_accepts_modified_service_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(
                Path(temporary), service="[SubmitOrderService]"
            )
            service_file = component.with_name("submit_order.srv.dart")
            service_file.write_text(
                service_file.read_text(encoding="utf-8").replace(
                    "// GENERATED BY fr-mvvm-contract: generate_service.py\n", ""
                ),
                encoding="utf-8",
            )
            parsed = parse_component(component)
            contract = component.with_name("submit_order.c.dart").read_text(
                encoding="utf-8"
            )
            validate_runtime_integration(parsed, contract)

    def test_required_runtime_rejects_missing_service_class(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(
                Path(temporary), service="[DifferentService]"
            )
            parsed = parse_component(component)
            contract = component.with_name("submit_order.c.dart").read_text(
                encoding="utf-8"
            )
            with self.assertRaisesRegex(ContractError, "does not declare class"):
                validate_runtime_integration(parsed, contract)

    def test_legacy_scoped_service_declaration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(
                Path(temporary), service="[SubmitOrderService]"
            )
            self.mutate_contract(
                component,
                "BFF Service: [SubmitOrderService]",
                "BFF Service: shared [SubmitOrderService]",
            )
            parsed = parse_component(component)
            contract = component.with_name("submit_order.c.dart").read_text(
                encoding="utf-8"
            )
            with self.assertRaisesRegex(ContractError, "BFF v9 requires"):
                validate_api_semantics(parsed, contract)

    def test_required_data_runtime_uses_registered_load_handler(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(
                Path(temporary),
                api_kind="query",
                service="[SubmitOrderService]",
            )
            vm = component.with_name("submit_order.vm.dart")
            vm.write_text(
                vm.read_text(encoding="utf-8")
                .replace(
                    "on<SubmitOrderSubmitted>(_onSubmitted, transformer: droppable())",
                    "on<SubmitOrderStarted>(_onSubmitted, transformer: restartable())",
                )
                .replace(
                    "orderCreated: response.orderCreated,",
                    "orderState: response.orderState,",
                )
                .replace(
                    "        nextRoute: response.orderCreated ? '/home' : null,\n",
                    "",
                ),
                encoding="utf-8",
            )
            parsed = parse_component(component)
            contract = component.with_name("submit_order.c.dart").read_text(
                encoding="utf-8"
            )
            validate_api_semantics(parsed, contract)
            validate_runtime_integration(parsed, contract)

    def test_final_phase_executes_required_runtime_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component = self.write_fixture(
                Path(temporary), service="[SubmitOrderService]"
            )
            for suffix in ("freezed", "g"):
                component.with_name(f"submit_order.{suffix}.dart").write_text(
                    "part of 'submit_order.dart';\n", encoding="utf-8"
                )
            parsed = parse_component(component)
            with mock.patch("validate_contract.generate_bff"):
                validate_full_contract(None, parsed, phase="final")

            vm = component.with_name("submit_order.vm.dart")
            vm.write_text(
                vm.read_text(encoding="utf-8").replace(
                    "final response = await service.submitOrder(request);",
                    "final response = SubmitOrderBffRsp("
                    "orderCreated: true, orderState: 'active');",
                ),
                encoding="utf-8",
            )
            parsed = parse_component(component)
            with (
                mock.patch("validate_contract.generate_bff"),
                self.assertRaisesRegex(ContractError, "must await SubmitOrderService"),
            ):
                validate_full_contract(None, parsed, phase="final")

    def test_required_runtime_rejects_missing_execution_steps(self) -> None:
        mutations = {
            "import 'submit_order.srv.dart';\n": (
                "",
                "BFF service must be imported",
                "shell",
            ),
            "required this.service": (
                "",
                "constructor must receive",
                "vm",
            ),
            ") async {": (
                ") {",
                "must return Future and be async",
                "vm",
            ),
            "      final request = SubmitOrderBffReq(\n"
            "        checkoutToken: 'checkout-token',\n"
            "        cartId: state.cartId,\n"
            "      );\n": (
                "",
                "must construct SubmitOrderBffReq",
                "vm",
            ),
            "final response = await service.submitOrder(request);": (
                "final response = SubmitOrderBffRsp(orderCreated: true, orderState: 'active');",
                "must await SubmitOrderService",
                "vm",
            ),
            "orderCreated: response.orderCreated,\n"
            "        nextRoute: response.orderCreated ? '/home' : null": (
                "orderCreated: true,\n        nextRoute: '/home'",
                "Success State must assign",
                "vm",
            ),
            "        error: error.toString(),\n": (
                "",
                "Failure State",
                "vm",
            ),
            "service.submitOrder(request)": (
                "service.submitOrder(Object())",
                "must pass its SubmitOrderBffReq",
                "vm",
            ),
            "    try {\n": (
                "    this.emit(state.copyWith(nextRoute: '/home'));\n    try {\n",
                "must not navigate",
                "vm",
            ),
            "    } catch (error) {\n": (
                "    } catch (error) {\n"
                "      this.emit(state.copyWith(nextRoute: '/error'));\n",
                "must not navigate",
                "vm",
            ),
            "        isSubmitting: false,\n      ));\n    } catch": (
                "      ));\n    } catch",
                "Success State",
                "vm",
            ),
        }
        for original, (replacement, expected, target) in mutations.items():
            with (
                self.subTest(expected=expected),
                tempfile.TemporaryDirectory() as temporary,
            ):
                component = self.write_fixture(
                    Path(temporary), service="[SubmitOrderService]"
                )
                path = (
                    component
                    if target == "shell"
                    else component.with_name(
                        "submit_order.c.dart"
                        if target == "contract"
                        else "submit_order.vm.dart"
                    )
                )
                source = path.read_text(encoding="utf-8")
                self.assertIn(original, source)
                path.write_text(
                    source.replace(original, replacement, 1), encoding="utf-8"
                )
                parsed = parse_component(component)
                contract = component.with_name("submit_order.c.dart").read_text(
                    encoding="utf-8"
                )
                with self.assertRaisesRegex(ContractError, expected):
                    validate_runtime_integration(parsed, contract)


if __name__ == "__main__":
    unittest.main()

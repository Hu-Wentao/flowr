#!/usr/bin/env python3
"""Focused contract/runtime coverage for BFF v9 endpoint interaction flows."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from contract_core import ContractError  # noqa: E402
from contract_parser import parse_component  # noqa: E402
from validate_contract import (  # noqa: E402
    validate_api_semantics,
    validate_runtime_integration,
)


class InteractionValidationTest(unittest.TestCase):
    def write_fixture(self, root: Path) -> Path:
        directory = root / "lib/order"
        directory.mkdir(parents=True)
        sdk = root / "lib/api/gen/orders_api.dart"
        sdk.parent.mkdir(parents=True)
        sdk.write_text("abstract class OrdersApi {}\n", encoding="utf-8")
        component = directory / "order.dart"
        component.write_text(
            "import 'order.srv.dart';\n"
            "part 'order.c.dart';\n"
            "part 'order.v.dart';\n"
            "part 'order.vm.dart';\n",
            encoding="utf-8",
        )
        (directory / "order.c.dart").write_text(
            "/// State Ownership: component-owned [OrderViewModel]\n"
            "/// Public Views: [OrderView]\n"
            "/// Widget Tree: [OrderView] > [SubmitButton]\n"
            "/// Theme: none\n"
            "/// Events: [OrderStarted], [OrderSubmitted]\n"
            "/// Startup Event: [OrderStarted]\n"
            "/// ViewModels: [OrderViewModel]\n"
            "/// Models: [OrderModel]\n"
            "/// BFF-API:\n"
            "/// GET /orders/:orderId\n"
            "/// [LoadOrderBffReq], [LoadOrderBffRsp]\n"
            "/// POST /orders/:orderId/submit\n"
            "/// [SubmitOrderBffReq], [SubmitOrderBffRsp]\n"
            "/// Behaviors:\n"
            "/// - Endpoint: [LoadOrderBffReq]\n"
            "/// - UI Data: order details\n"
            "/// - Source: approved order requirements\n"
            "/// - Loading/Refresh: load on startup and keep old data on refresh\n"
            "/// - Empty/Error: missing order is empty; failure supports retry\n"
            "/// - Endpoint: [SubmitOrderBffReq]\n"
            "/// - Effect: submit the loaded order\n"
            "/// - Success: confirmationId confirms submission\n"
            "/// - Failure: rejected -> restore submit state and show reason\n"
            "/// - Navigation: app\n"
            "/// Request Field Sources:\n"
            "/// - Endpoint: [LoadOrderBffReq]\n"
            "/// - orderId <- OrderPage.orderId | selects the order\n"
            "/// - Endpoint: [SubmitOrderBffReq]\n"
            "/// - orderId <- OrderModel.orderId | selects the order\n"
            "/// Interactions:\n"
            "/// - Flow: load-order\n"
            "/// - Trigger: startup\n"
            "/// - Event: [OrderStarted]\n"
            "/// - Uses: ui-api [LoadOrderBffReq]\n"
            "/// - Guard: [OrderModel].isLoading == false\n"
            "/// - Pending State: [OrderModel].isLoading = true; [OrderModel].error = null\n"
            "/// - Success State: [OrderModel].orderId <- [LoadOrderBffRsp].orderId; [OrderModel].isLoading = false\n"
            "/// - Failure State: [OrderModel].error <- error; [OrderModel].isLoading = false\n"
            "/// - Concurrency: latest-wins\n"
            "/// - Navigation: none\n"
            "/// - Flow: submit-order\n"
            "/// - Trigger: widget [SubmitButton].tap\n"
            "/// - Event: [OrderSubmitted]\n"
            "/// - Uses: ui-api [SubmitOrderBffReq]\n"
            "/// - Guard: [OrderModel].isSubmitting == false\n"
            "/// - Pending State: [OrderModel].isSubmitting = true; [OrderModel].error = null\n"
            "/// - Success State: [OrderModel].confirmationId <- [SubmitOrderBffRsp].confirmationId; [OrderModel].isSubmitting = false\n"
            "/// - Failure State: [OrderModel].error <- error; [OrderModel].isSubmitting = false\n"
            "/// - Concurrency: ignore-while-active\n"
            "/// - Navigation: app-on-success\n"
            "/// BFF Service: [OrderService]\n"
            "part of 'order.dart';\n\n"
            "class OrderModel {\n"
            "  const factory OrderModel({\n"
            "    required String orderId,\n"
            "    required String confirmationId,\n"
            "    required bool isLoading,\n"
            "    required bool isSubmitting,\n"
            "    String? error,\n"
            "  }) = OrderModelImpl;\n"
            "}\n"
            "class LoadOrderBffReq { const factory LoadOrderBffReq({required String orderId}) = LoadOrderBffReqImpl; }\n"
            "class LoadOrderBffRsp { const factory LoadOrderBffRsp({required String orderId}) = LoadOrderBffRspImpl; }\n"
            "class SubmitOrderBffReq { const factory SubmitOrderBffReq({required String orderId}) = SubmitOrderBffReqImpl; }\n"
            "class SubmitOrderBffRsp { const factory SubmitOrderBffRsp({required String confirmationId}) = SubmitOrderBffRspImpl; }\n"
            "class OrderStarted {}\n"
            "class OrderSubmitted {}\n",
            encoding="utf-8",
        )
        (directory / "order.v.dart").write_text(
            "part of 'order.dart';\n"
            "class OrderView {\n"
            "  Object build(OrderViewModel vm) => SubmitButton(\n"
            "    onPressed: () => vm.add(const OrderSubmitted()),\n"
            "  );\n"
            "}\n",
            encoding="utf-8",
        )
        (directory / "order.srv.dart").write_text(
            "import '../api/gen/orders_api.dart';\n"
            "class OrderService {\n"
            "  Future<LoadOrderBffRsp> loadOrder(LoadOrderBffReq request) => throw UnimplementedError();\n"
            "  Future<SubmitOrderBffRsp> submitOrder(SubmitOrderBffReq request) => throw UnimplementedError();\n"
            "}\n",
            encoding="utf-8",
        )
        (directory / "order.vm.dart").write_text(
            "part of 'order.dart';\n"
            "class OrderViewModel {\n"
            "  OrderViewModel({required this.service}) {\n"
            "    on<OrderStarted>(_onStarted, transformer: restartable());\n"
            "    on<OrderSubmitted>(_onSubmitted, transformer: droppable());\n"
            "  }\n"
            "  final OrderService service;\n"
            "  OrderModel get state => throw UnimplementedError();\n"
            "  void add(Object event) {}\n"
            "  void emit(Object state) {}\n"
            "  void on<T>(Object handler, {Object? transformer}) {}\n"
            "  Future<void> _onStarted(OrderStarted event, Object emit) async {\n"
            "    if (state.isLoading) return;\n"
            "    this.emit(state.copyWith(isLoading: true, error: null));\n"
            "    try {\n"
            "      final request = LoadOrderBffReq(orderId: state.orderId);\n"
            "      final response = await service.loadOrder(request);\n"
            "      this.emit(state.copyWith(orderId: response.orderId, isLoading: false));\n"
            "    } catch (error) {\n"
            "      this.emit(state.copyWith(error: error.toString(), isLoading: false));\n"
            "    }\n"
            "  }\n"
            "  Future<void> _onSubmitted(OrderSubmitted event, Object emit) async {\n"
            "    if (state.isSubmitting) return;\n"
            "    this.emit(state.copyWith(isSubmitting: true, error: null));\n"
            "    try {\n"
            "      final request = SubmitOrderBffReq(orderId: state.orderId);\n"
            "      final response = await service.submitOrder(request);\n"
            "      this.emit(state.copyWith(confirmationId: response.confirmationId, isSubmitting: false));\n"
            "      OrderDonePage().go(context);\n"
            "    } catch (error) {\n"
            "      this.emit(state.copyWith(error: error.toString(), isSubmitting: false));\n"
            "    }\n"
            "  }\n"
            "}\n",
            encoding="utf-8",
        )
        return component

    def test_validates_each_endpoint_and_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            validate_api_semantics(component, contract)
            validate_runtime_integration(component, contract)

    def test_missing_second_handler_names_its_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "    on<OrderSubmitted>(_onSubmitted, transformer: droppable());\n",
                    "",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "Flow `submit-order`"):
                validate_runtime_integration(component, contract)

    def test_widget_trigger_must_dispatch_from_the_declared_widget_action(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            view = component_file.with_name("order.v.dart")
            view.write_text(view.read_text().replace("SubmitButton(", "RetryButton("))
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "Flow `submit-order`.*SubmitButton"):
                validate_runtime_integration(component, contract)

    def test_widget_trigger_rejects_an_unrelated_dispatch_receiver(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            view = component_file.with_name("order.v.dart")
            view.write_text(
                view.read_text()
                .replace(
                    "Object build(OrderViewModel vm)",
                    "Object build(OrderViewModel vm, UnrelatedBloc bloc)",
                )
                .replace("vm.add(", "bloc.add(")
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "Flow `submit-order`.*callback"):
                validate_runtime_integration(component, contract)

    def test_widget_trigger_rejects_untyped_receiver_shadowing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            view = component_file.with_name("order.v.dart")
            view.write_text(
                view.read_text().replace(
                    "onPressed: () => vm.add(",
                    "onPressed: (vm) => vm.add(",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "Flow `submit-order`.*callback"):
                validate_runtime_integration(component, contract)

    def test_guard_runtime_must_use_the_inverse_contract_polarity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "if (state.isSubmitting) return;",
                    "if (!state.isSubmitting) return;",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "Flow `submit-order`.*inverse"):
                validate_runtime_integration(component, contract)

    def test_commented_guard_does_not_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "    if (state.isSubmitting) return;",
                    "    // if (state.isSubmitting) return;",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "Flow `submit-order`.*inverse"):
                validate_runtime_integration(component, contract)

    def test_commented_pending_state_write_does_not_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "    this.emit(state.copyWith(isSubmitting: true, error: null));",
                    "    // this.emit(state.copyWith(isSubmitting: true, error: null));",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "Flow `submit-order`.*Pending"):
                validate_runtime_integration(component, contract)

    def test_navigation_after_try_catch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "      this.emit(state.copyWith(error: error.toString(), isSubmitting: false));\n"
                    "    }\n"
                    "  }\n"
                    "}\n",
                    "      this.emit(state.copyWith(error: error.toString(), isSubmitting: false));\n"
                    "    }\n"
                    "    OrderDonePage().go(context);\n"
                    "  }\n"
                    "}\n",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "Flow `submit-order`.*after try/catch"):
                validate_runtime_integration(component, contract)

    def test_local_flow_navigation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            contract_file = component_file.with_name("order.c.dart")
            contract_file.write_text(
                contract_file.read_text()
                .replace(
                    "/// Events: [OrderStarted], [OrderSubmitted]",
                    "/// Events: [OrderStarted], [OrderSubmitted], [TabSelected]",
                )
                .replace(
                    "/// Widget Tree: [OrderView] > [SubmitButton]",
                    "/// Widget Tree: [OrderView] > [SubmitButton] > [TabBar]",
                )
                .replace(
                    "/// BFF Service: [OrderService]",
                    "/// - Flow: select-tab\n"
                    "/// - Trigger: widget [TabBar].select\n"
                    "/// - Event: [TabSelected]\n"
                    "/// - Uses: local\n"
                    "/// - Guard: none\n"
                    "/// - Pending State: none\n"
                    "/// - Success State: [OrderModel].isLoading = false\n"
                    "/// - Failure State: none\n"
                    "/// - Concurrency: not-applicable\n"
                    "/// - Navigation: none\n"
                    "/// BFF Service: [OrderService]",
                )
                .replace("class OrderSubmitted {}", "class OrderSubmitted {}\nclass TabSelected {}")
            )
            view = component_file.with_name("order.v.dart")
            view.write_text(
                view.read_text().replace(
                    "  );",
                    "    child: TabBar(onSelected: () => vm.add(const TabSelected())),\n"
                    "  );",
                )
            )
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text()
                .replace(
                    "    on<OrderSubmitted>(_onSubmitted, transformer: droppable());",
                    "    on<OrderSubmitted>(_onSubmitted, transformer: droppable());\n"
                    "    on<TabSelected>(_onTabSelected);",
                )
                .replace(
                    "  Future<void> _onStarted",
                    "  void _onTabSelected(TabSelected event, Object emit) {\n"
                    "    this.emit(state.copyWith(isLoading: false));\n"
                    "    OrdersPage().go(context);\n"
                    "  }\n"
                    "  Future<void> _onStarted",
                )
            )
            component = parse_component(component_file)
            contract = contract_file.read_text()

            with self.assertRaisesRegex(ContractError, "Flow `select-tab`.*navigates"):
                validate_runtime_integration(component, contract)

    def test_guard_must_run_before_pending_state_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "    if (state.isSubmitting) return;\n"
                    "    this.emit(state.copyWith(isSubmitting: true, error: null));",
                    "    this.emit(state.copyWith(isSubmitting: true, error: null));\n"
                    "    if (state.isSubmitting) return;",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "Flow `submit-order`.*first executable"
            ):
                validate_runtime_integration(component, contract)

    def test_response_mapping_must_be_inside_the_state_emit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "      this.emit(state.copyWith(confirmationId: response.confirmationId, isSubmitting: false));",
                    "      this.emit((confirmationId: response.confirmationId,));\n"
                    "      this.emit(state.copyWith(confirmationId: 'wrong', isSubmitting: false));",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "Flow `submit-order`.*exact target"):
                validate_runtime_integration(component, contract)

    def test_response_mapping_rejects_a_forged_rhs_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "confirmationId: response.confirmationId,",
                    "confirmationId: response.confirmationId + '-forged',",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "Flow `submit-order`.*exact target"):
                validate_runtime_integration(component, contract)

    def test_wrong_flow_transformer_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "on<OrderStarted>(_onStarted, transformer: restartable())",
                    "on<OrderStarted>(_onStarted, transformer: sequential())",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "Flow `load-order`.*restartable"):
                validate_runtime_integration(component, contract)

    def test_second_flow_cannot_reuse_the_wrong_operation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "await service.submitOrder(request)",
                    "await service.loadOrder(request)",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "Flow `submit-order`.*submitOrder"):
                validate_runtime_integration(component, contract)

    def test_unknown_flow_model_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            contract_file = component_file.with_name("order.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "[OrderModel].confirmationId <- [SubmitOrderBffRsp].confirmationId",
                    "[OrderModel].missing <- [SubmitOrderBffRsp].confirmationId",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(ContractError, "Flow `submit-order`.*missing"):
                validate_api_semantics(component, contract_file.read_text())


if __name__ == "__main__":
    unittest.main()

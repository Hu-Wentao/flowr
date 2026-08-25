#!/usr/bin/env python3
"""Focused contract/runtime coverage for endpoint and local interaction flows."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from contract_core import ContractError  # noqa: E402
from contract_parser import parse_component  # noqa: E402
from validate_contract import (  # noqa: E402
    _copy_with_assignments,
    _emit_arguments,
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
            "/// BFF-UI-API:\n"
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
            "/// - Pending State: [OrderModel].isSubmitting = true; [OrderModel].error = null; [OrderModel].navigationSignal = null\n"
            "/// - Success State: [OrderModel].confirmationId <- [SubmitOrderBffRsp].confirmationId; [OrderModel].isSubmitting = false; [OrderModel].navigationSignal = OrderNavigation.confirmation\n"
            "/// - Failure State: [OrderModel].error <- error; [OrderModel].isSubmitting = false\n"
            "/// - Concurrency: ignore-while-active\n"
            "/// - Navigation: view-listener-on-success [OrderModel].navigationSignal = OrderNavigation.confirmation\n"
            "/// BFF Service: [OrderService]\n"
            "part of 'order.dart';\n\n"
            "class OrderModel {\n"
            "  const factory OrderModel({\n"
            "    required String orderId,\n"
            "    required String confirmationId,\n"
            "    required bool isLoading,\n"
            "    required bool isSubmitting,\n"
            "    String? error,\n"
            "    OrderNavigation? navigationSignal,\n"
            "  }) = OrderModelImpl;\n"
            "}\n"
            "enum OrderNavigation { confirmation }\n"
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
            "  Object build(OrderViewModel vm) => FrListener<OrderViewModel, OrderModel>(\n"
            "    listener: (context, previous, current, vm) {\n"
            "      if (previous.navigationSignal != current.navigationSignal &&\n"
            "          current.navigationSignal == OrderNavigation.confirmation) {\n"
            "        OrderDonePage().go(context);\n"
            "      }\n"
            "    },\n"
            "    child: SubmitButton(\n"
            "      onPressed: () => vm.add(const OrderSubmitted()),\n"
            "    ),\n"
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
            "    this.emit(state.copyWith(isSubmitting: true, error: null, navigationSignal: null));\n"
            "    try {\n"
            "      final request = SubmitOrderBffReq(orderId: state.orderId);\n"
            "      final response = await service.submitOrder(request);\n"
            "      this.emit(state.copyWith(confirmationId: response.confirmationId, isSubmitting: false, navigationSignal: OrderNavigation.confirmation));\n"
            "    } catch (error) {\n"
            "      this.emit(state.copyWith(error: error.toString(), isSubmitting: false));\n"
            "    }\n"
            "  }\n"
            "}\n",
            encoding="utf-8",
        )
        return component

    def add_local_navigation_flow(self, component_file: Path) -> None:
        contract = component_file.with_name("order.c.dart")
        contract.write_text(
            contract.read_text()
            .replace(
                "/// Widget Tree: [OrderView] > [SubmitButton]",
                "/// Widget Tree: [OrderView] > [SubmitButton] > [TabBar]",
            )
            .replace(
                "/// Events: [OrderStarted], [OrderSubmitted]",
                "/// Events: [OrderStarted], [OrderSubmitted], [TabSelected]",
            )
            .replace(
                "/// BFF Service: [OrderService]",
                "/// - Flow: select-tab\n"
                "/// - Trigger: widget [TabBar].select\n"
                "/// - Event: [TabSelected]\n"
                "/// - Uses: local\n"
                "/// - Guard: none\n"
                "/// - Pending State: [OrderModel].localNavigationSignal = null\n"
                "/// - Success State: [OrderModel].selectedTab = 'details'; [OrderModel].localNavigationSignal = LocalOrderNavigation.details\n"
                "/// - Failure State: none\n"
                "/// - Concurrency: not-applicable\n"
                "/// - Navigation: view-listener-on-success [OrderModel].localNavigationSignal = LocalOrderNavigation.details\n"
                "/// BFF Service: [OrderService]",
            )
            .replace(
                "    OrderNavigation? navigationSignal,",
                "    OrderNavigation? navigationSignal,\n"
                "    LocalOrderNavigation? localNavigationSignal,\n"
                "    required String selectedTab,",
            )
            .replace(
                "enum OrderNavigation { confirmation }",
                "enum OrderNavigation { confirmation }\n"
                "enum LocalOrderNavigation { details }",
            )
            .replace(
                "class OrderSubmitted {}",
                "class OrderSubmitted {}\nclass TabSelected {}",
            )
        )
        view = component_file.with_name("order.v.dart")
        view.write_text(
            view.read_text().replace(
                "    child: SubmitButton(\n"
                "      onPressed: () => vm.add(const OrderSubmitted()),\n"
                "    ),",
                "    child: FrListener<OrderViewModel, OrderModel>(\n"
                "      listener: (context, previous, current, vm) {\n"
                "        if (previous.localNavigationSignal != current.localNavigationSignal &&\n"
                "            current.localNavigationSignal == LocalOrderNavigation.details) {\n"
                "          OrderDetailsPage().push(context);\n"
                "        }\n"
                "      },\n"
                "      child: TabBar(\n"
                "        onSelected: () => vm.add(const TabSelected()),\n"
                "        child: SubmitButton(\n"
                "          onPressed: () => vm.add(const OrderSubmitted()),\n"
                "        ),\n"
                "      ),\n"
                "    ),",
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
                "    this.emit(state.copyWith(localNavigationSignal: null));\n"
                "    this.emit(state.copyWith(\n"
                "      selectedTab: 'details',\n"
                "      localNavigationSignal: LocalOrderNavigation.details,\n"
                "    ));\n"
                "  }\n"
                "  Future<void> _onStarted",
            )
        )

    def write_local_guarded_entry_fixture(self, root: Path) -> Path:
        directory = root / "lib/protected_entry"
        directory.mkdir(parents=True)
        component = directory / "protected_entry.dart"
        component.write_text(
            "part 'protected_entry.c.dart';\n"
            "part 'protected_entry.v.dart';\n"
            "part 'protected_entry.vm.dart';\n",
            encoding="utf-8",
        )
        (directory / "protected_entry.c.dart").write_text(
            "/// State Ownership: component-owned [ProtectedEntryViewModel]\n"
            "/// Public Views: [ProtectedEntryView]\n"
            "/// Widget Tree: [ProtectedEntryView] > [ProtectedEntryButton]\n"
            "/// Theme: none\n"
            "/// Events: [ProtectedEntryRequested]\n"
            "/// ViewModels: [ProtectedEntryViewModel]\n"
            "/// Models: [ProtectedEntryModel]\n"
            "/// Interactions:\n"
            "/// - Flow: request-protected-entry\n"
            "/// - Trigger: widget [ProtectedEntryButton].tap\n"
            "/// - Event: [ProtectedEntryRequested]\n"
            "/// - Uses: local\n"
            "/// - Guard: [ProtectedEntryModel].isCheckingEntry == false\n"
            "/// - Pending State: [ProtectedEntryModel].isCheckingEntry = true; [ProtectedEntryModel].entryOutcome = null; [ProtectedEntryModel].entryError = null; [ProtectedEntryModel].navigationSignal = null\n"
            "/// - Success State: [ProtectedEntryModel].isCheckingEntry = false; [ProtectedEntryModel].entryOutcome = ProtectedEntryOutcome.approved; [ProtectedEntryModel].navigationSignal = ProtectedEntryNavigation.destination\n"
            "/// - Failure State: [ProtectedEntryModel].isCheckingEntry = false; [ProtectedEntryModel].entryOutcome = ProtectedEntryOutcome.blocked; [ProtectedEntryModel].entryError = 'blocked'\n"
            "/// - Concurrency: ignore-while-active\n"
            "/// - Navigation: view-listener-on-success [ProtectedEntryModel].navigationSignal = ProtectedEntryNavigation.destination\n"
            "part of 'protected_entry.dart';\n\n"
            "class ProtectedEntryModel {\n"
            "  const factory ProtectedEntryModel({\n"
            "    required bool isCheckingEntry,\n"
            "    ProtectedEntryOutcome? entryOutcome,\n"
            "    String? entryError,\n"
            "    ProtectedEntryNavigation? navigationSignal,\n"
            "  }) = ProtectedEntryModelImpl;\n"
            "}\n"
            "enum ProtectedEntryOutcome { approved, blocked }\n"
            "enum ProtectedEntryNavigation { destination }\n"
            "class ProtectedEntryRequested {}\n",
            encoding="utf-8",
        )
        (directory / "protected_entry.v.dart").write_text(
            "part of 'protected_entry.dart';\n"
            "class ProtectedEntryView {\n"
            "  Object build(ProtectedEntryViewModel vm) => "
            "FrListener<ProtectedEntryViewModel, ProtectedEntryModel>(\n"
            "    listener: (context, previous, current, vm) {\n"
            "      if (previous.navigationSignal != current.navigationSignal &&\n"
            "          current.navigationSignal == "
            "ProtectedEntryNavigation.destination) {\n"
            "        ProtectedDestinationPage().push(context);\n"
            "      }\n"
            "    },\n"
            "    child: ProtectedEntryButton(\n"
            "      onPressed: () => vm.add(const ProtectedEntryRequested()),\n"
            "    ),\n"
            "  );\n"
            "}\n",
            encoding="utf-8",
        )
        (directory / "protected_entry.vm.dart").write_text(
            "part of 'protected_entry.dart';\n"
            "abstract class ProtectedEntryGateway {\n"
            "  Future<bool> canEnter();\n"
            "}\n"
            "class ProtectedEntryViewModel {\n"
            "  ProtectedEntryViewModel({required this.entryGateway}) {\n"
            "    on<ProtectedEntryRequested>(_onProtectedEntryRequested);\n"
            "  }\n"
            "  final ProtectedEntryGateway entryGateway;\n"
            "  ProtectedEntryModel get state => throw UnimplementedError();\n"
            "  void add(Object event) {}\n"
            "  void emit(Object state) {}\n"
            "  void on<T>(Object handler, {Object? transformer}) {}\n"
            "  Future<void> _onProtectedEntryRequested(\n"
            "    ProtectedEntryRequested event,\n"
            "    Object emit,\n"
            "  ) async {\n"
            "    if (state.isCheckingEntry) return;\n"
            "    this.emit(state.copyWith(\n"
            "      isCheckingEntry: true,\n"
            "      entryOutcome: null,\n"
            "      entryError: null,\n"
            "      navigationSignal: null,\n"
            "    ));\n"
            "    try {\n"
            "      final approved = await entryGateway.canEnter();\n"
            "      if (!approved) {\n"
            "        this.emit(state.copyWith(\n"
            "          isCheckingEntry: false,\n"
            "          entryOutcome: ProtectedEntryOutcome.blocked,\n"
            "          entryError: 'blocked',\n"
            "        ));\n"
            "        return;\n"
            "      }\n"
            "      this.emit(state.copyWith(\n"
            "        isCheckingEntry: false,\n"
            "        entryOutcome: ProtectedEntryOutcome.approved,\n"
            "        navigationSignal: ProtectedEntryNavigation.destination,\n"
            "      ));\n"
            "    } catch (error) {\n"
            "      this.emit(state.copyWith(\n"
            "        isCheckingEntry: false,\n"
            "        entryOutcome: ProtectedEntryOutcome.blocked,\n"
            "        entryError: error.toString(),\n"
            "      ));\n"
            "    }\n"
            "  }\n"
            "}\n",
            encoding="utf-8",
        )
        return component

    def test_dart_formatted_direct_emit_is_recognized(self) -> None:
        source = (
            "emit(\n"
            "  state.copyWith(\n"
            "    isCheckingEntry: true,\n"
            "    navigationSignal: null,\n"
            "  ),\n"
            ");\n"
        )

        self.assertEqual(len(_emit_arguments(source)), 1)
        self.assertEqual(
            [(field, value) for field, value, _ in _copy_with_assignments(source)],
            [("isCheckingEntry", "true"), ("navigationSignal", "null")],
        )

    def test_validates_each_endpoint_and_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            validate_api_semantics(component, contract)
            validate_runtime_integration(component, contract)

    def test_local_component_without_interactions_keeps_legacy_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            contract_file = component_file.with_name("protected_entry.c.dart")
            source = contract_file.read_text()
            interactions_start = source.index("/// Interactions:\n")
            contract_start = source.index("part of 'protected_entry.dart';")
            contract_file.write_text(
                source[:interactions_start] + source[contract_start:]
            )
            component = parse_component(component_file)

            self.assertEqual(component.interactions, ())
            validate_api_semantics(component, contract_file.read_text())
            validate_runtime_integration(component, contract_file.read_text())

    def test_local_component_with_interactions_none_keeps_legacy_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            contract_file = component_file.with_name("protected_entry.c.dart")
            source = contract_file.read_text()
            interactions_start = source.index("/// Interactions:\n")
            contract_start = source.index("part of 'protected_entry.dart';")
            contract_file.write_text(
                source[:interactions_start]
                + "/// Interactions: none\n"
                + source[contract_start:]
            )
            component = parse_component(component_file)

            self.assertEqual(component.interactions, ())
            validate_api_semantics(component, contract_file.read_text())
            validate_runtime_integration(component, contract_file.read_text())

    def test_api_less_local_guarded_entry_flow_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            component = parse_component(component_file)
            contract = component_file.with_name("protected_entry.c.dart").read_text()

            self.assertEqual(component.endpoints, ())
            self.assertEqual(component.interactions[0].uses, "local")
            validate_api_semantics(component, contract)
            validate_runtime_integration(component, contract)

    def test_bff_api_less_structured_local_guarded_entry_flow_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            contract_file = component_file.with_name("protected_entry.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "/// Interactions:\n",
                    "/// BFF-UI-API:\n/// -\n/// Interactions:\n",
                )
            )
            component = parse_component(component_file)
            contract = contract_file.read_text()

            self.assertEqual(component.endpoints, ())
            self.assertEqual(component.sections["BFF-UI-API"], ["-"])
            self.assertEqual(component.interactions[0].uses, "local")
            validate_api_semantics(component, contract)
            validate_runtime_integration(component, contract)

    def test_local_guarded_entry_vm_must_not_call_typed_page_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            vm = component_file.with_name("protected_entry.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "      final approved = await entryGateway.canEnter();",
                    "      final approved = await entryGateway.canEnter();\n"
                    "      ProtectedDestinationPage().go(context);",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("protected_entry.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "must not call router navigation"):
                validate_runtime_integration(component, contract)

    def test_local_guarded_entry_requires_view_listener(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            view = component_file.with_name("protected_entry.v.dart")
            view.write_text(view.read_text().replace("FrListener<", "UnrelatedListener<"))
            component = parse_component(component_file)
            contract = component_file.with_name("protected_entry.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "FrListener/FrConsumer"):
                validate_runtime_integration(component, contract)

    def test_local_guarded_entry_pending_must_clear_navigation_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            contract_file = component_file.with_name("protected_entry.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "; [ProtectedEntryModel].navigationSignal = null\n", "\n"
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(ContractError, "Pending State must reset"):
                validate_api_semantics(component, contract_file.read_text())

    def test_local_guarded_entry_failure_must_not_set_navigation_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            contract_file = component_file.with_name("protected_entry.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "[ProtectedEntryModel].entryError = 'blocked'\n",
                    "[ProtectedEntryModel].entryError = 'blocked'; "
                    "[ProtectedEntryModel].navigationSignal = "
                    "ProtectedEntryNavigation.destination\n",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(ContractError, "Failure State must not write"):
                validate_api_semantics(component, contract_file.read_text())

    def test_local_guarded_entry_failure_requires_observable_blocked_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            contract_file = component_file.with_name("protected_entry.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "/// - Failure State: [ProtectedEntryModel].isCheckingEntry = false; "
                    "[ProtectedEntryModel].entryOutcome = "
                    "ProtectedEntryOutcome.blocked; "
                    "[ProtectedEntryModel].entryError = 'blocked'\n",
                    "/// - Failure State: "
                    "[ProtectedEntryModel].isCheckingEntry = false\n",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(
                ContractError, "observable blocked/error outcome"
            ):
                validate_api_semantics(component, contract_file.read_text())

    def test_local_guarded_entry_failure_rejects_unrelated_observable_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            contract_file = component_file.with_name("protected_entry.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "/// - Failure State: [ProtectedEntryModel].isCheckingEntry = false; "
                    "[ProtectedEntryModel].entryOutcome = "
                    "ProtectedEntryOutcome.blocked; "
                    "[ProtectedEntryModel].entryError = 'blocked'\n",
                    "/// - Failure State: "
                    "[ProtectedEntryModel].isCheckingEntry = false; "
                    "[ProtectedEntryModel].entryOutcome = "
                    "ProtectedEntryOutcome.approved\n",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(
                ContractError, "observable blocked/error outcome"
            ):
                validate_api_semantics(component, contract_file.read_text())

    def test_local_guarded_entry_blocked_runtime_must_not_set_navigation_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            vm = component_file.with_name("protected_entry.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "          entryError: 'blocked',\n"
                    "        ));\n"
                    "        return;",
                    "          entryError: 'blocked',\n"
                    "          navigationSignal: "
                    "ProtectedEntryNavigation.destination,\n"
                    "        ));\n"
                    "        return;",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("protected_entry.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "direct Pending null then Success"):
                validate_runtime_integration(component, contract)

    def test_local_guarded_entry_pending_signal_must_share_atomic_emit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            vm = component_file.with_name("protected_entry.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "      entryError: null,\n"
                    "      navigationSignal: null,\n"
                    "    ));",
                    "      entryError: null,\n"
                    "    ));\n"
                    "    this.emit(state.copyWith(navigationSignal: null));",
                    1,
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("protected_entry.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "all declared Pending State writes together"
            ):
                validate_runtime_integration(component, contract)

    def test_local_guarded_entry_premature_signal_before_approved_emit_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            vm = component_file.with_name("protected_entry.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "    try {\n",
                    "    this.emit(state.copyWith(\n"
                    "      navigationSignal: "
                    "ProtectedEntryNavigation.destination,\n"
                    "    ));\n"
                    "    try {\n",
                    1,
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("protected_entry.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "direct Pending null then Success"
            ):
                validate_runtime_integration(component, contract)

    def test_local_guarded_entry_success_signal_must_share_approved_emit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            vm = component_file.with_name("protected_entry.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "      this.emit(state.copyWith(\n"
                    "        isCheckingEntry: false,\n"
                    "        entryOutcome: ProtectedEntryOutcome.approved,\n"
                    "        navigationSignal: "
                    "ProtectedEntryNavigation.destination,\n"
                    "      ));",
                    "      this.emit(state.copyWith(\n"
                    "        isCheckingEntry: false,\n"
                    "        entryOutcome: ProtectedEntryOutcome.approved,\n"
                    "      ));\n"
                    "      this.emit(state.copyWith(\n"
                    "        navigationSignal: "
                    "ProtectedEntryNavigation.destination,\n"
                    "      ));",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("protected_entry.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "all declared Success State writes together"
            ):
                validate_runtime_integration(component, contract)

    def test_local_guarded_async_entry_requires_preflight_await(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            vm = component_file.with_name("protected_entry.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "      final approved = await entryGateway.canEnter();",
                    "      final approved = true;",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("protected_entry.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "must await preflight"):
                validate_runtime_integration(component, contract)

    def test_local_guarded_async_blocked_emit_must_return_before_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            vm = component_file.with_name("protected_entry.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "        ));\n"
                    "        return;\n"
                    "      }\n"
                    "      this.emit(state.copyWith(\n"
                    "        isCheckingEntry: false,\n"
                    "        entryOutcome: ProtectedEntryOutcome.approved,",
                    "        ));\n"
                    "      }\n"
                    "      this.emit(state.copyWith(\n"
                    "        isCheckingEntry: false,\n"
                    "        entryOutcome: ProtectedEntryOutcome.approved,",
                    1,
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("protected_entry.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "emit a blocked Failure State and return"
            ):
                validate_runtime_integration(component, contract)

    def test_local_guarded_entry_success_requires_real_approved_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            contract_file = component_file.with_name("protected_entry.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "; [ProtectedEntryModel].entryOutcome = "
                    "ProtectedEntryOutcome.approved",
                    "",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(
                ContractError, "non-navigation Success State decision"
            ):
                validate_api_semantics(component, contract_file.read_text())

    def test_local_guarded_entry_null_outcome_is_not_approved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            contract_file = component_file.with_name("protected_entry.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "[ProtectedEntryModel].entryOutcome = "
                    "ProtectedEntryOutcome.approved",
                    "[ProtectedEntryModel].entryOutcome = null",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(
                ContractError, "non-navigation Success State decision"
            ):
                validate_api_semantics(component, contract_file.read_text())

    def test_local_guarded_entry_error_clear_is_not_an_approved_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            contract_file = component_file.with_name("protected_entry.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "[ProtectedEntryModel].entryOutcome = "
                    "ProtectedEntryOutcome.approved",
                    "[ProtectedEntryModel].entryError = null",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(
                ContractError, "non-navigation Success State decision"
            ):
                validate_api_semantics(component, contract_file.read_text())

    def test_local_guarded_entry_event_must_dispatch_from_target_widget(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            view = component_file.with_name("protected_entry.v.dart")
            view.write_text(
                view.read_text().replace(
                    "onPressed: () => vm.add(const ProtectedEntryRequested()),",
                    "onPressed: () {},",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("protected_entry.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "request-protected-entry.*ProtectedEntryButton"
            ):
                validate_runtime_integration(component, contract)

    def test_local_contract_interactions_may_use_only_local(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_local_guarded_entry_fixture(Path(temporary))
            contract_file = component_file.with_name("protected_entry.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "/// - Uses: local",
                    "/// - Uses: ui-api [MissingRequest]",
                )
            )

            with self.assertRaisesRegex(ContractError, "unknown endpoint identity"):
                parse_component(component_file)

    def test_navigation_signal_requires_nullable_semantic_enum(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            contract_file = component_file.with_name("order.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "OrderNavigation? navigationSignal",
                    "OrderNavigation navigationSignal",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(
                ContractError, "nullable semantic enum type `OrderNavigation\\?`"
            ):
                validate_api_semantics(component, contract_file.read_text())

    def test_navigation_enum_accepts_doc_comments_and_json_value_annotation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            contract_file = component_file.with_name("order.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "enum OrderNavigation { confirmation }",
                    "enum OrderNavigation {\n"
                    "  /// Navigate after the confirmed business result.\n"
                    "  @JsonValue('confirmation')\n"
                    "  confirmation,\n"
                    "}",
                )
            )
            component = parse_component(component_file)

            validate_api_semantics(component, contract_file.read_text())

    def test_navigation_enum_ignores_members_named_only_in_comments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            contract_file = component_file.with_name("order.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "enum OrderNavigation { confirmation }",
                    "enum OrderNavigation {\n"
                    "  // confirmation,\n"
                    "  unrelated,\n"
                    "}",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(
                ContractError, "undeclared enum member OrderNavigation.confirmation"
            ):
                validate_api_semantics(component, contract_file.read_text())

    def test_navigation_enum_rejects_comment_or_string_only_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            contract_file = component_file.with_name("order.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "enum OrderNavigation { confirmation }",
                    "// enum OrderNavigation { confirmation }\n"
                    "const enumExample = 'enum OrderNavigation { confirmation }';",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(
                ContractError, "undeclared enum member OrderNavigation.confirmation"
            ):
                validate_api_semantics(component, contract_file.read_text())

    def test_navigation_signal_resets_in_pending_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            contract_file = component_file.with_name("order.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "; [OrderModel].navigationSignal = null\n",
                    "\n",
                    1,
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(
                ContractError, "Pending State must reset.*navigationSignal = null"
            ):
                validate_api_semantics(component, contract_file.read_text())

    def test_view_listener_must_handle_the_exact_enum_member(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            view = component_file.with_name("order.v.dart")
            view.write_text(
                view.read_text().replace(
                    "current.navigationSignal == OrderNavigation.confirmation",
                    "current.navigationSignal != null",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "FrListener/FrConsumer.*exact enum member"
            ):
                validate_runtime_integration(component, contract)

    def test_view_listener_rejects_or_null_member_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            view = component_file.with_name("order.v.dart")
            view.write_text(
                view.read_text().replace(
                    "current.navigationSignal == OrderNavigation.confirmation",
                    "(current.navigationSignal == OrderNavigation.confirmation || "
                    "current.navigationSignal == null)",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "exact enum member"):
                validate_runtime_integration(component, contract)

    def test_view_listener_must_compare_previous_and_current(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            view = component_file.with_name("order.v.dart")
            view.write_text(
                view.read_text().replace(
                    "previous.navigationSignal != current.navigationSignal &&\n"
                    "          ",
                    "",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "compares previous/current"
            ):
                validate_runtime_integration(component, contract)

    def test_view_listener_rejects_previous_equals_current_as_transition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            view = component_file.with_name("order.v.dart")
            view.write_text(
                view.read_text().replace(
                    "previous.navigationSignal != current.navigationSignal",
                    "previous.navigationSignal == current.navigationSignal",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "equality early-return"):
                validate_runtime_integration(component, contract)

    def test_view_listener_accepts_equality_early_return_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            view = component_file.with_name("order.v.dart")
            view.write_text(
                view.read_text().replace(
                    "      if (previous.navigationSignal != current.navigationSignal &&\n"
                    "          current.navigationSignal == OrderNavigation.confirmation) {",
                    "      if (previous.navigationSignal == current.navigationSignal) {\n"
                    "        return;\n"
                    "      }\n"
                    "      if (current.navigationSignal == OrderNavigation.confirmation) {",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            validate_runtime_integration(component, contract)

    def test_view_listener_accepts_member_inside_exact_transition_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            view = component_file.with_name("order.v.dart")
            view.write_text(
                view.read_text().replace(
                    "      if (previous.navigationSignal != current.navigationSignal &&\n"
                    "          current.navigationSignal == OrderNavigation.confirmation) {\n"
                    "        OrderDonePage().go(context);\n"
                    "      }",
                    "      if ((previous.navigationSignal != "
                    "current.navigationSignal)) {\n"
                    "        if ((current.navigationSignal == "
                    "OrderNavigation.confirmation)) {\n"
                    "          OrderDonePage().go(context);\n"
                    "        }\n"
                    "      }",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            validate_runtime_integration(component, contract)

    def test_view_listener_requires_the_exact_generic_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            view = component_file.with_name("order.v.dart")
            view.write_text(
                view.read_text().replace(
                    "FrListener<OrderViewModel, OrderModel>",
                    "FrListener<OrderViewModel, UnrelatedModel>",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "FrListener/FrConsumer<OrderViewModel, OrderModel>"
            ):
                validate_runtime_integration(component, contract)

    def test_view_listener_rejects_navigation_from_an_unrelated_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            view = component_file.with_name("order.v.dart")
            view.write_text(
                view.read_text().replace(
                    "      if (previous.navigationSignal != current.navigationSignal &&\n"
                    "          current.navigationSignal == OrderNavigation.confirmation) {\n"
                    "        OrderDonePage().go(context);\n"
                    "      }",
                    "      if (previous.navigationSignal != current.navigationSignal &&\n"
                    "          current.navigationSignal == OrderNavigation.confirmation) {\n"
                    "        final handled = true;\n"
                    "      }\n"
                    "      if (current.isLoading) {\n"
                    "        OrderDonePage().go(context);\n"
                    "      }",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "exact enum member"):
                validate_runtime_integration(component, contract)

    def test_navigation_signal_is_not_emitted_from_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "      this.emit(state.copyWith(confirmationId: response.confirmationId, isSubmitting: false, navigationSignal: OrderNavigation.confirmation));\n"
                    "    } catch (error) {\n"
                    "      this.emit(state.copyWith(error: error.toString(), isSubmitting: false));",
                    "      this.emit(state.copyWith(confirmationId: response.confirmationId, isSubmitting: false, navigationSignal: OrderNavigation.confirmation));\n"
                    "    } catch (error) {\n"
                    "      this.emit(state.copyWith(error: error.toString(), isSubmitting: false, navigationSignal: OrderNavigation.confirmation));",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "Navigation signal.*only after success"
            ):
                validate_runtime_integration(component, contract)

    def test_query_contract_must_not_write_another_flows_navigation_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            contract_file = component_file.with_name("order.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "[OrderModel].orderId <- [LoadOrderBffRsp].orderId; "
                    "[OrderModel].isLoading = false",
                    "[OrderModel].orderId <- [LoadOrderBffRsp].orderId; "
                    "[OrderModel].isLoading = false; "
                    "[OrderModel].navigationSignal = "
                    "OrderNavigation.confirmation",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(
                ContractError, "load-order.*must not write navigation signal"
            ):
                validate_api_semantics(component, contract_file.read_text())

    def test_query_flow_must_not_write_another_flows_navigation_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "orderId: response.orderId, isLoading: false",
                    "orderId: response.orderId, isLoading: false, "
                    "navigationSignal: OrderNavigation.confirmation",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "outside owning Flow `submit-order` handler"
            ):
                validate_runtime_integration(component, contract)

    def test_undeclared_handler_must_not_write_navigation_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "  Future<void> _onStarted",
                    "  void injectNavigation() {\n"
                    "    emit(state.copyWith(\n"
                    "      navigationSignal: OrderNavigation.confirmation,\n"
                    "    ));\n"
                    "  }\n"
                    "  Future<void> _onStarted",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "outside owning Flow `submit-order` handler"
            ):
                validate_runtime_integration(component, contract)

    def test_indirect_navigation_signal_assignment_outside_owner_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "      this.emit(state.copyWith(orderId: response.orderId, isLoading: false));",
                    "      final next = state.copyWith(\n"
                    "        orderId: response.orderId,\n"
                    "        isLoading: false,\n"
                    "        navigationSignal: OrderNavigation.confirmation,\n"
                    "      );\n"
                    "      this.emit(next);",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "outside owning Flow `submit-order` handler"
            ):
                validate_runtime_integration(component, contract)

    def test_navigation_signal_is_not_written_after_catch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "      this.emit(state.copyWith(error: error.toString(), isSubmitting: false));\n"
                    "    }\n"
                    "  }\n"
                    "}",
                    "      this.emit(state.copyWith(error: error.toString(), isSubmitting: false));\n"
                    "    }\n"
                    "    this.emit(state.copyWith(navigationSignal: OrderNavigation.confirmation));\n"
                    "  }\n"
                    "}",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "post-catch writes"):
                validate_runtime_integration(component, contract)

    def test_view_model_must_not_own_build_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "  final OrderService service;",
                    "  final OrderService service;\n  final BuildContext context;",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(
                ContractError, "ViewModel must not own BuildContext"
            ):
                validate_runtime_integration(component, contract)

    def test_view_model_rejects_navigator_state_and_push_named(self) -> None:
        replacements = (
            (
                "  final OrderService service;",
                "  final OrderService service;\n  NavigatorState? navigatorState;",
            ),
            (
                "  Future<void> _onStarted",
                "  void openRoute() { navigator.pushNamed('/orders'); }\n"
                "  Future<void> _onStarted",
            ),
        )
        for old, new in replacements:
            with self.subTest(new=new):
                with tempfile.TemporaryDirectory() as temporary:
                    component_file = self.write_fixture(Path(temporary))
                    vm = component_file.with_name("order.vm.dart")
                    vm.write_text(vm.read_text().replace(old, new))
                    component = parse_component(component_file)
                    contract = component_file.with_name("order.c.dart").read_text()

                    with self.assertRaisesRegex(
                        ContractError,
                        "ViewModel must not (?:own BuildContext or router types|call router navigation)",
                    ):
                        validate_runtime_integration(component, contract)

    def test_api_less_view_model_still_enforces_routing_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component_file = root / "local.dart"
            contract_file = root / "local.c.dart"
            vm_file = root / "local.vm.dart"
            component_file.write_text("part 'local.vm.dart';\n")
            contract_file.write_text("/// BFF-UI-API:\n/// -\n")
            vm_file.write_text(
                "part of 'local.dart';\n"
                "class LocalViewModel {\n"
                "  NavigatorState? navigator;\n"
                "}\n"
            )
            component = SimpleNamespace(
                component_file=str(component_file),
                contract_file=str(contract_file),
                sections={"BFF-UI-API": ["-"]},
                view_models=["LocalViewModel"],
                interactions=(),
            )

            with self.assertRaisesRegex(ContractError, "router types"):
                validate_runtime_integration(component, contract_file.read_text())

    def test_api_less_state_ownership_none_does_not_require_a_view_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            component_file = root / "local.dart"
            contract_file = root / "local.c.dart"
            component_file.write_text("part 'local.c.dart';\n")
            contract_file.write_text("/// BFF-UI-API:\n/// -\n")
            component = SimpleNamespace(
                component_file=str(component_file),
                contract_file=str(contract_file),
                sections={"BFF-UI-API": ["-"]},
                view_models=[],
                interactions=(),
            )

            validate_runtime_integration(component, contract_file.read_text())

    def test_router_words_inside_a_string_literal_do_not_fail_vm_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "class OrderViewModel {",
                    "class OrderViewModel {\n"
                    "  static const routingExample = "
                    "'NavigatorState navigator; navigator.pushNamed(\\'/orders\\');';",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            validate_runtime_integration(component, contract)

    def test_executable_string_interpolation_does_not_hide_vm_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "class OrderViewModel {",
                    "class OrderViewModel {\n"
                    "  String debugRoute() => \"${appRouter.go('/orders')}\";",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "call router navigation"):
                validate_runtime_integration(component, contract)

    def test_arbitrary_app_router_go_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "  Future<void> _onStarted",
                    "  void openRoute() { appRouter.go('/orders'); }\n"
                    "  Future<void> _onStarted",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            with self.assertRaisesRegex(ContractError, "call router navigation"):
                validate_runtime_integration(component, contract)

    def test_app_router_go_inside_inert_string_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "class OrderViewModel {",
                    "class OrderViewModel {\n"
                    "  static const routingExample = "
                    "\"appRouter.go('/orders');\";",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            validate_runtime_integration(component, contract)

    def test_ambiguous_domain_push_pop_replace_calls_remain_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "  Future<void> _onStarted",
                    "  void updateDomain() {\n"
                    "    cart.push(item);\n"
                    "    stack.pop();\n"
                    "    repository.replace(value);\n"
                    "  }\n"
                    "  Future<void> _onStarted",
                )
            )
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

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
                    "    this.emit(state.copyWith(isSubmitting: true, error: null, navigationSignal: null));",
                    "    // this.emit(state.copyWith(isSubmitting: true, error: null, navigationSignal: null));",
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

            with self.assertRaisesRegex(
                ContractError, "ViewModel must not call router navigation"
            ):
                validate_runtime_integration(component, contract)

    def test_local_business_flow_may_emit_view_listener_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            self.add_local_navigation_flow(component_file)
            component = parse_component(component_file)
            contract = component_file.with_name("order.c.dart").read_text()

            validate_api_semantics(component, contract)
            validate_runtime_integration(component, contract)

    def test_local_presentation_only_navigation_signal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            self.add_local_navigation_flow(component_file)
            contract_file = component_file.with_name("order.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "/// - Success State: [OrderModel].selectedTab = 'details'; "
                    "[OrderModel].localNavigationSignal = "
                    "LocalOrderNavigation.details",
                    "/// - Success State: [OrderModel].localNavigationSignal = "
                    "LocalOrderNavigation.details",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(
                ContractError, "non-navigation Success State decision"
            ):
                validate_api_semantics(component, contract_file.read_text())

    def test_local_navigation_rejects_obvious_self_assignment_business_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            self.add_local_navigation_flow(component_file)
            contract_file = component_file.with_name("order.c.dart")
            contract_file.write_text(
                contract_file.read_text().replace(
                    "/// - Success State: [OrderModel].selectedTab = 'details'; "
                    "[OrderModel].localNavigationSignal = "
                    "LocalOrderNavigation.details",
                    "/// - Success State: [OrderModel].selectedTab = state.selectedTab; "
                    "[OrderModel].localNavigationSignal = "
                    "LocalOrderNavigation.details",
                )
            )
            component = parse_component(component_file)

            with self.assertRaisesRegex(ContractError, "no-op self-assignment"):
                validate_api_semantics(component, contract_file.read_text())

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

            with self.assertRaisesRegex(
                ContractError, "ViewModel must not call router navigation"
            ):
                validate_runtime_integration(component, contract)

    def test_guard_must_run_before_pending_state_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            component_file = self.write_fixture(Path(temporary))
            vm = component_file.with_name("order.vm.dart")
            vm.write_text(
                vm.read_text().replace(
                    "    if (state.isSubmitting) return;\n"
                    "    this.emit(state.copyWith(isSubmitting: true, error: null, navigationSignal: null));",
                    "    this.emit(state.copyWith(isSubmitting: true, error: null, navigationSignal: null));\n"
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
                    "      this.emit(state.copyWith(confirmationId: response.confirmationId, isSubmitting: false, navigationSignal: OrderNavigation.confirmation));",
                    "      this.emit((confirmationId: response.confirmationId,));\n"
                    "      this.emit(state.copyWith(confirmationId: 'wrong', isSubmitting: false, navigationSignal: OrderNavigation.confirmation));",
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

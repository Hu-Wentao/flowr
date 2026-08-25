# Frontend Interaction Contracts

Use `Interactions:` in every BFF v9 component contract. Keep `.c.dart` as the
source of truth; treat the generated `### 前端交互逻辑` Markdown as a review
projection.

`Interactions:` documents only ViewModel-owned Flows. Do not add an Event or
Flow merely because a Widget has a callback.

## View and ViewModel authority

Classify authority before writing Events:

- Keep an operation in the View callback when it needs `BuildContext`, a Widget
  controller, overlay ownership, or platform presentation and does not change
  durable/business/API state.
- Use a Bloc Event and an Interaction Flow when the ViewModel owns model
  changes, API or service work, business decisions, validation, guard or
  concurrency policy, retry/recovery, or an outcome that other consumers must
  observe as state.
- Do not generate Intent or callback-output protocols as a second state
  channel. Ordinary reusable Widgets may still accept input callbacks.

Normally View-local operations include, but are not limited to:

- navigation to a known typed Page from a View callback;
- opening or closing a dialog, sheet, menu, tooltip, or local overlay;
- focus, keyboard, scroll, selection-controller, animation, and other
  Widget-lifecycle work;
- transient visual feedback that does not become model or business state.

This list is intentionally non-exhaustive. Do not add exhaustive operation
syntax validation; decide from authority and state ownership.

Platform picker, URL launch, share, and clipboard operations are boundary
cases. Keep the direct platform invocation in the View when it is a
presentation-only action over already-approved data. Put the decision and
result in the ViewModel when permissions, validation, persistence, API work,
business policy, retry, or model changes are involved; inject a platform
service where deterministic testing or lifecycle isolation requires it. The
View still owns `BuildContext` and router calls.

A known typed Page destination invoked directly by a View callback normally
needs no Event and no Interaction Flow:

```dart
SubmitButton(
  onPressed: () => OrderDetailsPage(orderId: orderId).push(context),
)
```

## Endpoint identity

Identify each UI endpoint by its request boundary type. Require one
`Behaviors:` record and one `Request Field Sources:` record per endpoint:

```dart
/// BFF-UI-API:
/// GET /orders/:orderId
/// [LoadOrderBffReq], [LoadOrderBffRsp]
/// POST /orders/:orderId/submit
/// [SubmitOrderBffReq], [SubmitOrderBffRsp]
/// Behaviors:
/// - Endpoint: [LoadOrderBffReq]
/// - UI Data: order details and available actions
/// - Source: approved order UI requirements
/// - Loading/Refresh: load on entry and retain data while refreshing
/// - Empty/Error: missing order is empty; failure supports retry
/// - Endpoint: [SubmitOrderBffReq]
/// - Effect: submit the approved order
/// - Success: confirmationId proves submission
/// - Failure: rejected -> restore submit state and show reason
/// - Navigation: app
/// Request Field Sources:
/// - Endpoint: [LoadOrderBffReq]
/// - orderId <- OrderPage.orderId | selects the order
/// - Endpoint: [SubmitOrderBffReq]
/// - orderId <- OrderModel.orderId | selects the order
```

Keep request boundary types unique within the component. Do not identify an
endpoint by repeating its method/path in Behavior, provenance, or interaction
records.

## Interaction grammar

Declare one fixed record per ViewModel-owned frontend Flow:

```dart
/// Interactions:
/// - Flow: submit-order
/// - Trigger: widget [SubmitButton].tap
/// - Event: [OrderSubmitted]
/// - Uses: ui-api [SubmitOrderBffReq]
/// - Guard: [OrderModel].isSubmitting == false
/// - Pending State: [OrderModel].isSubmitting = true; [OrderModel].error = null; [OrderModel].navigationSignal = null
/// - Success State: [OrderModel].confirmationId <- [SubmitOrderBffRsp].confirmationId; [OrderModel].isSubmitting = false; [OrderModel].navigationSignal = OrderNavigation.confirmation
/// - Failure State: [OrderModel].error <- error; [OrderModel].isSubmitting = false
/// - Concurrency: ignore-while-active
/// - Navigation: view-listener-on-success [OrderModel].navigationSignal = OrderNavigation.confirmation
```

Use these fields exactly:

- `Flow`: use a unique kebab-case identity.
- `Trigger`: use `startup`, `reactivation`, `widget [Widget].action`, or
  `external stable-id`. Supported Widget actions are `tap`, `change`,
  `submit`, `refresh`, `retry`, `select`, and `dismiss`.
- `Event`: reference exactly one Event declared under `Events:`. Do not reuse
  one Event across multiple Flows.
- `Uses`: use `ui-api [XxxBffReq]` or `local`.
- `Guard`: use `none` or `[XxxModel].field == true|false`.
- `Pending State`, `Success State`, and `Failure State`: separate writes with
  semicolons. Use `[XxxModel].field = value` for assignments and
  `[XxxModel].field <- [XxxBffRsp].field` or
  `[XxxModel].field <- error` for mappings. Use `none` only when that phase has
  no state write.
- `Concurrency`: use `ignore-while-active`, `latest-wins`, `queue`,
  `allow-parallel`, or `not-applicable`. Do not use `not-applicable` for a UI
  API Flow.
- `Navigation`: use `none` or exactly
  `view-listener-on-success [XxxModel].field = XxxNavigation.member`.

Require every UI endpoint to be used by at least one Flow because endpoint
execution is ViewModel-owned. Permit additional `Uses: local` Flows only when
the ViewModel owns their state or business effect. Such a Flow may use
`view-listener-on-success` only when Success also writes a real non-navigation
business/state outcome. An obvious self-assignment such as
`[Model].field = state.field` is a no-op and does not satisfy this gate. Treat
subtler semantic equivalence as review guidance rather than claiming complete
static proof. Do not document View-local callbacks or direct presentation
routing as local Flows.

For `BFF-UI-API: -`, declare `Interactions: none` when no ViewModel-owned Flow
exists, or declare structured Flows whose `Uses` value is `local`. Never attach
a UI endpoint to an API-less contract.

## Business-result navigation

Use `Navigation: none` when the Flow does not navigate.

When a command Behavior declares `Navigation: app`, or a `Uses: local` Flow
owns a genuine business/state decision that leads to navigation, use the
`view-listener-on-success` form. Declare the named Model field as the exact
nullable semantic enum type and declare the enum in the component contract.
Documented and annotated enum values are valid, including `///` comments and
metadata such as `@JsonValue(...)`:

```dart
enum OrderNavigation { confirmation }

@FrState
class OrderModel with _$OrderModel {
  const factory OrderModel({
    OrderNavigation? navigationSignal,
    // Other state fields.
  }) = _OrderModel;
}
```

The Flow must:

- own its signal field exclusively; scan executable `field:` named assignments
  throughout the ViewModel, and reject every occurrence outside the owning
  handler;
- reset the signal to `null` in Pending State;
- set the exact declared enum member only in Success State, after the API
  response when an API is used;
- avoid writing the signal in Failure State or after catch;
- continue mapping at least one business response field into frontend state for
  an API Flow, or write a separate non-navigation Success State outcome for a
  local Flow.

The ViewModel must not own `BuildContext`, `GoRouter`, `Navigator`,
`NavigatorState`, `RouterConfig`, `RouterDelegate`,
`RouteInformationParser`, typed Page calls, or common navigator/router calls.
Apply this boundary to every BFF component that declares a ViewModel, even for
an API-less component with `Interactions: none`; `State Ownership: none`
requires no ViewModel and therefore no VM file. Mask comments and inert string
content while keeping executable `${...}` interpolation code visible. Scan
distinctive router methods such as `go`, `goNamed`, `pushNamed*`,
`pushReplacement*`, `replaceNamed`, `maybePop`, and `popUntil` on arbitrary
receivers. Do not broadly classify ambiguous `push`, `pop`, or `replace` calls
on arbitrary domain objects as routing.

The View uses `FrListener` or `FrConsumer` with the exact ViewModel and Model
generic types. Accept only one of these exact braced shapes, allowing
parentheses and whitespace: an exact enum-member condition nested in an exact
`previous.field != current.field` parent; an exact enum-member condition after
an exact equality early-return guard; or one condition containing exactly the
transition comparison and exact member comparison joined by `&&` in either
order. Reject `||`, null fallbacks, other members, and additional predicates.
The accepted enum-member branch body performs typed or approved router
navigation:

```dart
FrListener<OrderViewModel, OrderModel>(
  listener: (context, previous, current, vm) {
    if (previous.navigationSignal != current.navigationSignal &&
        current.navigationSignal == OrderNavigation.confirmation) {
      OrderConfirmationPage(orderId: current.orderId).go(context);
    }
  },
  child: const OrderBody(),
)
```

Do not use a backend `nextRoute`, raw internal URI, or `BuildContext` in the
ViewModel as a substitute for the semantic enum signal. Read
`typed-routing.md` for target Page construction and exceptional external URI
boundaries.

`Navigation: app-on-success` is legacy and invalid. Migrate it by declaring a
nullable semantic enum signal, resetting it in Pending State, setting the exact
member in Success State, and moving navigation to a View
`FrListener`/`FrConsumer`.

## Ownership boundary

Use interactions only for ViewModel coordination:

```text
Trigger -> Bloc Event -> guard/concurrency -> request or VM-owned local action
        -> pending/success/failure state -> optional semantic navigation signal
```

Do not put these facts in `Interactions:`:

- View-local typed Page navigation, overlays, focus, controllers, or other
  Widget-lifecycle work;
- backend SDK methods, OpenAPI call ids, or backend call order;
- duplicated HTTP method/path or DTO field definitions;
- business success/failure meaning already owned by `Behaviors:`;
- request field provenance already owned by `Request Field Sources:`;
- complete Widget hierarchy already stored in the local Figma workspace.

## Contract validation

Before derivation, require:

- exactly one complete query or command Behavior per endpoint;
- exactly one provenance record per endpoint;
- complete Flow coverage for every endpoint;
- Event, Model, field, enum, enum-member, and response-field references to
  resolve during contract validation;
- trigger Widgets and inline Event dispatch to resolve from `.v.dart` during
  final validation;
- `startup` to use the declared `Startup Event`;
- query Flows to use `Navigation: none` and `Concurrency: latest-wins`;
- command Flow navigation to agree with its endpoint Behavior;
- app-navigation Flows to use one exclusively owned nullable semantic enum
  signal, Pending `null` reset, exact Success member, and no Failure write;
- local navigation Flows to own a separate non-navigation Success State
  decision and reject obvious `field = state.field` no-ops; presentation-only
  routing remains no Flow, while subtler semantic equivalence remains a review
  concern;
- `ignore-while-active` to guard one boolean field, activate it in Pending
  State, and reset it in both Success and Failure State;
- response mappings to use that Flow's declared response type;
- response fields not to appear in Pending State;
- `error` mappings to appear only in Failure State.

## Final runtime validation

Prove every ViewModel-owned Flow independently:

- register its exact Event once with a named `on<Event>` handler;
- dispatch Widget-triggered Events inline from the declared Widget/action
  callback through the conventional `vm`, `viewModel`, or `bloc` receiver, or a
  typed `context.read/watch<XxxViewModel>()`;
- implement its boolean guard as the handler's first executable statement,
  using the inverse condition with an immediate early return;
- prove `ignore-while-active` through its early-return guard and active/reset
  state writes; map `latest-wins`, `queue`, and `allow-parallel` to
  `restartable()`, `sequential()`, and `concurrent()` respectively;
- construct and pass the Flow's request to the matching Service operation;
- await and retain the matching response;
- emit all declared Pending, Success, and Failure state fields through
  `emit(state.copyWith(...))` in the correct regions, with every mapped source
  assigned to its exact target inside that `copyWith` call;
- read declared response fields in the success region;
- keep BuildContext and router calls out of the ViewModel;
- for `view-listener-on-success`, scan every executable signal `field:` named
  assignment, reject occurrences outside the owning handler, require only one
  direct Pending `null` assignment before an API await and one direct exact
  member assignment in Success, then prove one of the three exact listener
  branch shapes above;
- apply the masked ViewModel routing boundary even when the BFF component has a
  ViewModel but declares `Interactions: none`.

Treat a missing second or later Flow as a validation failure even when another
handler integrates successfully.

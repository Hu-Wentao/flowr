# Frontend Interaction Contracts

Use `Interactions:` in every BFF v9 component contract. Keep `.c.dart` as the
source of truth; treat the generated `### 前端交互逻辑` Markdown as a review
projection.

## Endpoint identity

Identify each UI endpoint by its request boundary type. Require one
`Behaviors:` record and one `Request Field Sources:` record per endpoint:

```dart
/// BFF-API:
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

Declare one fixed record per frontend Flow:

```dart
/// Interactions:
/// - Flow: submit-order
/// - Trigger: widget [SubmitButton].tap
/// - Event: [OrderSubmitted]
/// - Uses: ui-api [SubmitOrderBffReq]
/// - Guard: [OrderModel].isSubmitting == false
/// - Pending State: [OrderModel].isSubmitting = true; [OrderModel].error = null
/// - Success State: [OrderModel].confirmationId <- [SubmitOrderBffRsp].confirmationId; [OrderModel].isSubmitting = false
/// - Failure State: [OrderModel].error <- error; [OrderModel].isSubmitting = false
/// - Concurrency: ignore-while-active
/// - Navigation: app-on-success
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
- `Navigation`: use `none` or `app-on-success`.

Require every UI endpoint to be used by at least one Flow. Permit additional
local Flows for tab selection, form editing, disclosure, or other frontend-only
state changes.

For `BFF-API: -`, declare `Interactions: none` when no interaction state is
owned, or declare structured Flows whose `Uses` value is `local`. Never attach
a UI endpoint to an API-less contract.

## Ownership boundary

Use interactions only for frontend coordination:

```text
Trigger -> Bloc Event -> guard/concurrency -> request or local action
        -> pending/success/failure state -> optional success navigation
```

Do not put these facts in `Interactions:`:

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
- Event, Model, field, and response-field references to resolve during contract validation;
- trigger Widgets and inline Event dispatch to resolve from `.v.dart` during final validation;
- `startup` to use the declared `Startup Event`;
- query Flows to use `Navigation: none` and `Concurrency: latest-wins`;
- command Flow navigation to agree with its endpoint Behavior;
- `ignore-while-active` to guard one boolean field, activate it in Pending
  State, and reset it in both Success and Failure State;
- response mappings to use that Flow's declared response type;
- response fields not to appear in Pending State;
- `error` mappings to appear only in Failure State.

## Final runtime validation

Prove every Flow independently:

- register its exact Event once with a named `on<Event>` handler;
- dispatch Widget-triggered Events inline from the declared Widget/action
  callback (`onTap`, `onPressed`, `onChanged`, and the other supported semantic
  callback names) through the conventional `vm`, `viewModel`, or `bloc`
  receiver, or a typed `context.read/watch<XxxViewModel>()`; indirect helper
  callbacks and arbitrary receivers are outside the statically proven convention;
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
- navigate only after success when `app-on-success` is declared.

Treat a missing second or later Flow as a validation failure even when another
handler integrates successfully.

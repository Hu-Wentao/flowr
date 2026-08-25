# API Contract Semantics

## Contents

- UI API classification
- Endpoint-scoped BFF behavior
- Query behavior
- Command behavior
- Request field provenance
- Frontend interactions
- Backend authority
- BFF service declaration
- Validation gates

Store `.c.dart` contract sections in consecutive `///` comments. Write
descriptive values in the resolved Contract Description Language while keeping
identifiers, types, methods, paths, enum literals, and source expressions
unchanged.

## UI API Classification

Infer each UI-facing API as:

- `query`: supplies UI data without causing a backend state transition;
- `command`: completes or confirms a state-changing user operation.

Do not add an API-type field. GET is a query. PUT, PATCH, and DELETE are
commands. Classify POST from its approved effect.

For BFF contracts, identify each endpoint by its unique request boundary type
and write one record under `Behaviors:`. Keep singular `Behavior:` only for
explicit non-BFF `API:` mode. Read `frontend-interactions.md` before defining
BFF Events or runtime state transitions.

## Unresolved Data Boundary

Do not infer an API-less/local-only decision from Figma, fixture data, or an
absent API description. When a screen needs data, search, filtering, refresh,
or a state-changing interaction and its approved UI API or backend evidence is
unknown, record this in its `.c.dart` contract:

```dart
/// Data Boundary:
/// - TODO(data-boundary): customer search — confirm the approved UI API/OpenAPI operation before implementing sample-data filtering.
```

The marker must name the capability and the missing authority or evidence so
`rg -n 'TODO\\(data-boundary\\)' lib` is an actionable follow-up list. It is
valid only while drafting: contract and final validation reject it. Do not
replace it with `BFF-UI-API: -`. That API-less declaration is reserved for an
explicit approved local-only decision with a concise reason in `Notes:`.

## Query Behavior

```dart
/// BFF-UI-API:
/// GET /orders/:orderId
/// [OrderDataBffReq], [OrderDataBffRsp]
/// Behaviors:
/// - Endpoint: [OrderDataBffReq]
/// - UI Data: order summary and available actions
/// - Source: approved order UI requirements
/// - Loading/Refresh: show loading initially and keep data while refreshing
/// - Empty/Error: missing order is empty; failure is blocking with retry
```

## Command Behavior

```dart
/// BFF-UI-API:
/// POST /orders
/// [SubmitOrderBffReq], [SubmitOrderBffRsp]
/// Behaviors:
/// - Endpoint: [SubmitOrderBffReq]
/// - Effect: submit the approved order operation
/// - Success: orderId proves success
/// - Failure: inventory-changed -> restore submit state and show refresh
/// - Navigation: app
```

A command response must contain non-UI success evidence. Every failure maps to
an App recovery/display action.

## Request Field Provenance

Trace every UI request field exactly once:

```dart
/// Request Field Sources:
/// - Endpoint: [SubmitOrderBffReq]
/// - cartId <- CartModel.cartId | selects the cart to submit
```

This mapping describes the frontend UI API only. It does not define backend
SDK parameters or DTO fields. Require one endpoint-scoped provenance record for
every BFF endpoint; use `- none` inside the record when its request has no
fields.

## Frontend Interactions

Declare `Interactions:` after request provenance. Document only
ViewModel-owned Flows: bind each owned trigger to one Bloc Event, one UI API
request identity or VM-owned local action, explicit state phases, concurrency,
and navigation signal. Do not create Events or Flows for View-local typed Page
navigation, overlays, controllers, or other presentation-only callbacks. Do not
duplicate backend flow or API meaning. Read `frontend-interactions.md` for the
authority rules, fixed grammar, and runtime gates.

## Backend Authority

Do not declare backend APIs or flow in `.c.dart`. In particular, reject
`Backend Calls`, `Backend Call Flow`, `SDK Calls`, and `SDK Call Flow`.

Backend developers upload `.openapi.json` and maintain the complete
`后端业务流程与业务逻辑 API` section in `xxx.bff.md`. The skill validates that
section but never edits it. Read `bff-dual-authority.md` for its syntax and
preservation rules.

## BFF Service Declaration

For runtime backend calls, declare:

```dart
/// BFF Service: [SubmitOrderService]
```

`xxx.srv.dart` is an SDK adapter. It imports concrete clients from
`lib/api/gen` and is not `@RestApi`. The generator must not create or overwrite
it. The ViewModel injects it, constructs requests, awaits calls, maps responses
to state, and restores loading/submitting state on failure.

When successful business/API results, or a VM-owned local state/business
outcome, require navigation, declare
`Navigation: view-listener-on-success [Model].field = Enum.member`. Give the
nullable semantic enum field one owning Flow, reset it to `null` in Pending
State, set the exact member only in Success State, and forbid every other Flow,
handler, Failure/post-catch region, or undeclared VM region from writing it. A
View `FrListener`/`FrConsumer` binds the exact ViewModel/Model generics, proves
`previous != current` or uses an equality early-return guard, and navigates
inside the exact enum-member braced branch. The ViewModel must not own
BuildContext, router types, or router calls. Retain `Navigation: none` when no
navigation follows; direct presentation routing remains no Flow.

Allow a semantic `typedef` for a generated SDK request type constructed by the
ViewModel. Keep response signatures in their original generated SDK form by
default. Every alias must preserve the exact underlying type and cannot rename
fields or change structure.

Before declaring a BFF request class, compare the frontend method/path with the
backend-owned business API list. If both are identical, the frontend entry is a
direct backend boundary: its `XxxBffReq` must be an exact typedef of the
generated SDK request payload. Do not use a larger UI aggregate request and
then reconstruct the SDK DTO in the Service. Multi-call orchestration has no
standalone UI HTTP contract unless it owns a distinct approved endpoint, so use
`BFF-UI-API: -` in the local-orchestration case.

## Approval Gate

Present only the UI method/path, UI Req/Rsp, behavior, field provenance, and
Service name for frontend approval. Do not invent or edit backend APIs or flow.
When the backend section is missing or inconsistent, stop and request a backend
developer update.

## Validation Gates

Contract validation rejects incomplete endpoint-scoped UI semantics,
provenance gaps, missing ViewModel-owned interaction coverage, invalid
state/Event/Widget/enum references, legacy `app-on-success`, placeholders, and
backend-owned sections in `.c.dart`.

Final validation additionally requires the current v9 BFF artifact, a valid
backend-owned section, an SDK-adapter Service importing `lib/api/gen`, awaited
ViewModel integration, response-backed state, failure recovery, View-owned
navigation listeners for declared semantic signals, absence of BuildContext or
router calls in the ViewModel, and clean `generate_bff.py --check`.

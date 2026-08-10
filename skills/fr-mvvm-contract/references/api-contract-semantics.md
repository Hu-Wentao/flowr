# API Contract Semantics

## Contents

- UI API classification
- Query behavior
- Command behavior
- Request field provenance
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

## Query Behavior

```dart
/// BFF-UI-API:
/// GET /orders/:orderId
/// [OrderDataBffReq], [OrderDataBffRsp]
/// Behavior:
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
/// Behavior:
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
/// - cartId <- CartModel.cartId | selects the cart to submit
```

This mapping describes `BFF-UI-API` only: the data-request API AI infers from
approved UI requirements. It does not define BFF-BZ-API business logic, backend
SDK parameters, or DTO fields.

## Backend Authority

Do not declare `BFF-BZ-API` backend APIs or flow in `.c.dart`. In particular,
reject `BFF-BZ-API`, `Backend Calls`, `Backend Call Flow`, `SDK Calls`, and
`SDK Call Flow`.

Backend developers provide business logic, publish/configure `.openapi.json`,
and maintain the complete `BFF-BZ-API` section in `xxx.bff.md`. This category
is intentionally not inferred from design. The skill validates that section
but never edits it. Read `bff-dual-authority.md` for its syntax and preservation
rules.

## BFF Service Declaration

For runtime backend calls, declare:

```dart
/// BFF Service: [SubmitOrderService]
```

`xxx.srv.dart` is an SDK adapter. It imports concrete clients from
`lib/api/gen` and is not `@RestApi`. The generator must not create or overwrite
it. The ViewModel injects it, constructs requests, awaits calls, maps responses
to state, restores loading/submitting state on failure, and navigates only after
success.

Allow a semantic `typedef` for a generated SDK request type constructed by the
ViewModel. Keep response signatures in their original generated SDK form by
default. Every alias must preserve the exact underlying type and cannot rename
fields or change structure.

## Approval Gate

Present only the BFF-UI-API method/path, UI Req/Rsp, behavior, field provenance,
and Service name for frontend approval. Do not invent or edit BFF-BZ-API
business logic or flow.
When the backend section is missing or inconsistent, stop and request a backend
developer update.

## Validation Gates

Contract validation rejects incomplete UI semantics, provenance gaps,
placeholders, and backend-owned sections in `.c.dart`.

Final validation additionally requires the current v9 BFF artifact, a valid
backend-owned section, an SDK-adapter Service importing `lib/api/gen`, awaited
ViewModel integration, response-backed state, failure recovery, and clean
`generate_bff.py --check`.

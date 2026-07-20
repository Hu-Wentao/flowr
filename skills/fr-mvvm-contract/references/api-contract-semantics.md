# API Contract Semantics

## Contents

- AI classification
- Query behavior
- Command behavior
- Request field provenance
- BFF service declaration
- Approval gate
- Validation gate

Store every `.c.dart` contract section in consecutive `///` documentation
comments. Do not wrap contract sections in `/* ... */` blocks.

Write descriptive values in the resolver's `Contract Description Language`.
This includes `Behavior` entries, the purpose prose after `|` in Request Field
Sources, and Notes. Do not translate stable section/field labels, Dart
identifiers or types, HTTP methods or paths, enum literals, code references,
field names before `<-`, or authoritative source expressions between `<-` and
`|`.

## AI classification

Do not ask the user to classify an API or write an API-type field. Infer an
internal kind before defining DTO fields:

- `query` supplies the read model needed to render UI and causes no backend
  state transition.
- `command` completes a user operation and causes or confirms a backend state
  transition.

Derive the internal kind from the approved API meaning, then write one
user-facing `Behavior:` section. Query fields and command fields are mutually
exclusive. The validator deterministically infers the same kind from those
fields; it never relies on an unrecorded model decision.

Prefer separate APIs when a component both reads data and submits an operation.
If an upstream endpoint cannot be split, use the command behavior and stricter
gate. GET must be a query. PUT, PATCH, and DELETE must be commands. POST may be
either according to its approved effect.

## Query behavior

For an internal query, retain only these `Behavior` fields:

```dart
/// BFF-API:
/// GET /orders/:orderId
/// [OrderDataBffReq], [OrderDataBffRsp]
/// Behavior:
/// - UI Data: order summary, line items, available actions
/// - Source: order and catalog services aggregated by the BFF
/// - Loading/Refresh: show loading initially and keep current data while refreshing
/// - Empty/Error: missing order is empty; summary failure is blocking with retry
```

## Command behavior

For an internal command, retain only these `Behavior` fields:

```dart
/// BFF-API:
/// POST /orders
/// [SubmitOrderBffReq], [SubmitOrderBffRsp]
/// Behavior:
/// - Effect: create an order and reserve its inventory
/// - Success: orderId proves the order was created
/// - Failure: inventory-changed -> restore submit state and show refresh action;
///   checkout-expired -> restore submit state and return to checkout preparation
/// - Navigation: app
```

Before approval, determine what backend state changes, which response field
proves success, how the App recovers from each failure, and whether navigation
belongs to `app` or `none`. Infer these facts only from authoritative API,
product, flow, or user-provided context. Ask the user only about facts that
remain uncertain; never invent them.

A command response must contain a non-UI result referenced by `Success`.
Fields such as `nextRoute`, `title`, and `message` may be auxiliary but cannot
be the only response. Write every failure as
`error -> App recovery/display`, separated by semicolons.

## Request field provenance

Trace every request DTO field exactly once:

```dart
/// Request Field Sources:
/// - checkoutToken <- PrepareCheckoutBffRsp.checkoutToken | authorizes this checkout
/// - cartId <- CartModel.cartId | selects the cart to submit
/// - deliveryOptionId <- CheckoutModel.deliveryOptionId | selects fulfillment
```

The source must name an upstream response, user input, approved flow state, or
other authoritative origin. The purpose must explain why the backend needs the
field. Use `/// - none` only when the request DTO has no fields.

## BFF service declaration

For BFF contracts that require runtime integration, reference the Dart class
that the generator must create:

```dart
/// BFF Service: [SubmitOrderService]
```

Every BFF-JSON contract must declare `BFF Service: [Type]`. Contract-only BFF
delivery, omitted service declarations, `BFF Runtime`, and `BFF Service: none`
are obsolete. Explicit API mode is outside this generated BFF Service workflow.

Final validation proves the referenced Dart service class, ViewModel
injection, an asynchronous registered query/command handler, request
construction, awaited service invocation, response-backed state, failure
state, submit/loading recovery, and no navigation before a successful response.

When absent, `generate_bff.py` reads every generated BFF Markdown endpoint and
creates one independent Retrofit `xxx.srv.dart` whose `@RestApi` abstract class
is `Type`. It uses `@RestApi()` and `factory Type(Dio dio)`; the application
environment configures the supplied Dio's base URL. An endpoint without path parameters is a typed semantic lower-camel
Retrofit operation directly on that Service, with its `XxxBffReq` annotated as
`@Body()` or `@Queries()`. Every request DTO explicitly declares
`Map<String, dynamic> toJson();`. Only an endpoint with path parameters uses a
private annotated JSON-map transport method and a same-file typed extension so
path fields can be removed from the payload. Never expose generic `call` or
`execute` operations. A request
matching the component name keeps that name (`ConfirmPasswordBffReq` becomes
`confirmPassword`); additional operation requests remove the component prefix
(`ConfirmPasswordPolicyBffReq` becomes `policy`). After first generation,
`.srv.dart` is project code and may change to match the backend; generation and
refresh must preserve it. Run build_runner to generate `xxx.srv.g.dart`.

## Approval gate

Before drafting DTOs, draw the cross-component state flow, internally classify
each API, let AI organize the applicable `Behavior` fields, and map every
request field. Present the method/path, Req/Rsp/Error design, behavior,
provenance, and generated service class together. Do not require the user to
write or format the behavior section.

If an authoritative fact is unknown, ask only for that fact and keep its draft
marker invalid. Do not invent `/bootstrap`, `nextRoute`, proof tokens, success
flags, error codes, or recovery behavior. Never reverse-generate API meaning
from a mock ViewModel.

## Validation gate

Run `validate_contract.py --phase contract` before BFF/DTO derivation. It
rejects pending markers, incomplete or mixed query/command behavior, request
fields without provenance, UI-only command responses, `Success` values that do
not reference response fields, and failures without recovery mappings.

Run `validate_contract.py --phase final` after service, ViewModel, View, and
generated files are complete. A declared `BFF Service` makes actual service
execution part of final delivery; an up-to-date `xxx.bff.md` alone is not
enough.

# API Contract Semantics

## Contents

- API types
- Data contract
- Business contract
- Request field provenance
- Runtime declaration
- Approval gate
- Validation gate

## API types

Store every `.c.dart` contract section in consecutive `///` documentation
comments. Do not wrap contract sections in `/* ... */` blocks.

Write descriptive values in the resolver's `Contract Description Language`.
This includes Data and Business entries, the purpose prose after `|` in
Request Field Sources, and Notes. Do not translate stable section/field labels,
Dart identifiers or types, HTTP methods or paths, enum literals, code
references, field names before `<-`, or authoritative source expressions
between `<-` and `|`.

Classify every API before defining DTO fields:

```dart
/// API Type: data
```

or:

```dart
/// API Type: business
```

A `data` API supplies the read model needed to render UI. It must not cause a
business state transition. A `business` API completes a user operation and
causes or confirms a backend state transition.

Prefer separate data and business APIs when a component both loads content and
submits an operation. If an upstream endpoint cannot be split, classify it as
`business` and apply the stricter gate.

## Data contract

Keep only `Data:` for a data API:

```dart
/// API Type: data
/// BFF-API:
/// GET /orders/:orderId
/// [OrderDataBffReq], [OrderDataBffRsp]
/// Data:
/// - UI Data: order summary, line items, available actions
/// - Source: order and catalog services aggregated by the BFF
/// - Loading/Refresh: show loading initially and keep current data while refreshing
/// - Empty/Error: missing order is empty; summary failure is blocking with retry
```

GET and query-style POST are valid data transports. PUT, PATCH, and DELETE are
not data operations.

## Business contract

Keep only `Business:` for a business API:

```dart
/// API Type: business
/// BFF-API:
/// POST /orders
/// [SubmitOrderBffReq], [SubmitOrderBffRsp]
/// Business:
/// - Goal: submit the reviewed cart as an order
/// - Upstream Proof: checkoutToken from PrepareCheckoutBffRsp
/// - Effect: create an order and reserve its inventory
/// - Success Condition: orderId proves the order was created
/// - Failure Cases: inventory-changed -> restore submit state and show refresh action;
///   checkout-expired -> restore submit state and return to checkout preparation
/// - Navigation Ownership: app
```

Answer before approval:

1. What operation is the user completing?
2. What backend state changes on success?
3. Where does the identity, authorization, or flow proof come from?
4. Which response field proves success?
5. How does the App recover and present each failure?

Use POST, PUT, PATCH, or DELETE for a business command. The response must
contain a non-UI business result referenced by `Success Condition`. Fields
such as `nextRoute`, `title`, and `message` may be auxiliary, but cannot be the
only response. `Navigation Ownership` is `app` or `none`.

Write every failure as `error -> App recovery/display`, separated by
semicolons. Do not list error codes without recovery behavior.

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

Omit `BFF Service` entirely for contract-only delivery. Do not write
`BFF Runtime` or `BFF Service: none`; both forms are obsolete.

When `BFF Service` exists, final validation proves the referenced Dart service
class, ViewModel injection, an async registered data/command handler,
request construction, awaited service invocation, response-backed state,
failure state, submit/loading recovery, and no navigation before the successful
response.

When absent, `generate_bff.py` reads the generated BFF Markdown and creates an
independent Retrofit `xxx.srv.dart` whose public wrapper class is `Type`. After
that first generation, `.srv.dart` is project code and may change to match the
backend; generation and refresh must preserve it. Run build_runner to generate
`xxx.srv.g.dart`. Validation checks the class, import, part directive, and
generated file, not template equality. Service reuse follows the owning
component's reuse scope; the field carries no separate ownership prefix.

## Approval gate

Before drafting DTOs, draw the cross-component state flow, classify each API,
define data read-model behavior or business proof/effect/result/error behavior,
and map every request field. Present the method/path, Req/Rsp/Error design,
semantic section, provenance, and optional generated service class together.

If any item is unknown, stop for user input or design approval. Keep the draft
marker invalid; do not invent `/bootstrap`, `nextRoute`, proof tokens, success
flags, or error codes. Never reverse-generate API meaning from a mock
ViewModel.

## Validation gate

Run `validate_contract.py --phase contract` before BFF/DTO derivation. It
rejects pending markers, missing semantic fields, mixed Data/Business
sections, request fields without provenance, UI-only command responses,
success conditions that do not reference response fields, and failures without
recovery mappings.

Run `validate_contract.py --phase final` after service, ViewModel, View, and
generated files are complete. A declared `BFF Service` makes actual service
execution part of final delivery; an up-to-date `xxx.bff.md` alone is not
enough.

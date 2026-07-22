# BFF UI/OpenAPI Authority Format

## Contents

- Ownership boundary
- Component contract syntax
- YAML Front Matter
- Markdown body
- Generation
- Validation
- Compatibility

## Ownership Boundary

Generate every BFF artifact as one reviewable Markdown file with four domains:

- **UI API Contract** is frontend-owned. It defines the HTTP method/path and
  inline request/response DTOs that the frontend needs from the BFF. UI API DTO
  fields remain `XxxBffReq`/`XxxBffRsp` declarations extracted from `.c.dart`.
- **Backend Call Contract** is OpenAPI-owned. Every BFF-to-backend operation is
  identified by an `.openapi.json` location, HTTP method, and API request path.
  Never copy that operation's request or response schema into the BFF Markdown.
- **UI Contract** is frontend-owned. It contains component `@FrState` model
  fields, behavior, and presentation structure.
- **Integration Mapping** is frontend-owned. It maps UI/flow sources into the
  UI API request. Backend orchestration and result/error mapping belong in the
  backend call flow without redefining OpenAPI schemas.

An OpenAPI location may be either a path relative to the configured local
OpenAPI root or an `http`/`https` URL. The local root defaults to the project
root. A project may map it to a checked-out documentation authority while the
authored BFF path remains relative to that authority's publication root. Local
absolute paths, root traversal, `file:` URLs, and files whose path does not end
in `.openapi.json` are invalid.

## Component Contract Syntax

Keep `BFF-API:` as the UI-facing API section because `fr_acdd:extract_bff`
reads it. Declare backend operations separately:

```dart
/// BFF-API:
/// POST /bff/orders/submit
/// [SubmitOrderBffReq], [SubmitOrderBffRsp]
/// Backend Calls:
/// - createOrder <- openapi/orders.openapi.json | POST /orders
/// - getOrder <- openapi/orders.openapi.json | GET /orders/{orderId}
/// - auditOrder <- https://api.example.com/audit.openapi.json | POST /audit/orders
/// Backend Call Flow:
/// - [createOrder] 使用 UI 请求创建订单
/// - [getOrder] 创建成功后读取订单，并映射为 UI 响应
/// - [auditOrder] 订单确认后写入审计；失败时按已批准策略恢复
```

The same `.openapi.json` document may be referenced by any number of backend
calls. Method and request path are mandatory on every entry and uniquely select
the operation within that document. Use `- none` for both backend sections only
when the BFF operation requires no backend call.

The call flow may describe ordering, conditions, request/result mapping, and
error recovery. It must reference every call id as `[id]`; it must not contain
copied backend Request/Response JSON5 or a second DTO declaration.

## YAML Front Matter

Use YAML Front Matter at the beginning of every generated `*.bff.md`:

```yaml
---
bff_meta:
  schema: "bff-md-meta/v5"
  contract_version: "2.0.0"
  ui_revision: "1.0.0"
  mode: BFF-JSON
  contract_file: "lib/app/order_content/order_content.c.dart"
  authorities:
    ui_api:
      owner: frontend
    backend_api:
      owner: openapi
    ui:
      owner: frontend
  ui_apis:
    - method: POST
      route: "/bff/orders/submit"
      request: SubmitOrderBffReq
      response: SubmitOrderBffRsp
      behavior: command
  backend_calls:
    - id: createOrder
      openapi: "openapi/orders.openapi.json"
      method: POST
      route: "/orders"
    - id: getOrder
      openapi: "openapi/orders.openapi.json"
      method: GET
      route: "/orders/{orderId}"
---
```

Quote schema versions, paths, URLs, and other values that YAML could coerce.
Keep `contract_version` independent from `ui_revision`: UI API transport
changes bump the former; UI-only changes bump the latter.

## Markdown Body

Render these top-level sections in order:

1. `UI API Contract` with extracted `BFF-API` request/response JSON5.
2. `Backend Call Contract` with OpenAPI references and `Backend Call Flow`.
3. `UI Contract` with UI state, Behavior, and Widget Tree.
4. `Integration Mapping` with UI API `Request Field Sources`.

Every backend OpenAPI reference in the body retains its method and API request
path. Do not render backend request/response schemas even when the referenced
document contains them. The Retrofit generator reads only the UI API endpoint
and request JSON5 data.

## Generation

1. Extract UI API DTOs with `fr_acdd:extract_bff` into a temporary artifact.
2. Parse UI API endpoint identities and JSON5 shapes.
3. Resolve every backend OpenAPI reference, then verify the exact method/path
   operation exists. Fetch network references with a bounded timeout and size.
4. Wrap UI API and backend-call metadata in deterministic YAML Front Matter.
5. Render backend references and authored call flow without backend schemas.
6. Read UI models, Behavior, Widget Tree, Figma, and Request Field Sources.
7. Generate or check frontend Retrofit only from the UI API Contract.

Never copy raw Dart source, absolute local paths, credentials, or fetched
OpenAPI content into the artifact.

## Validation

Require generated BFF artifacts to satisfy these invariants:

- the file begins with `bff-md-meta/v5` YAML Front Matter;
- `authorities.ui_api.owner` is `frontend`,
  `authorities.backend_api.owner` is `openapi`, and
  `authorities.ui.owner` is `frontend`;
- every `ui_apis` entry matches `BFF-API` method, route, request, response, and
  inferred behavior;
- every UI API request/response field comes from an annotated BFF DTO;
- every backend call has a unique id, `.openapi.json` location, method, and
  request path, and the referenced operation exists;
- every backend call id appears in `Backend Call Flow`;
- backend request/response schemas do not appear in the BFF backend section;
- every UI API request field has exactly one `Request Field Sources` mapping;
- stale checks compare the complete deterministic artifact.

Packaging includes only BFF Markdown. Local and network OpenAPI documents remain
independently owned references and are never copied into the BFF archive or by
the BFF synchronization step.

## Compatibility

`bff-md-meta/v5` is a breaking artifact-format change. Consumers of v4 must
migrate from `apis` and `Business Contract` to `ui_apis`, `UI API Contract`,
and `Backend Call Contract`. UI API DTO semantics and generated frontend
Retrofit operation behavior remain compatible.

For migration only, a pre-existing source contract that declares neither
`Backend Calls` nor `Backend Call Flow` continues to reproduce its v4 artifact.
New drafts always contain both sections and generate v5. Adding either section
opts that component into v5; do not remove the sections to downgrade it.

# BFF Backend Logic / UI Data Format

## Contents

- Ownership boundary
- Component contract syntax
- YAML Front Matter
- Markdown body
- Generation
- Validation
- Compatibility

## Ownership Boundary

Generate every BFF artifact as one reviewable Markdown file with two ordered domains:

- **后端逻辑流程接口** is backend-owned. It only references backend-created
  `.openapi.json` APIs and DTOs, lists the APIs used by this BFF, explains their
  use cases, and states call order. AI must never create, edit, infer, or
  redefine backend API paths, fields, or DTOs here.
- **前端 UI 数据接口** is frontend-owned. It defines UI-facing BFF paths plus
  `XxxBffReq` / `XxxBffRsp` JSON5 shapes that AI may derive from approved Figma
  and UI requirements. UI State, Behavior, Widget Tree, and request mappings
  remain frontend-owned subsections of this domain.

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

1. `后端逻辑流程接口`: `.openapi.json 文档引用`, `本 BFF 使用的 API 列表`,
   `API 使用场景`, and ordered `调用时序`.
2. `前端 UI 数据接口`: `接口描述`, one subsection per BFF path with Req/Rsp
   class names and Request/Response JSON5, then UI Contract and Integration
   Mapping.

Every backend OpenAPI reference in the body retains its method and API request
path. Do not render backend request/response schemas even when the referenced
document contains them. The Retrofit generator reads only the UI API endpoint
and request JSON5 data.

### UI State Format

Render `### UI State` as one `json5` code block, never as a Markdown table.
Keep it structurally consistent with UI API request and response examples. For
each field, add consecutive comments for its owning Model, Dart type, and
`Authority: Frontend`, then render a JSON5 example value. Use `null` only for
nullable fields; use an empty object only when a non-null custom Dart type has
no serializable literal. Do not put HTTP DTO fields in this block.

```json5
{
  // Model: OrderContentModel
  // Dart type: bool
  // Authority: Frontend
  isExpanded: false,
}
```

## Generation

1. Extract UI API DTOs with `fr_acdd:extract_bff` into a temporary artifact.
2. Parse UI API endpoint identities and JSON5 shapes.
3. Resolve every backend OpenAPI reference, then verify the exact method/path
   operation exists. Fetch network references with a bounded timeout and size.
4. Wrap UI API and backend-call metadata in deterministic YAML Front Matter.
5. Render the backend document references, API list, use cases, and ordered
   call sequence without backend schemas.
6. Read UI models, Behavior, Widget Tree, Figma, and Request Field Sources.
7. Generate or check frontend Retrofit only from the UI API Contract.

Never copy raw Dart source, absolute local paths, credentials, or fetched
OpenAPI content into the artifact.

## Validation

Require generated BFF artifacts to satisfy these invariants:

- the file begins with `bff-md-meta/v6` YAML Front Matter;
- `authorities.backend_logic.owner` is `backend`, `authorities.ui_api.owner` is
  `frontend`, and
  `authorities.ui.owner` is `frontend`;
- every `ui_apis` entry matches `BFF-API` method, route, request, response, and
  inferred behavior;
- every UI API request/response field comes from an annotated BFF DTO;
- UI State is a single JSON5 code block with Model, Dart type, and Frontend
  authority comments for every state field; Markdown state tables are invalid;
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

`bff-md-meta/v6` is a breaking artifact-format change. Consumers must migrate
from `Business Contract` / `UI API Contract` / `Backend Call Contract` to the
ordered `后端逻辑流程接口` and `前端 UI 数据接口` domains. UI API DTO semantics
and generated frontend Retrofit operation behavior remain compatible.

For migration only, a pre-existing source contract that declares neither
`Backend Calls` nor `Backend Call Flow` continues to reproduce its v4 artifact.
New drafts always contain both sections and generate v5. Adding either section
opts that component into v5; do not remove the sections to downgrade it.

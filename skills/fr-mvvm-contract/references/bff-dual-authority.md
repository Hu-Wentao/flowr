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

- **后端逻辑 API（SDK）** is backend-owned. The generated SDK exclusively owns
  API paths, HTTP methods, parameters, and wire DTOs. AI may select a published
  `GeneratedApi.operation` and describe orchestration, but must never edit or
  redefine the SDK API.
- **前端 UI 数据 API（BFF-API）** is frontend-owned. AI may create and edit its
  UI-facing paths, `XxxBffReq` / `XxxBffRsp` JSON5 shapes, and UI mapping from
  approved Figma and UI requirements. UI State, Behavior, and Widget Tree also
  remain frontend-owned.

The generated concrete `XxxApi` classes are the SDK. A frontend Service injects
only the concrete API it needs; do not create an aggregate SDK, gateway, facade,
or backend name that is absent from OpenAPI. An SDK operation's existence proves
it is callable, not that the app should invoke it: AI must not add a network
call without an approved UI/flow trigger and authoritative request-field
sources.

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
/// SDK Calls:
/// - createOrder <- OrdersApi.createOrder
/// - getOrder <- OrdersApi.getOrder
/// - auditOrder <- AuditApi.auditOrder
/// SDK Call Flow:
/// - [createOrder] 使用 UI 请求创建订单
/// - [getOrder] 创建成功后读取订单，并映射为 UI 响应
/// - [auditOrder] 订单确认后写入审计；失败时按已批准策略恢复
```

Each SDK call names exactly one generated client operation. Do not include an
HTTP method, request path, request parameter, or backend DTO in a BFF contract.
Use `- none` for both SDK sections only when the BFF operation requires no SDK
call.

The call flow may describe ordering, conditions, request/result mapping, and
error recovery. It must reference every call id as `[id]`; it must not contain
copied backend Request/Response JSON5 or a second DTO declaration.

## YAML Front Matter

Begin every generated `*.bff.md` with compact identity and source metadata:

```yaml
---
bff_meta:
  schema: "bff-md-meta/v7"
  namespace: "order_content"
  contract_version: 1
  ui_source:
    type: figma
    url: "https://www.figma.com/design/..."
---
```

Read `namespace` and `contract_version` from the component's `@FrAcddPage`
annotation; an omitted annotation version is `1`. Copy `ui_source.url` from the
contract's `Figma` section. Derive the contract source from the adjacent,
same-basename `.c.dart`; do not repeat its path. Do not repeat mode, ownership,
UI API, SDK-call, or Page-route data in YAML. Those facts are fixed by the
format, rendered in the Markdown body, or owned by an optional Page adapter
rather than the component.

## Markdown Body

Render these top-level sections in order:

1. `后端逻辑流程接口`: `本 BFF 使用的 SDK 操作`,
   `API 使用场景`, and ordered `调用时序`.
2. `前端 UI 数据接口`: `接口描述`, one subsection per BFF path with Req/Rsp
   class names and Request/Response JSON5, then UI Contract and Integration
   Mapping.

Do not render SDK HTTP paths, methods, parameters, or backend request/response
schemas. The Retrofit generator reads only the UI API endpoint and request JSON5 data.

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
3. Resolve every SDK client operation against `lib/api/generated`.
4. Wrap the artifact in compact `bff-md-meta/v7` YAML Front Matter.
5. Render the SDK operation list, use cases, and ordered
   call sequence without backend schemas.
6. Read UI models, Behavior, Widget Tree, Figma, and Request Field Sources.
7. Generate or check frontend Retrofit only from the UI API Contract.

When a UI flow consumes an SDK operation, implement the frontend Service as an
adapter over the referenced concrete `XxxApi`; do not create an SDK aggregator.
Keep UI DTO mapping explicit. Do not create pages, flows, or automatic SDK calls
only to make an existing SDK operation appear used.

Never copy raw Dart source, absolute local paths, credentials, or fetched
OpenAPI content into the artifact.

## Validation

Require generated BFF artifacts to satisfy these invariants:

- the file begins with `bff-md-meta/v7` YAML Front Matter containing schema,
  namespace, contract version, and the declared UI source, followed by its
  `# XxxView BFF Contract` title;
- every UI API section matches `BFF-API` method, route, request, and response;
- every UI API request/response field comes from an annotated BFF DTO;
- UI State is a single JSON5 code block with Model, Dart type, and Frontend
  authority comments for every state field; Markdown state tables are invalid;
- every SDK call has a unique id and resolves to a generated SDK client operation;
- every SDK call id appears in `SDK Call Flow`;
- SDK HTTP paths, methods, parameters, and DTO schemas do not appear in the BFF backend section;
- every runtime SDK call has an approved UI/flow trigger and request-field sources;
- Services depend on the referenced concrete `XxxApi`, never a synthetic aggregate SDK or backend boundary;
- every UI API request field has exactly one `Request Field Sources` mapping;
- stale checks compare the complete deterministic artifact.

Packaging includes only BFF Markdown. Local and network OpenAPI documents remain
independently owned references and are never copied into the BFF archive or by
the BFF synchronization step.

## Compatibility

`bff-md-meta/v7` is a breaking metadata-format change. Consumers must accept
the compact identity/source YAML Front Matter and read UI API and SDK-call
details from the ordered `后端逻辑流程接口` and `前端 UI 数据接口` Markdown
domains. The removed metadata fields are not compatibility aliases. UI API DTO
semantics and generated frontend Retrofit operation behavior remain compatible.

`Backend Calls` and `Backend Call Flow` are obsolete and rejected. Migrate them
to `SDK Calls` and `SDK Call Flow`; BFF contracts identify SDK symbols only.

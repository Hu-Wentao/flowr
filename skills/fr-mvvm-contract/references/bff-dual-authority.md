# BFF Backend Logic / UI Data Format

## Contents

- Ownership boundary
- Backend-owned format
- Frontend-owned format
- API query records
- Generation and preservation
- Runtime Service
- Validation
- Compatibility

## Ownership Boundary

One `xxx.bff.md` contains two ordered authority domains:

- `后端业务流程与业务逻辑 API` is written by backend developers. Its business
  APIs come from published `.openapi.json` documents. The skill may validate
  this section but must never create, edit, normalize, reorder, or delete it.
- `前端 UI 数据接口` is written by the skill from approved UI requirements and
  the component contract. The skill may create and refresh this section.

OpenAPI exclusively owns backend method/path semantics, parameters, DTO names,
DTO fields, and wire behavior. Backend developers exclusively own the business
flow. The skill must not move either authority into `.c.dart`.

## Backend-Owned Format

Use this fixed section shape:

```markdown
## 后端业务流程与业务逻辑 API

> Authority: Backend. 此区域由后端开发维护。

### 业务逻辑 API

- [apply] POST /app/noLogin/trans/auth/apply | Parameters: body ReqWrapper<TransAuthNoLoginApplyReq> | Response: RspWrapper<AuthInfoDto>

### 业务流程

- [apply] 申请未登录认证并将 authId 返回给后续验证步骤
```

Each API line contains only:

- a stable call id;
- HTTP method and request path;
- parameter names and generated SDK type names;
- generated SDK response type.

The backend authority domain may also contain backend-authored prose, JSON,
DTO field examples, copied schema excerpts, or code blocks. Keep these
supplementary examples outside each machine-readable API entry. The parser
ignores them when building `API Query Records`, preserves them byte-for-byte,
and never treats them as frontend DTO authority.

Every machine-readable call id must appear in the backend-written flow. Use
`- none` in `### 业务逻辑 API` when the domain has no machine-declared business
API; `### 业务流程` may still contain prose and JSON/DTO examples.

Validation resolves method/path against exactly one OpenAPI operation under the
configured OpenAPI root and resolves referenced non-primitive type names from
`lib/api/gen`. A mismatch is an error for backend developers to correct; the
skill must not rewrite the annotation or flow.

## Frontend-Owned Format

The frontend domain contains the UI-facing data API, UI DTO JSON5, UI State,
endpoint-scoped Behavior, frontend interaction Flows, Widget Tree, and Integration Mapping. AI may edit only this domain from approved Figma and UI requirements.

UI DTO fields must never be presented as backend DTO fields. A UI type may map
or aggregate values returned by multiple backend SDK calls without redefining
the backend field meanings.

Render the frontend contract in this fixed order: `接口描述`, `UI State`,
endpoint-scoped `UI Behavior`, `前端交互逻辑`, `UI Structure`, endpoint-scoped
`Integration Mapping`, and `API Query Records`. Derive Behaviors, interaction
Flows, and provenance from `.c.dart`; never edit their Markdown projections as
parallel facts.

## YAML Front Matter

Begin every artifact with compact identity/source metadata:

```yaml
---
bff_meta:
  schema: "bff-md-meta/v9"
  namespace: "order_content"
  contract_version: 1
  ui_source:
    type: figma
    url: "https://www.figma.com/design/..."
mdq:
  version: 2
  # Generated API Query Records table-row contract.
---
```

Read namespace and version from `@FrAcddPage(namespace: ..., version: ...)`;
the annotation field is exactly `version`, never `contractVersion`. Copy the UI
source from the contract. Do not duplicate backend APIs or flow in metadata.

## API Query Records

Append one generated `API Query Records` GFM table after the authority domains.
Treat it as a verification projection, never as API authority. Its mdq v2
contract exposes one stable row per backend business API, UI API, observed
runtime-only backend call, or explicit API-less disposition. Expose at least:

- namespace, API type, operation, method, and path;
- `contract_status`: `declared`, `missing_backend_contract`, or `api_less`;
- `integration_status`: `integrated`, `unconfirmed`, or `not_required`;
- authority and source-located verification evidence.

Derive backend integration only from a concrete generated SDK method called by
the component Service. Emit a `missing_backend_contract` row when the Service
calls a generated backend method/path absent from the backend-owned BFF list;
do not copy that observation into the backend authority section. Derive UI
integration only when the component Service declares the semantic operation
and its ViewModel awaits it. A declaration without that runtime evidence is
`unconfirmed`, not integrated.

Keep the table deterministic and machine-owned. Refresh it after Service or
ViewModel changes. `generate_bff.py --check` must reject stale integration
records. Collection consumers may use mdq `scan --require-contract` and the
named API queries without parsing DTO prose or Dart source.

## Generation And Preservation

For a new artifact, generate a backend-owned placeholder containing `- none`
and generate the complete frontend domain. The placeholder is not permission
for AI to invent backend APIs or flow.

For an existing artifact:

1. locate the exact text from `## 后端业务流程与业务逻辑 API` up to
   `## 前端 UI 数据接口`;
2. validate it without mutation;
3. render refreshed metadata and frontend content;
4. reinsert the backend text byte-for-byte.

`generate_bff.py --check` applies the same merge in memory. It reports stale UI
content or invalid backend annotations without modifying either file.

## Runtime Service

`xxx.srv.dart` is a frontend SDK adapter over the generated clients in
`lib/api/gen`. It is not a Retrofit client generated from the UI data API.
It must import each concrete generated SDK it needs and use the application
provided `Dio`.

Permit a semantic request alias when the ViewModel constructs the request:

```dart
typedef VerifyMobileApplyReq = auth_sdk.TransAuthNoLoginApplyReq;

Future<auth_sdk.RspWrapper<auth_sdk.AuthInfoDto>> apply(
  VerifyMobileApplyReq request,
);
```

The alias must preserve the exact SDK type. Do not rename fields, change
generic arguments, or create a replacement DTO. Keep response signatures in
their original generated SDK form by default; add a response alias only when
the response type itself must be stored, passed, or reused as a declaration.

### Direct Backend Boundary Identity

Compare every frontend `BFF-UI-API` method/path with the backend-owned business
API annotations before approving UI DTOs. An exact method/path match identifies
the same backend operation; it does not create a separate frontend endpoint.
The `XxxBffReq` named by that frontend entry must therefore be an exact
`typedef` of the generated SDK request payload carried by `ReqWrapper<T>`.
A structurally similar or larger Freezed request class is forbidden because it
can hide fields that are later dropped when the Service reconstructs `T`.

If one UI action coordinates uploads, OCR, verification, and a final business
call, model it as local orchestration with `BFF-UI-API: -`, or obtain approval for
a genuinely distinct UI endpoint. Never assign the final backend call's
method/path to the aggregate request DTO.

The skill never generates or overwrites SDK adapter logic because backend
developers own the flow that determines its calls.

## Validation

Require:

- ordered backend and frontend authority sections;
- `bff-md-meta/v9`;
- one valid mdq v2 table-row contract over `API Query Records`;
- deterministic API records whose integration status agrees with generated SDK,
  Service, and ViewModel call evidence;
- backend prose and JSON/DTO/code examples remain supplementary and are
  excluded from machine API records;
- every business API line to match the fixed annotation syntax;
- every method/path to resolve to exactly one OpenAPI operation;
- every non-primitive annotated type to exist in `lib/api/gen`;
- every backend call id to appear in the backend-written flow;
- frontend refresh to preserve the backend section exactly;
- one endpoint-scoped Behavior and request-provenance record per UI endpoint;
- complete structured `Interactions` coverage for every UI endpoint;
- generated `### 前端交互逻辑` content to match the source Flow records;
- `.c.dart` to contain no `Backend Calls`, `Backend Call Flow`, `SDK Calls`, or
  `SDK Call Flow`;
- `xxx.srv.dart` to import `lib/api/gen`, not declare `@RestApi`, and preserve
  SDK types or exact `typedef` aliases.
- an exact frontend/backend method-path match to use an `XxxBffReq` typedef of
  the generated SDK request payload, never a replacement request class.

## Compatibility

`bff-md-meta/v9` is a breaking frontend-contract change. Migrate v8 source
contracts by replacing singular `Behavior:` with endpoint-scoped `Behaviors:`,
scoping `Request Field Sources:` by request boundary type, and adding complete
`Interactions:` Flow records. Regenerate the artifact; preserve the complete
backend-owned section byte-for-byte. The v9 migration does not authorize
translating, normalizing, or otherwise editing backend APIs or flow.

The mdq API projection remains compatible in v9. Interaction records stay in
the human-readable frontend domain and do not become API Query Records.

Allowing backend-authored JSON/DTO examples is backward-compatible. Existing
machine API entries and API query records retain their identities; examples do
not create or alter records, and no compatibility configuration is required.

The direct-boundary identity gate is intentionally breaking for contracts that
reuse a backend method/path while declaring an independent UI request class.
Migrate by replacing that class with an exact SDK typedef, or by moving the
multi-call aggregate to a distinct approved UI boundary or `BFF-UI-API: -`.

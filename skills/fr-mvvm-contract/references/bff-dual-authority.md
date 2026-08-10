# BFF-BZ-API / BFF-UI-API Format

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

- `BFF-BZ-API` is written by backend developers. It represents business logic
  that cannot be inferred from a design; backend developers provide its flow,
  publish/configure `.openapi.json`, and own this section. The skill may
  validate it but must never create, edit, normalize, reorder, or delete it.
- `BFF-UI-API` is written by the skill from approved Figma/UI requirements and
  the component contract. It represents AI-inferred UI data requests and the
  skill may create and refresh this section.

OpenAPI exclusively owns backend method/path semantics, parameters, DTO names,
DTO fields, and wire behavior. Backend developers exclusively own the business
flow. The skill must not move either authority into `.c.dart`.

## Backend-Owned Format

Use this fixed section shape:

```markdown
## BFF-BZ-API

> Authority: Backend. This business logic cannot be inferred from design. Backend developers maintain it and configure its `.openapi.json` evidence.

### BFF-BZ-API

- [apply] POST /app/noLogin/trans/auth/apply | Parameters: body ReqWrapper<TransAuthNoLoginApplyReq> | Response: RspWrapper<AuthInfoDto>

### 业务流程

- [apply] 申请未登录认证并将 authId 返回给后续验证步骤
```

Each API line contains only:

- a stable call id;
- HTTP method and request path;
- parameter names and generated SDK type names;
- generated SDK response type.

Never include DTO fields, JSON examples, copied schemas, or generated Dart
source in this section. Every call id must appear in the backend-written flow.
Use `- none` in both subsections only when the feature has no backend business
API.

Validation resolves method/path against exactly one OpenAPI operation under the
configured OpenAPI root and resolves referenced non-primitive type names from
`lib/api/gen`. A mismatch is an error for backend developers to correct; the
skill must not rewrite the annotation or flow.

## Frontend-Owned Format

The `BFF-UI-API` domain contains the UI-facing data-request API, UI DTO JSON5,
UI State, Behavior, Widget Tree, and Integration Mapping. AI may edit only
this domain from approved Figma and UI requirements.

```markdown
## BFF-UI-API

> Authority: Frontend. AI derives this data-request API from approved Figma/UI requirements.

### 接口描述

#### GET /orders/:orderId

- Request DTOs: [OrderDataBffReq]
- Response DTOs: [OrderDataBffRsp]
```

UI DTO fields must never be presented as backend DTO fields. A UI type may map
or aggregate values returned by multiple backend SDK calls without redefining
the backend field meanings.

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
contract exposes one stable row per BFF-BZ-API business API, BFF-UI-API,
observed runtime-only backend call, or explicit API-less disposition. Expose at
least:

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

1. locate the exact text from `## BFF-BZ-API` up to `## BFF-UI-API`;
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

The skill never generates or overwrites SDK adapter logic because backend
developers own the flow that determines its calls.

## Validation

Require:

- ordered `BFF-BZ-API` and `BFF-UI-API` authority sections;
- `bff-md-meta/v9`;
- one valid mdq v2 table-row contract over `API Query Records`;
- deterministic API records whose integration status agrees with generated SDK,
  Service, and ViewModel call evidence;
- no DTO fields or code/JSON blocks in the backend section;
- every BFF-BZ-API line to match the fixed annotation syntax and resolve from
  the backend-configured `.openapi.json` source root;
- every method/path to resolve to exactly one OpenAPI operation;
- every non-primitive annotated type to exist in `lib/api/gen`;
- every backend call id to appear in the backend-written flow;
- frontend refresh to preserve the backend section exactly;
- `.c.dart` to contain no `Backend Calls`, `Backend Call Flow`, `SDK Calls`, or
  `SDK Call Flow`;
- `xxx.srv.dart` to import `lib/api/gen`, not declare `@RestApi`, and preserve
  SDK types or exact `typedef` aliases.

## Compatibility

`bff-md-meta/v9` is a breaking category change. Migrate v8 artifacts by having
backend developers rewrite and approve the backend-owned region as
`BFF-BZ-API` with configured OpenAPI evidence, then regenerate the
frontend-owned `BFF-UI-API` region. Frontend tooling must not automatically
translate old backend content because doing so would edit backend-owned data.

The API Query Records `API Type` values are now exactly `BFF-BZ-API` and
`BFF-UI-API`; consumers filtering the old `backend_logic` or `ui` values must
migrate their queries.

# BFF Business/UI Dual-Authority Format

## Contents

- Ownership boundary
- YAML Front Matter
- Markdown body
- Generation
- Validation
- Compatibility

## Ownership Boundary

Generate every BFF artifact as one reviewable Markdown file with three domains:

- **Business Contract** is backend-owned. It contains only HTTP method/path,
  request and response DTOs, backend errors, and business rules. Never add a
  field because a screen, Figma frame, route, or local state needs it.
- **UI Contract** is frontend-owned. It contains component `@FrState` model
  fields, behavior, and presentation structure. UI fields are never HTTP DTO
  fields unless the Business Contract independently declares the same wire
  field.
- **Integration Mapping** is frontend-owned. It maps UI/flow sources into
  request fields and backend responses/errors into UI behavior. A mapping may
  transform a value but cannot rename or redefine the backend field.

Treat field ownership as semantic rather than name-based. `business.mobile`
and `ui.mobileInput` may carry related values but remain different fields.

## YAML Front Matter

Use YAML Front Matter at the beginning of every generated `*.bff.md`. Do not
emit an HTML `BFF_META` comment, TOML metadata, or a Markdown-embedded metadata
code fence.

```yaml
---
bff_meta:
  schema: "bff-md-meta/v4"
  contract_version: "1.0.0"
  ui_revision: "1.0.0"
  mode: BFF-JSON
  contract_file: "lib/app/order_content/order_content.c.dart"
  authorities:
    business:
      owner: backend
    ui:
      owner: frontend
      source:
        type: figma
        url: "https://www.figma.com/design/..."
  apis:
    - method: POST
      route: "/orders"
      request: OrderContentBffReq
      response: OrderContentBffRsp
      behavior: command
---
```

Quote schema versions, paths, URLs, and other values that YAML could coerce.
Keep `contract_version` independent from `ui_revision`: transport changes bump
the former; UI-only changes bump the latter.

## Markdown Body

Render these top-level sections in order:

1. `Business Contract` authority notice.
2. Extracted `BFF-API` request/response JSON5 blocks.
3. `UI Contract` authority notice, UI state table, Behavior, and Widget Tree.
4. `Integration Mapping` authority notice and `Request Field Sources`.

The `UI State` table is derived from every model named in `Models:` and its
Freezed factory fields. It is descriptive frontend state, not a DTO schema.
The Retrofit generator must continue reading only endpoint and request JSON5
data from the Business Contract.

## Generation

1. Extract backend DTOs with `fr_acdd:extract_bff` into a temporary artifact.
2. Parse its endpoint identities and JSON5 shapes.
3. Wrap it with deterministic YAML Front Matter.
4. Read UI models, Behavior, Widget Tree, Figma, and Request Field Sources from
   the approved component contract.
5. Render Business, UI, and Mapping sections atomically.
6. Generate or check Retrofit from the Business Contract only.

Never copy raw Dart source or absolute local paths into the artifact.

## Validation

Require all generated BFF artifacts to satisfy these invariants:

- the file begins with `---` and contains `bff_meta.schema` equal to
  `bff-md-meta/v4`;
- `authorities.business.owner` is `backend` and `authorities.ui.owner` is
  `frontend`;
- every metadata API matches the approved `BFF-API` method, route, request,
  response, and inferred query/command behavior;
- every request/response field comes from an annotated BFF DTO;
- every UI state row comes from a declared component model;
- every request field has exactly one `Request Field Sources` mapping;
- UI fields never appear in transport DTOs merely to support presentation or
  navigation;
- stale checks compare the complete deterministic artifact.

## Compatibility

`bff-md-meta/v4` is a breaking artifact-format change. Existing backend field
semantics and Retrofit operation behavior remain compatible, but consumers
that parse the old HTML/TOML `BFF_META` block or assume `# Derived JSON5
Contract` is the first line must migrate to YAML Front Matter and the
Business/UI/Mapping sections.

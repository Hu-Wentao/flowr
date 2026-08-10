# Generic Source-First Validation

Validate an approved contract before deriving files:

```bash
uv run --script <skill-root>/scripts/validate_contract.py \
  --page-file path/to/xxx.page.dart --phase contract
uv run --script <skill-root>/scripts/validate_contract.py \
  --component-file path/to/xxx.dart --phase contract
```

This phase enforces `api-contract-semantics.md`: inferred query/command kind,
the applicable `Behavior` fields, request-field provenance, command success
evidence, failure recovery, the BFF Service declaration, rejection of
backend-owned API/flow sections from `.c.dart`, and invalid placeholder/path
rejection. It requires `.c.dart` contract sections to use consecutive `///`
documentation comments and rejects `/* ... */` contract blocks. It also
rejects Widget Tree TODOs, invalid typed Page route-field consumption,
incomplete Theme schema, invalid state/Provider placement, invalid BFF
declarations, missing public View implementations, and missing direct
dependencies. The draft already contains a marked `.v.dart` public-View stub;
contract validation does not require an applicable `.vm`, Theme
implementation, BFF output, or Freezed/JSON output.

After backend developers publish OpenAPI and maintain the backend section of
`xxx.bff.md`, implement `.srv.dart` as a `lib/api/gen` SDK adapter, then
implement `.vm.dart` and `.v.dart`. Regenerate `xxx.bff.md` afterward so its
mdq API query records carry current runtime evidence.

```bash
uv run --script <skill-root>/scripts/generate_bff.py \
  --component-file path/to/xxx.dart
uv run --script <skill-root>/scripts/validate_contract.py \
  --page-file path/to/xxx.page.dart --phase final
uv run --script <skill-root>/scripts/validate_contract.py \
  --component-file path/to/xxx.dart --phase final
fvm flutter analyze
```

The validator checks page-to-component linkage,
`XxxPage extends GoRouteData with $XxxPage`, absence of `PageArgs`, consumption
of Page route fields by the page ViewModel factory and/or ordinary View fields,
component `XxxArgs`/`XxxConfig`
wrappers, and sibling `.page.dart`/GoRouter references from component sources.
It also rejects a Page/Component module whose leaf directory contains another
module shell or `*.c.dart` contract with a different basename. Feature
directories may group modules only through separate child leaf directories.
It permits references to a different target Page adapter for typed navigation.
It also checks `XxxModel` state naming, component shell/part ownership, the
primary View inferred from `build`, the route inferred from `@TypedGoRoute`,
the authoritative `Public Views:` inventory across the component library, one
Widget Tree root per public View, and the declared state ownership:

- `page-owned [XxxViewModel]` requires the Provider in every typed Page variant,
  dispatches the optional declared `Startup Event`, and rejects a
  component-local Provider.
- `app-owned [AppViewModel]` and `none` reject local Provider, VM part, Event,
  and Model declarations.
- `component-owned [XxxViewModel]` requires a View-owned Provider as an
  explicit exception.

Remove `.page.dart` only for `app-owned`, `none`, or explicit
`component-owned` components, then run the repository analyzer to verify
standalone compilation. Page-owned components intentionally require their
page adapter for lifecycle creation. Run Dart formatting, build_runner, and
the repository analyzer after derived Dart files change.

Final validation additionally requires every declared Dart part to exist,
requires `.freezed.dart` and `.g.dart` for JSON-enabled FrState models, and
rejects unfinished `.v` or applicable `.vm` generated stubs. It does not
replace the repository analyzer. Omitting `--phase` preserves the source
validation entry for compatibility and must not be treated as the final
completion gate.

For BFF-JSON, final validation also proves the
referenced Dart service class, ViewModel injection, asynchronous registered handler,
request construction, awaited service call, response-backed state, failure
state, loading/submitting recovery, and absence of navigation before the
successful response. A component service must import at least one concrete SDK
from `lib/api/gen`, must not declare `@RestApi`, and must be imported by the
component shell. Contract-only BFF delivery cannot skip this runtime gate.

The generator never creates or overwrites `.srv.dart`. A request type may use
an exact semantic `typedef`; response signatures use the original SDK type by
default.

For BFF-JSON, final validation additionally requires `xxx.bff.md`, exactly one
`@FrAcddPage(mode: FrAcddMode.bff)`, at least one root DTO, JSON Freezed DTOs
with `fromJson`, direct `fr_acdd` ownership, resolvable request/response DTO
references named `XxxBffReq`/`XxxBffRsp` in `BFF-API:`, an explicit
`Map<String, dynamic> toJson();` declaration on every request DTO, internal
`XxxDto` names, one component SDK-adapter Service, and a clean
`generate_bff.py --check`. Missing, stale, or unexecutable extractor output
fails validation. A new or migrated artifact must begin with compact
`bff-md-meta/v8` YAML Front Matter containing schema, namespace, the
annotation-owned contract version, and UI source, then separate the inline UI
API Contract, backend-owned business APIs and flow, frontend-owned UI Contract,
and Integration Mapping as defined in `bff-dual-authority.md`. Backend API
annotations retain only method/path, parameter and response type names, and
flow; they never contain DTO fields. Explicit API mode does not require a BFF
file.

Migrate v7 artifacts through backend review; frontend tooling must not
automatically translate or overwrite the old backend call list and flow.

For route refactors and cross-page modules, resolve the separate
`validate_routes` task and run `validate_routes.py --module-file ...`. It
validates module documentation, target-owned PageExtra declarations, `$extra`
types, Freezed/JSON generation shape, application route-extra codec coverage,
field inventory, Page-to-View expansion, and absence of PageExtra state inside
the target component.

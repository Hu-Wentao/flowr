# Generic Source-First Validation

Validate an approved contract before deriving files:

```bash
uv run python <skill-root>/scripts/validate_contract.py \
  --page-file path/to/xxx.page.dart --phase contract
uv run python <skill-root>/scripts/validate_contract.py \
  --component-file path/to/xxx.dart --phase contract
```

This phase enforces `api-contract-semantics.md`: API type, the applicable Data
or Business section, request-field provenance, business success evidence,
failure recovery, optional generated BFF service class, and invalid placeholder/path
rejection. It requires `.c.dart` contract sections to use consecutive `///`
documentation comments and rejects `/* ... */` contract blocks. It also
rejects Widget Tree TODOs, invalid PageArgs conversion, incomplete Theme
schema, invalid BFF declarations, and missing direct dependencies. It does not
require `.v/.vm`, Theme implementation, BFF output, or Freezed/JSON output.

After generating an optional component Retrofit `.srv.dart`, run build_runner
to produce `.srv.g.dart`, then implement `.vm.dart` and `.v.dart`. Run
formatting before the final gate:

```bash
uv run python <skill-root>/scripts/validate_contract.py \
  --page-file path/to/xxx.page.dart --phase final
uv run python <skill-root>/scripts/validate_contract.py \
  --component-file path/to/xxx.dart --phase final
fvm flutter analyze
```

The validator checks page-to-component linkage, route-owned `XxxPageArgs`
declaration and expansion into ordinary View fields, absence of `PageArgs`,
component `XxxArgs`/`XxxConfig` wrappers, and `.page.dart` references from
component sources, `XxxModel` state naming, component shell/part ownership, the
primary View marker, and the View-owned Provider requirement. Remove `.page.dart` and run
the repository analyzer against the component library to verify standalone
compilation. Run Dart formatting, build_runner, and the repository analyzer
after derived Dart files change.

Final validation additionally requires every declared Dart part to exist,
requires `.freezed.dart` and `.g.dart` for JSON-enabled FrState models, and
rejects unfinished `.v/.vm` generated stubs. It does not replace the repository
analyzer. Omitting `--phase` preserves the previous source-validation behavior
for compatibility and must not be treated as the final completion gate.

When `BFF Service` is declared, final validation also proves the
referenced Dart service class, ViewModel injection, asynchronous registered handler,
request construction, awaited service call, response-backed state, failure
state, loading/submitting recovery, and absence of navigation before the
successful response. A component service additionally requires direct `dio`,
`efficient_dio_logger`, and `retrofit` runtime dependencies, `build_runner`
and `retrofit_generator` dev dependencies, the component shell import, and
generated `.srv.g.dart`.
Omitting it selects contract-only delivery and skips this runtime gate.

Do not compare `.srv.dart` against its initial generated template or require a
generator marker. After first generation it is project code and may customize
Retrofit parameters, annotations, headers, and bodies.

For BFF-JSON, final validation additionally requires `xxx.bff.md`, exactly one
`@FrAcddPage(mode: FrAcddMode.bff)`, at least one root DTO, JSON Freezed DTOs
with `fromJson`, direct `fr_acdd` ownership, resolvable request/response DTO
references named `XxxBffReq`/`XxxBffRsp` in `BFF-API:`, internal `XxxDto`
names, and a clean `generate_bff.py --check`. Missing,
stale, or unexecutable extractor output fails validation. Explicit API mode
does not require or generate a BFF file.

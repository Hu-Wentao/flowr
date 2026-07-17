# Generic Source-First Validation

Validate an approved contract before deriving files:

```bash
uv run python <skill-root>/scripts/validate_contract.py \
  --page-file path/to/xxx.page.dart --phase contract
uv run python <skill-root>/scripts/validate_contract.py \
  --component-file path/to/xxx.dart --phase contract
```

This phase rejects Widget Tree TODOs, draft `pendingRequestField` /
`pendingResponseField` values, invalid PageArgs conversion, incomplete Theme
schema, invalid BFF declarations, and missing direct dependencies. It does not
require `.v/.vm`, Theme implementation, BFF output, or Freezed/JSON output.

After implementing optional `.srv.dart`, then `.vm.dart`, then `.v.dart`, run
formatting and build_runner before the final gate:

```bash
uv run python <skill-root>/scripts/validate_contract.py \
  --page-file path/to/xxx.page.dart --phase final
uv run python <skill-root>/scripts/validate_contract.py \
  --component-file path/to/xxx.dart --phase final
fvm flutter analyze
```

The validator checks page-to-component linkage, route-owned `XxxPageArgs`
declaration and conversion, absence of `PageArgs` and `.page.dart` references
from component sources, component shell/part ownership, the primary View
marker, and the View-owned Provider requirement. Remove `.page.dart` and run
the repository analyzer against the component library to verify standalone
compilation. Run Dart formatting, build_runner, and the repository analyzer
after derived Dart files change.

Final validation additionally requires every declared Dart part to exist,
requires `.freezed.dart` and `.g.dart` for JSON-enabled FrState models, and
rejects unfinished `.v/.vm` generated stubs. It does not replace the repository
analyzer. Omitting `--phase` preserves the previous source-validation behavior
for compatibility and must not be treated as the final completion gate.

For BFF-JSON, final validation additionally requires `xxx.bff.md`, exactly one
`@FrAcddPage(mode: FrAcddMode.bff)`, at least one root DTO, JSON Freezed DTOs
with `fromJson`, direct `fr_acdd` ownership, resolvable request/response DTO
references in `BFF-API:`, and a clean `generate_bff.py --check`. Missing,
stale, or unexecutable extractor output fails validation. Explicit API mode
does not require or generate a BFF file.

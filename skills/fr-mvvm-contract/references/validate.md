# Generic Source-First Validation

Validate one supported runtime entry:

```bash
uv run python <skill-root>/scripts/validate_contract.py \
  --page-file path/to/xxx.page.dart
uv run python <skill-root>/scripts/validate_contract.py \
  --component-file path/to/xxx.dart
```

The validator checks page-to-component linkage, route-owned `XxxPageArgs`
declaration and conversion, absence of `PageArgs` and `.page.dart` references
from component sources, component shell/part ownership, the primary View
marker, and the View-owned Provider requirement. Remove `.page.dart` and run
the repository analyzer against the component library to verify standalone
compilation. Run Dart formatting, build_runner, and the repository analyzer
after derived Dart files change.

For BFF-JSON it additionally requires `xxx.bff.md`, exactly one
`@FrAcddPage(mode: FrAcddMode.bff)`, at least one root DTO, JSON Freezed DTOs
with `fromJson`, direct `fr_acdd` ownership, resolvable request/response DTO
references in `BFF-API:`, and a clean `generate_bff.py --check`. Missing,
stale, or unexecutable extractor output fails validation. Explicit API mode
does not require or generate a BFF file.

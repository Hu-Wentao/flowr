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

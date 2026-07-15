# Generic Source-First Validation

Validate one supported runtime entry:

```bash
uv run python .agents/skills/fr-mvvm-contract/scripts/validate_contract.py \
  --page-file path/to/xxx.page.dart
uv run python .agents/skills/fr-mvvm-contract/scripts/validate_contract.py \
  --component-file path/to/xxx.dart
```

The validator checks page-to-component linkage, component shell/part ownership,
the primary View marker, and the View-owned Provider requirement. Run Dart
formatting, build_runner, and the repository analyzer after derived Dart files
change.

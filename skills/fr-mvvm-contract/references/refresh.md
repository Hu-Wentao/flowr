# Generic Contract Refresh

Use this fallback when derived artifacts need to be regenerated from contract
files.

## Workflow

1. Re-read the contract Dart file before refreshing derived files.
2. In BFF-JSON mode, regenerate the component-owned BFF artifact with the
   generic generator. A project profile may override the command, but may not
   make BFF delivery optional.
3. Regenerate Freezed/JSON code when models, annotations, or parts changed.
4. Re-run validation after refresh.

## Commands

```bash
uv run python <skill-root>/scripts/generate_bff.py \
  --component-file path/to/xxx.dart
fvm dart run build_runner build --delete-conflicting-outputs
fvm flutter analyze
```

Extractor preflight failure, including `fr_acdd`/analyzer incompatibility, is a
refresh failure; never silently skip BFF generation.

# Generic Contract Refresh

Use this fallback when derived artifacts need to be regenerated from contract
files.

## Workflow

1. Re-read the contract Dart file before refreshing derived files.
2. Regenerate Freezed/JSON code when models, annotations, or parts changed.
3. Refresh BFF or API artifacts only when the active project profile provides
   a command for them.
4. Re-run validation after refresh.

## Commands

```bash
fvm dart run build_runner build --delete-conflicting-outputs
fvm flutter analyze
```

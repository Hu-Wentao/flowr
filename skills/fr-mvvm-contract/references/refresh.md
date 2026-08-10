# Generic Contract Refresh

Use this fallback when derived artifacts need to be regenerated from contract
files.

## Workflow

1. Re-read the contract Dart file and run contract-phase validation before
   refreshing derived files. This revalidates UI API semantics, request
   provenance, every backend OpenAPI method/path reference and call flow, and
   required service scope; refresh must not preserve a semantically incomplete
   contract.
2. In BFF-JSON mode, refresh only the frontend-owned BFF content with the
   generic Python generator while preserving the backend-owned section
   byte-for-byte. It never creates or overwrites `.srv.dart`.
3. Run build_runner to regenerate Freezed/JSON code
   when models, annotations, or parts changed.
4. Run final-phase validation and the repository analyzer after refresh. Final
   validation must still prove the actual service call and state/error recovery
   path.
5. When preparing project-wide backend delivery, resolve `package_bff` and run
   its `package` command after all component BFF artifacts are current. Run an
   optional project `sync` command only with explicit authorization.

## Commands

```bash
uv run --script <skill-root>/scripts/validate_contract.py \
  --component-file path/to/xxx.dart --phase contract
uv run --script <skill-root>/scripts/generate_bff.py \
  --component-file path/to/xxx.dart
fvm dart run build_runner build
uv run --script <skill-root>/scripts/validate_contract.py \
  --component-file path/to/xxx.dart --phase final
fvm flutter analyze
```

Extractor preflight failure, including `fr_acdd`/analyzer incompatibility, is a
refresh failure; never silently skip BFF generation.

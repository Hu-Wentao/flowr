# Generic Contract Refresh

Use this fallback when derived artifacts need to be regenerated from contract
files.

## Workflow

1. Run `ensure_fr_acdd.py` for the owning package. Require the resolved
   `fr_acdd >= 0.7.0` and allow its default automatic Pub upgrade attempt;
   path/git sources that remain old require an explicit source update.
2. Re-read the contract Dart file and run contract-phase validation before
   refreshing derived files. This revalidates endpoint Behaviors, scoped
   request provenance, every frontend interaction Flow, and required Service
   scope. Backend OpenAPI annotations and call flow remain owned exclusively by
   the protected BFF Markdown domain; refresh validates but never rewrites it.
3. In BFF-JSON mode, refresh only the frontend-owned BFF content with the
   generic Python generator while preserving the backend-owned section
   byte-for-byte. It never creates or overwrites `.srv.dart`.
4. Run build_runner to regenerate Freezed/JSON code
   when models, annotations, or parts changed.
5. Run final-phase validation and the repository analyzer after refresh. Final
   validation must prove every Flow's exact handler, API/local operation,
   state phases, concurrency policy, and navigation timing.
6. When preparing project-wide backend delivery, resolve `package_bff` and run
   its `package` command after all component BFF artifacts are current. Run an
   optional project `sync` command only with explicit authorization.

## Commands

```bash
uv run --script <skill-root>/scripts/ensure_fr_acdd.py \
  --project-root path/to/owning/package
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

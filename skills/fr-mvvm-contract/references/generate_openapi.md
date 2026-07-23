# OpenAPI Retrofit Generation

Generate backend-owned Retrofit APIs and JSON DTOs from checked-out
`.openapi.json` documents with:

```bash
uv run python .agents/skills/fr-mvvm-contract/scripts/openapi_to_retrofit.py \
  --source docs/openapi --output lib/api/gen
```

Run the command from the consuming repository root. The generator reads
`.agents/skills-config/fr-mvvm-contract/config.yaml` and remains deterministic
for unchanged OpenAPI documents and project configuration.

## Generic wrappers

Projects may declare stable request or response wrapper conventions without
putting project fields in the reusable skill:

```yaml
transport:
  backend_openapi:
    local_root: docs/openapi
    dart_codegen:
      generic_wrappers:
        request:
          dart_name: ReqWrapper
          schema_glob: StandardRequest*
          type_parameter_field: data
        response:
          dart_name: RspWrapper
          schema_glob: Response*
          type_parameter_field: data
```

Each rule selects OpenAPI component schemas by glob. The configured field is
the complete generic type slot and may contain an object reference, scalar,
array, map, or null schema. The generator derives every other field from the
matched schemas and emits one `dart_name<T>` per generated Dart library.

All schemas matched by one rule must be identical after replacing the complete
configured field schema with `T`. This comparison retains requiredness,
nullability, formats, item shapes, and all other wire-significant constraints,
while ignoring descriptions, titles, examples, and deprecation prose. Fail on
structural drift, overlapping rules, unsupported configuration, or Dart-name
collisions; never silently fall back to duplicate classes for a configured
rule.

Without `generic_wrappers`, preserve one generated Dart class per OpenAPI
schema. Preserve every OpenAPI schema name and every already-valid Dart field
identifier exactly; the OpenAPI document is authoritative. Do not substitute a
more convenient domain or UI name. Configured generic request and response
wrappers are the only schema-name exception. A downstream compatibility name
may only be a Dart `typedef` alias of the generated type; it must not copy or
translate fields. Use `--check` to detect generation drift without writing
files. After generation, run build_runner so Retrofit and json_serializable
regenerate their parts, then run the repository analyzer.

When `--source` is a directory, treat its `.openapi.json` files as the complete
SDK source set. Report generated SDK declarations and build-runner parts whose
OpenAPI source was renamed or removed as drift, and remove those stale files
during generation. Preserve non-generated files and do not prune other SDKs
when `--source` names one OpenAPI file.

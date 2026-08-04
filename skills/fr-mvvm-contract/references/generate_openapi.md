# OpenAPI Retrofit Generation

Generate backend-owned Retrofit APIs and JSON DTOs from checked-out
`.openapi.json` documents with:

```bash
uv run --script .agents/skills/fr-mvvm-contract/scripts/openapi_to_retrofit.py \
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
          missing_type_parameter_field: optional
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
rule. The default `missing_type_parameter_field: reject` requires every matched
schema to contain the generic field. Use `optional` only when the transport
contract deliberately omits that non-required field for void payloads; those
schemas generate the same nullable generic field and use `dynamic` as their
concrete payload type.

## Operation parameters

Resolve local `#/components/parameters/*` references before generating Retrofit
arguments. Unresolved or external parameter references are generation errors.
Required parameters remain positional; non-required parameters become optional
named Dart arguments.

Projects may declare headers that are always injected by their Dio interceptors:

```yaml
transport:
  backend_openapi:
    dart_codegen:
      interceptor_owned_headers:
        tenant_id: Tenant-ID
        access_token: Access-Token
```

The mapping keys are project-owned labels and the values are exact wire header
names. Do not expose those headers on generated SDK methods. Preserve all other
inline or referenced headers, including operation-specific authorization
tokens. Without this configuration, expose every OpenAPI operation parameter.

Without `generic_wrappers`, preserve one generated Dart class per OpenAPI
schema. Preserve every OpenAPI schema name and every already-valid Dart field
identifier exactly; the OpenAPI document is authoritative. Do not substitute a
more convenient domain or UI name. Configured generic request and response
wrappers are the only schema-name exception. A downstream compatibility name
may only be a Dart `typedef` alias of the generated type; it must not copy or
translate fields. Generate every property named by the schema's `required`
array as a non-nullable Dart field and a `required this.field` named constructor
parameter; keep other properties nullable and optional. Apply the same rule to
configured generic wrappers, including their type-parameter field. Treat
component schemas that contain only `additionalProperties` as typed Dart map
aliases so their arbitrary wire keys survive JSON conversion. Treat
configured wrappers as transport details in consuming Services. When a typed
map is the direct payload of a configured generic wrapper, emit a map-compatible
class with `fromJson` instead of a typedef because Retrofit must invoke that
factory while decoding the generic payload; preserve the same `Map<String, T>`
interface and wire shape. When an operation needs only the business payload,
accept the generated payload type
and construct the wrapper internally. Use `--check` to detect generation drift
without writing files. After generation, run build_runner so Retrofit and
json_serializable regenerate their parts, then run the repository analyzer.

Preserve OpenAPI prose as Dart `///` documentation comments. Use `info.title`
and `info.description` for the generated API class, operation `summary` and
`description` for methods, parameter and request-body descriptions for their
arguments, and schema `title`/`description` plus property descriptions for DTOs,
generic wrappers, and map aliases. Skip absent or blank prose without inventing
fallback text.

When `--source` is a directory, treat its `.openapi.json` files as the complete
SDK source set. Report generated SDK declarations and build-runner parts whose
OpenAPI source was renamed or removed as drift, and remove those stale files
during generation. Preserve non-generated files and do not prune other SDKs
when `--source` names one OpenAPI file.

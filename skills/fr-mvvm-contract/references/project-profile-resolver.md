# Project Profile Runtime Reference

This is runtime reference material for `fr-mvvm-contract`. It describes how a
task resolves project configuration and how the resolved instructions are used.
This reference and `bff-dual-authority.md` define the current runtime behavior;
historical implementation plans are not runtime authority.

## Resolver

Before every contract task, run:

```bash
uv run python <skill-root>/scripts/resolve.py --task <task>
```

Supported tasks are `adapt_project`, `gen_page`, `gen_component`, `validate`,
`refresh`, `package_bff`, and `generate_openapi`.
The default result is a small manifest. Read `instructions.path` once for a new
`instructions_id`; reuse it for subsequent calls with the same id.

The resolver loads generic references from its own skill directory (including
an installed `.agents/skills/fr-mvvm-contract/` copy when present) and optional tracked project rules from
`.agents/skills-config/fr-mvvm-contract/`. Cache files belong under
`.agents/.cache/fr-mvvm-contract/` and are not tracked.

`skills-config` is a repository-owned sibling of `skills`. Profile rules may
add instructions and commands, but resolution must not execute arbitrary
profile code. Resolver output is deterministic for unchanged input files.

## Contract Description Language

Project config may select the language used for descriptive contract values:

```yaml
schema: fr-mvvm-contract.config.v1
profile: example
contract:
  description_language: zh-CN
tasks:
  gen_component:
    base: references/gen_component.md
```

`contract.description_language` accepts any non-empty language tag or name,
such as `zh-CN`, `English`, or `简体中文`, and defaults to `English` when
omitted. It affects Data and Business entries, Request Field Sources purpose
prose, and Notes. Stable labels, identifiers, types, HTTP methods and paths,
enum literals, code references, and authoritative source expressions remain
unchanged. The resolved language appears in the manifest and participates in
`instructions_id` generation.

## Runtime Base URL Ownership

Do not put a `service` section or base URL in project skill config. The
application environment model owns `apiBaseUrl`; `createAppDio(AppEnv)` applies
it through `BaseOptions`, and SDK adapters pass that Dio to concrete generated
clients from `lib/api/gen`. The resolver rejects obsolete
`service.base_url` config so environment ownership cannot silently split
between generation time and runtime.

## Request And BFF Envelope Profiles

Projects whose gateway requires a top-level request `data` property may opt in
without changing every business DTO:

```yaml
transport:
  request_data_envelope:
    mode: interceptor
    retrofit_extra:
      key: requestDataEnvelopeExtra
      import: package:example/core/interceptors/request_data_envelope_interceptor.dart
```

The profile selects a non-GET root `XxxRequestDto` explicitly. The service
generator imports the configured symbol and adds `@Extra` to that Retrofit
operation; the project-owned interceptor alone wraps its JSON object as
`{data: payload}` before encryption. Existing `XxxBffReq` operations retain
their backend-defined top-level shape and are never wrapped by convention.

If BFF contracts must describe the complete gateway response rather than only
its original business value, configure its outer fields too:

```yaml
transport:
  bff_response_envelope:
    state_field: state
    code_field: code
    message_field: message
    data_field: data
```

Every profiled `XxxBffRsp` must contain these fields. The original BFF response
definition belongs under `data` (normally as a nested `XxxDto`); BFF Markdown
therefore shows `{state, code, message, data}` as the response shape. This is a
contract convention, not a response interceptor: Retrofit still deserializes
the declared `XxxBffRsp` directly.

## Backend OpenAPI Authority Root

By default, local `.openapi.json` references resolve from the project root. A
project whose OpenAPI authority is checked out elsewhere inside the repository
may configure that checkout's publication root:

```yaml
transport:
  backend_openapi:
    local_root: build/api-docs/api/app-backend
```

`local_root` must be repository-relative and cannot escape the repository.
Author BFF locations relative to that root, such as
`openapi/assisted_onboarding.openapi.json`; never write the checkout path into
the BFF contract. Validation reads the configured checkout or an HTTP(S) URL.
Packaging and synchronization retain only the reference and never copy,
delete, or stage the independently owned OpenAPI document.

## OpenAPI Dart Generic Wrappers

`transport.backend_openapi.dart_codegen.generic_wrappers` is a mapping of
project-owned wrapper rules. Each rule declares `dart_name`, `schema_glob`, and
`type_parameter_field`. The OpenAPI Retrofit generator derives all remaining
fields from the matching schemas and rejects structural drift outside the
generic field. Read `generate_openapi.md` before configuring or running this
generation task.

## Runtime Contract Layout

Place route-owned component libraries under `lib/app/<route-segment>/`. Place
component libraries reused by multiple routes under
`lib/components/<component-name>/`. Preserve established equivalent roots in
existing projects unless an approved adaptation moves them.

Keep a Widget used only by one component private in `.v.dart`. Put a plain
Widget reused inside one route under `lib/app/<route-segment>/widgets/`; put a
plain Widget reused by multiple routes under `lib/widgets/`. Plain Widgets do
not receive a component contract, Provider, Event, or ViewModel.

`gen_component` works with one independent component library:

```text
xxx.dart
xxx.c.dart
xxx.v.dart
xxx.vm.dart
xxx.srv.dart       # SDK adapter over lib/api/gen
xxx.bff.md         # required in BFF-JSON mode
```

`xxx.dart` owns imports and part declarations. Its parts use
`part of 'xxx.dart';` and declare no imports.
`xxx.srv.dart` is a separate library imported by `xxx.dart`; it imports
concrete generated SDKs, consumes the application-provided `Dio` without
modifying its interceptors. The root
Provider owns shared interceptor registration.

`gen_page` adds an optional independent route adapter:

```text
xxx.page.dart
```

The adapter imports `xxx.dart`; it is never a part. It declares a
basename-matching public `XxxPage extends GoRouteData with $XxxPage` typed route
entry. The route is read from `@TypedGoRoute`, and the primary View is read
from the direct construction in `XxxPage.build`, without duplicate doc
markers. It may add Page variants for other URLs only when they build that
same primary View.

`XxxPage` constructor fields are the only route inputs; `XxxPageArgs` is
forbidden. The Page expands route fields into ordinary named `XxxView` fields;
component input wrapper classes are forbidden.
`XxxView`, Events, ViewModel, models, BFF/service artifacts, component inputs,
and contract facts belong to the component library. The component library
never references `XxxPage`, GoRouter types, or imports `.page.dart`. Component interaction
uses Bloc Events only: do not add Intent or callback protocols.

## Contract Read Gate

Outside explicit contract drafting, editing, or review, read contract facts
through scripts before making module decisions:

```bash
uv run python <skill-root>/scripts/read_contract.py \
  --page-file path/to/xxx.page.dart
uv run python <skill-root>/scripts/read_contract.py \
  --component-file path/to/xxx.dart
```

The page form aggregates route facts with component facts. The component form
remains valid after deleting `.page.dart`.

## Runtime Flow

1. Read Figma, shared component and Widget catalogs, and API context. Default
   to BFF-JSON without a concrete API. Only explicit API mode may omit BFF.
2. Select `lib/app/<route-segment>/` for route-owned code or
   `lib/components/<component-name>/` for cross-route reuse.
3. Select `lib/app/<route-segment>/widgets/` for route-owned shared Widgets or
   `lib/widgets/` for cross-route shared Widgets.
4. Read `api-contract-semantics.md`; draft only the page adapter when needed,
   the component shell, and `.c.dart` with invalid semantic placeholders.
5. Classify the UI API, complete `Behavior`, trace BFF request fields, resolve
   downstream `.openapi.json` method/path references and call flow, and
   reference the required generated BFF service class before DTO derivation.
6. Present the UI API semantics and backend call flow with typed Page route fields and Widget Tree for user approval
   unless an active goal continues.
7. Replace every pending marker, then run `validate_contract.py --phase
   contract`.
8. Read the approved contract through `read_contract.py`.
9. Prepare the rollback-protected derived file set with
   `generate_from_contract.py`, which must also generate `xxx.bff.md` in
   BFF-JSON mode.
10. For the required `BFF Service: [Type]`, implement `xxx.srv.dart` as a
    `lib/api/gen` SDK adapter after backend developers maintain the BFF flow.
    Then implement `.vm.dart` and `.v.dart`, and run
    `validate_contract.py --phase final` and the repository analyzer before
    route registration. Contract-only BFF delivery is not supported.

The generic workflow always provides `generate_bff.py`; project commands may
override its invocation but cannot turn BFF generation or stale checking into
an optional step.

After project BFF artifacts are current, resolve `package_bff`. Its generic
`package` command creates `build/bff-contracts.zip` containing only BFF
Markdown. A project task may
override `package` and add a declarative `sync` command under
`tasks.package_bff.commands`. Resolver output never executes either command;
obtain explicit authorization before a sync mutates another repository.

```yaml
tasks:
  package_bff:
    base: references/package_bff.md
    profile: package_bff.md
    commands:
      package: uv run python .agents/skills/fr-mvvm-contract/scripts/package_bff.py --project-root . --output build/bff-contracts.zip
      sync: ./tool/sync_bff_contracts.sh build/bff-contracts.zip
```

No persistent JSON spec is part of this runtime flow.

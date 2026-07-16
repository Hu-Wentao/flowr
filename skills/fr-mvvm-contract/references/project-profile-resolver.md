# Project Profile Runtime Reference

This is runtime reference material for `fr-mvvm-contract`. It describes how a
task resolves project configuration and how the resolved instructions are used.
Architecture decisions, migration phases, and implementation work belong in
`contract-first-refactor-plan.md`.

## Resolver

Before every contract task, run:

```bash
uv run python <skill-root>/scripts/resolve.py --task <task>
```

Supported tasks are `gen_page`, `gen_component`, `validate`, and `refresh`.
The default result is a small manifest. Read `instructions.path` once for a new
`instructions_id`; reuse it for subsequent calls with the same id.

The resolver loads generic references from its own skill directory (including
an installed `.agents/skills/fr-mvvm-contract/` copy when present) and optional tracked project rules from
`.agents/skills-config/fr-mvvm-contract/`. Cache files belong under
`.agents/.cache/fr-mvvm-contract/` and are not tracked.

`skills-config` is a repository-owned sibling of `skills`. Profile rules may
add instructions and commands, but resolution must not execute arbitrary
profile code. Resolver output is deterministic for unchanged input files.

## Runtime Contract Layout

Place route-owned component libraries under `lib/app/<route-segment>/`. Place
component libraries reused by multiple routes under
`lib/components/<component-name>/`. Preserve established equivalent roots in
existing projects unless an approved adaptation moves them.

`gen_component` works with one independent component library:

```text
xxx.dart
xxx.c.dart
xxx.v.dart
xxx.vm.dart
xxx.srv.dart       # optional
xxx.bff.md         # optional
```

`xxx.dart` owns imports and part declarations. Its parts use
`part of 'xxx.dart';` and declare no imports.

`gen_page` adds an optional independent route adapter:

```text
xxx.page.dart
```

The adapter imports `xxx.dart`; it is never a part. It declares one primary
`/// Component: [XxxView]` marker and one public `XxxPage` route widget.
The marker identifies the direct view, not every nested component.

`XxxView` owns its `FrProvider` and startup Event. `XxxPageArgs`, Events,
ViewModel, models, BFF/service artifacts, and contract facts belong to the
component library. Component interaction uses Bloc Events only: do not add
Intent or callback protocols.

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

1. Read Figma, shared component catalogs, and API context. Default to BFF
   without a concrete API.
2. Select `lib/app/<route-segment>/` for route-owned code or
   `lib/components/<component-name>/` for cross-route reuse.
3. Draft only the page adapter when needed, the component shell, and `.c.dart`.
4. Stop for user approval unless an active goal continues.
5. Read the approved contract through `read_contract.py`.
6. Prepare derived parts with `generate_from_contract.py`, then implement
   `.v.dart`, `.vm.dart`, and optional `.srv.dart`.

No persistent JSON spec is part of this runtime flow.

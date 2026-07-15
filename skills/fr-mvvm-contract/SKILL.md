---
name: fr-mvvm-contract
description: Create, validate, and evolve FlowR component contracts and their optional page route adapters.
---

# FR MVVM Contract

Before contract work, run:

```bash
uv run python .agents/skills/fr-mvvm-contract/scripts/resolve.py --task <gen_page|gen_component|validate|refresh>
```

Read the resolved instructions once per `instructions_id`.

## Source-First Layout

A reusable feature component is one Dart library:

```text
order_content/
  order_content.dart
  order_content.c.dart
  order_content.v.dart
  order_content.vm.dart
  order_content.srv.dart       # optional
  order_content.bff.md         # optional
```

`order_content.dart` owns all imports and part declarations. Its `.c.dart`,
`.v.dart`, and `.vm.dart` files use `part of 'order_content.dart';` and never
declare imports.

A page is that component plus an optional, independent route adapter:

```text
order_content.page.dart
```

The adapter imports `order_content.dart`; it is never a `part` of it. Deleting
the adapter must leave the component library usable by another page, sheet,
tab, or dialog.

## Naming And Ownership

- `XxxPage` lives in `xxx.page.dart` and owns only route entry and conversion
  from route parameters to component-owned `XxxPageArgs`.
- `XxxView` is the public component entry and lives in the component library.
  It creates its own `FrProvider` and dispatches its startup Event.
- `XxxViewModel extends FrBlocViewModel<XxxEvent, XxxModel>` lives in
  `.vm.dart`; all external writes use `add(event)`.
- `XxxPageArgs`, models, DTOs, Events, BFF/service declarations, and the
  component contract belong to the component library, never to `.page.dart`.
- Do not generate Intent or callback output protocols. Component interactions
  use the Bloc Event hierarchy. Follow the project's established navigation
  mechanism from Event handlers.
- A View-owned Provider creates an independent VM lifecycle per embedding.
  Use it for feature components with independent state/API ownership; pure
  presentation subcomponents do not receive a VM.

## Page Contract

`xxx.page.dart` declares one direct route-to-view adapter:

```dart
/// Route: AppRoutes.orderContent
/// Component: [OrderContentView]
class OrderContentPage extends StatelessWidget { /* route args -> view args */ }
```

This marker identifies the primary View only. The primary View may compose any
number of public/shared components recorded in `Components:`; it does not
limit a page to one component.

## Contract-First Workflow

1. Inspect Figma, shared component catalogs, nearby usage, and API context.
   Default to BFF when no concrete API is supplied.
2. For `gen_page`, draft `xxx.page.dart`, `xxx.dart`, and `xxx.c.dart` only:

```bash
uv run python .agents/skills/fr-mvvm-contract/scripts/draft_contract.py \
  --name order_content --dir lib/pages/order_content \
  --figma-url <url> --api BFF-JSON --route <route>
```

   Use `--component-only` for `gen_component`.
3. Keep the approval contract minimal: Figma, API/BFF, state ownership,
   components, widget tree, theme, Event and ViewModel references, models, and
   concise notes. Page Support contains only route and primary View facts.
4. Stop for user review unless an active goal continues without interruption.
5. For all non-contract work, read the contract through scripts rather than
   manually deriving decisions from raw Dart:

```bash
uv run python .agents/skills/fr-mvvm-contract/scripts/read_contract.py \
  --page-file path/to/xxx.page.dart
uv run python .agents/skills/fr-mvvm-contract/scripts/read_contract.py \
  --component-file path/to/xxx.dart
```

6. Prepare derived parts only from the approved reader output:

```bash
uv run python .agents/skills/fr-mvvm-contract/scripts/generate_from_contract.py \
  --page-file path/to/xxx.page.dart --write-stubs
```

Then implement concrete `.v.dart`, `.vm.dart`, and optional `.srv.dart` code.
Do not create or persist a JSON spec file.

## Validation

- A component must not import or reference its sibling `.page.dart` adapter.
- `read_contract.py --component-file` must work after removing `.page.dart`.
- A page adapter must import its sibling component library and declare exactly
  one `/// Component: [XxxView]` marker.
- `xxx.bff.md` and `xxx.srv.dart` are component assets, not page assets.
- Use `@FrState` / `@FrStateJson` Freezed models; keep model/view helpers and
  Event handlers in `.vm.dart`.
- Format changed Dart files, run build_runner when generated parts change, and
  run the repository analyzer command.

## Breaking Change

This replaces the old JSON-first `new_page.py --spec-file` workflow and the
single `xxx_page.dart` contract layout. No compatibility mode is provided.

---
name: fr-mvvm-contract
description: >-
  Create or migrate FlowR Flutter pages to a contract-first MVVM layout with
  `xxx_page.dart` or `xxx_view.dart` plus their `.v.dart` and `.vm.dart`
  parts. This skill is bloc-only: it generates `FrBlocViewModel`, contract
  comments, and view widgets from a structured page spec.
---

# Fr Contract MVVM

Create or update FlowR pages in a contract-first layout. The contract file is
the entry and overview; the view and view-model live in `part` files.

Generated naming supports two modes:

- `page` (default): `foo_page.dart`, `FooPage`, `_FooPageView`,
  `FooPageViewModel`, `FooPageEvent`, `FooPageModel`
- `view`: `foo_view.dart`, `FooView`, `_FooViewBody`, `FooViewModel`,
  `FooEvent`, `FooModel`

This skill is intentionally strict:

- Only generate `FrBlocViewModel<GeneratedEvent, GeneratedModel>`.
- Generate page models with `@freezed`, not handwritten `copyWith`.
- Do not add `FrViewModel` / method-mode content here.
- First let the AI analyze the page and write a structured spec.
- Then pass that spec to the Python generator to produce the final Dart files.

Use the installed `flowr-usage` skill first for Flutter-facing API semantics.
If event semantics or shared FlowR behavior matter, load
`skills/flowr-dart-usage/SKILL.md` before `skills/flowr-usage/SKILL.md`.
If the target project does not already have `freezed` installed, load
`skills/flowr-dart-usage/references/freezed-install.md` before scaffolding the
page.

## Scaffolding Requirements

- Run `skills/fr-mvvm-contract/scripts/new_page.py` with
  `--spec-file <json>`.
- The generator produces:
  - `XxxPage` or `XxxView`
  - `_XxxPageView` or `_XxxViewBody`
  - a generated `FrBlocViewModel<...>` subclass
  - one generated sealed event base class
  - one generated primary `@freezed` model
- Generated contract files include:
  - `import 'package:freezed_annotation/freezed_annotation.dart';`
  - `part '<contract_name>.freezed.dart';`
- Target project runtime deps need `freezed_annotation`.
- Target project dev deps need `freezed` and `build_runner`.
- Run code generation after scaffolding.
- If the project has not installed those yet, follow
  `skills/flowr-dart-usage/references/freezed-install.md`.

## First Checks

- Follow `AGENTS.md`: Flutter and Dart commands use `fvm`; Python commands use
  `uv`.
- Before editing code, run `git status --short`. If unrelated uncommitted
  changes exist, ask whether to commit or ignore them.
- Do not add hidden compatibility switches for breaking changes. Explain the
  behavior change explicitly.

## Source-First Inputs

- If the user provides a Figma URL, read the Figma data before generating or
  editing page code. Extract the relevant frame/screen structure, repeated UI
  patterns, component names, text, interaction hints, and visual hierarchy.
- If the user provides an OpenAPI document or API URL/file, read the API data
  before generating or editing page code. Extract the endpoint/use case,
  request parameters, response schema, error/loading/empty states, and the data
  source that should feed the view model.
- Use the extracted Figma and API facts to fill the `Figma` and `API` contract
  sections first. Do not treat the URL or file path as enough context by
  itself.
- Use source data and nearby pages to decide `State Ownership` before creating
  page-private state. Top-level, parent-owned, feature-shared, and cached
  remote state should be referenced as external owners instead of copied into
  the generated primary model.
- If a provided Figma or OpenAPI source cannot be accessed, say so before
  writing code and continue only with an explicit fallback from the user or
  with clearly marked assumptions.

## Responsibility Boundary

- Use this skill when the task is about page layout under `lib/page/...` or
  `lib/src/page/...`, especially contract/view/view-model split files.
- Match the existing project page root. Some projects use
  `lib/page/xxx_page/`, `lib/page/xxx_view/`, or `lib/src/page/...`.
- Optional middle folders are allowed under the page root, for example
  `lib/src/page/account/xxx_page/` or `lib/src/page/account/xxx_view/`.
- Keep the page root's `widget.dart` for widgets reused across multiple pages.
  Do not move page-private widgets there.
- The contract file owns all imports used by both `part` files, including
  `freezed_annotation` and the generated `.freezed.dart` part.

## Recommended Layout

```text
lib/[src]/page/
├── widget.dart
└── [optional-middle-folder]/
    └── [xxx_page|xxx_view]/
        ├── [xxx_page|xxx_view].dart
        ├── [xxx_page|xxx_view].freezed.dart
        ├── [xxx_page|xxx_view].v.dart
        └── [xxx_page|xxx_view].vm.dart
```

## Workflow

1. Inspect source inputs.
   Read provided Figma URLs and OpenAPI documents before deciding widget
   boundaries, reused widgets, state fields, events, or models.

2. If the target project does not already use `freezed`, install it first by
   following `skills/flowr-dart-usage/references/freezed-install.md`.

3. Inspect nearby page folders or run:

```bash
uv run python skills/fr-mvvm-contract/scripts/page_context.py --target lib/page/foo_page
```

4. Analyze the page before generating code.
   The AI should first decide:
   - which models will exist
   - which widgets will exist
   - which events will exist
   - what the generated primary view model dependencies and event handlers are
   - which external view models / models are only referenced, not owned

5. Write a structured page spec JSON.

6. Generate the Dart files from that spec:

```bash
uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/order_confirm_page.json
uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/order_confirm_page.json --parent account
uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/order_confirm_page.json --page-root lib/src/page
uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/order_confirm_page.json --dir /tmp/order_confirm_page --force
```

7. Review the generated files, then make only the small manual edits that the
   generator cannot express cleanly.

## Contract File Rules

- `xxx_page.dart` or `xxx_view.dart` is the entry file and should expose the
   route-level widget at a glance.
  Keep only developer-facing contract content there: imports, `part`
  declarations, contract comments, the root widget, theme/model declarations,
  and state ownership notes.
- Always declare:

```dart
part '<contract_name>.freezed.dart';
part '<contract_name>.v.dart';
part '<contract_name>.vm.dart';
```

- Keep the contract doc comments above the root widget in this order:
  - Figma
  - API
  - State Ownership
  - Route
  - Reused Widgets
  - Widget Tree
  - Theme
  - Events
  - ViewModels
  - Models
- In the `Events` section, wrap every referenced event class in `[]`,
  including private subclasses such as `[_LoadMore]`. The contract file and
  `.vm.dart` part share the same library, so private event classes are valid
  direct references there.
- The root `XxxPage` / `XxxView` must be a `StatelessWidget`. Its `build`
  method should only wire dependencies and lifecycle hooks such as
  `FrProvider` and `onCreated`, then return the generated entry widget.
- Do not put concrete UI implementation in the root route widget.
- For `FrBlocViewModel`, use `FrProvider.onCreated` to dispatch startup events
  when the page needs bootstrap logic.

## View File Rules

- Start with `part of '<contract_name>.dart';`
- Keep widget code only. All concrete UI implementation belongs here,
  including `Scaffold`, app bars, layout structure, controls, lists,
  empty/loading/error surfaces, and private page widgets.
- The generator creates `_XxxPageView` in `page` mode and `_XxxViewBody` in
  `view` mode; provide its `build` body in the spec as `view.entry.build`.
- Other view widgets are generated from `view.widgets[]` and are currently
  constrained to `StatelessWidget`.

## ViewModel File Rules

- Start with `part of '<contract_name>.dart';`
- Keep business logic and state transitions only.
- Always use `FrBlocViewModel<GeneratedEvent, GeneratedModel>`.
- Events are generated under one sealed base class in the contract library.
- Models are generated in the contract file with `@freezed`.
- Put page logic into:
  - `view_model.event_handlers[]` for `on<Event>` blocks
  - `view_model.methods[]` for named methods/getters on the view model
- Use `event_handlers[].is_async: true` when a handler needs `await`.
- Return new unequal immutable model instances. Reallocate `List`, `Map`, and
  `Set` values before emitting.

## Required Spec Shape

The generator expects a JSON object with these top-level keys:

- `page`
- `models`
- `events`
- `view_model`
- `view`

### `page`

Required / common fields:

- `name`
  Accepts `foo`, `foo_page`, `FooPage`, `foo-page`, `foo_view`, `FooView`, or
  `foo-view`.
- `state_ownership`
  Use either `"none"` or a string array.
- `widget_tree`
  String array rendered into the contract comment.

Optional fields:

- `kind`
  Optional suffix mode when `name` omits it. Must be `page` or `view`.
- `figma`
- `api`
- `route`
- `imports`
  String URI imports or objects with `uri`, optional `as`, optional `show`,
  optional `hide`.
- `reused_widgets`
- `external_view_models`
- `external_models`
- `provider.create`
- `provider.on_created`
- `provider.lazy`
- `theme`

### `models`

- Must include the generated primary model:
  - `XxxPageModel` in `page` mode
  - `XxxModel` in `view` mode
- Each model entry contains:
  - `name`
  - `description`
  - optional `doc`
  - `fields`
  - optional `members`
- The generator emits:
  - `@freezed`
  - the generated primary model's private constructor
  - the generated primary model's `const factory`
- `copyWith` is provided by `freezed`, not handwritten by this script.
- When a model field uses `default`, the generator renders `@Default(...)`.
- If a field is non-nullable, it must be `required` or define `default`.
- Use nullable types for optional nullable fields instead of `default: null`
  unless that null default is intentional.

### `events`

- Each event entry contains:
  - `name`
  - `description`
  - optional `doc`
  - optional `fields`
- Field entries may use positional args or named args with `named: true`.

### `view_model`

- The generator fixes the class name to:
  - `XxxPageViewModel` in `page` mode
  - `XxxViewModel` in `view` mode
- Supported fields:
  - `description`
  - optional `doc`
  - optional `dependencies`
  - optional `initial_state`
  - `event_handlers`
  - optional `members`
  - optional `methods`

Each `event_handlers[]` item supports:

- `event`
- `body`
- optional `is_async`

Each `methods[]` item supports:

- `signature`
- `body`
- optional `doc`

### `view`

- `entry.build` is required and becomes:
  - `_XxxPageView.build` in `page` mode
  - `_XxxViewBody.build` in `view` mode
- `widgets[]` contains the remaining page widgets.
- Each widget entry supports:
  - `name`
  - optional `doc`
  - optional `fields`
  - optional `members`
  - `build`
  - optional `include_key`

## Minimal Example

```json
{
  "page": {
    "name": "order_confirm",
    "figma": "Checkout confirmation screen with summary and submit CTA.",
    "api": "POST /orders/confirm returns submit status.",
    "route": "AppRouter.orderConfirm",
    "state_ownership": [
      "[OrderConfirmPageViewModel]: page-private, owns local submit flow and [OrderConfirmPageModel]"
    ],
    "widget_tree": [
      "[OrderConfirmPageScaffold]",
      "|- [OrderConfirmHeader]",
      "'- [OrderConfirmActionBar]"
    ],
    "provider": {
      "create": "OrderConfirmPageViewModel(orderRepo: context.read<OrderRepo>())",
      "on_created": "vm.add(const OrderConfirmPageStarted());"
    }
  },
  "models": [
    {
      "name": "OrderConfirmPageModel",
      "description": "primary page state",
      "fields": [
        { "name": "loading", "type": "bool", "default": "true" },
        { "name": "note", "type": "String", "default": "''" },
        { "name": "errorText", "type": "String?", "default": "null" }
      ]
    }
  ],
  "events": [
    {
      "name": "OrderConfirmPageStarted",
      "description": "bootstrap the initial submit state"
    },
    {
      "name": "OrderConfirmSubmitted",
      "description": "submit the confirmation request"
    }
  ],
  "view_model": {
    "description": "primary page view model",
    "dependencies": [
      { "name": "orderRepo", "type": "OrderRepo" }
    ],
    "event_handlers": [
      {
        "event": "OrderConfirmPageStarted",
        "body": "emit(state.copyWith(loading: false));"
      },
      {
        "event": "OrderConfirmSubmitted",
        "is_async": true,
        "body": "emit(state.copyWith(loading: true));\ntry {\n  await orderRepo.submit();\n  emit(state.copyWith(loading: false));\n} catch (error) {\n  emit(state.copyWith(loading: false, errorText: error.toString()));\n}"
      }
    ]
  },
  "view": {
    "entry": {
      "build": "return FrView<OrderConfirmPageViewModel, OrderConfirmPageModel>(\n  builder: (context, snap, child) => OrderConfirmPageScaffold(snap: snap),\n);"
    },
    "widgets": [
      {
        "name": "OrderConfirmPageScaffold",
        "fields": [
          {
            "name": "snap",
            "type": "FrSnap<OrderConfirmPageViewModel, OrderConfirmPageModel>"
          }
        ],
        "build": "return Scaffold(body: OrderConfirmActionBar(snap: snap));"
      },
      {
        "name": "OrderConfirmActionBar",
        "fields": [
          {
            "name": "snap",
            "type": "FrSnap<OrderConfirmPageViewModel, OrderConfirmPageModel>"
          }
        ],
        "build": "return FilledButton(\n  onPressed: () => snap.vm.add(const OrderConfirmSubmitted()),\n  child: const Text('Submit'),\n);"
      }
    ]
  }
}
```

For `xxx_view.dart`, either set `"name": "order_confirm_view"` or keep
`"name": "order_confirm"` and add `"kind": "view"`. That mode generates
`OrderConfirmView`, `OrderConfirmViewModel`, `OrderConfirmEvent`, and
`OrderConfirmModel`.

## Validation

- Format changed Dart files with `fvm dart format <paths>`.
- Run `fvm dart run build_runner build --delete-conflicting-outputs` after
  generating or changing page models.
- Run `fvm flutter analyze` or the repo's analyzer command after page
  migrations.
- When editing only this skill, run:
  - `uv run python skills/fr-mvvm-contract/scripts/page_context.py`
  - write temporary `page` and `view` JSON specs
  - `uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/foo.json --dir /tmp/fr_contract_mvvm_smoke --force`
  - `uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/foo_view.json --dir /tmp/fr_contract_mvvm_smoke_view --force`
  - inspect the generated files before deleting the temp dir
  - this repository does not currently include `freezed_annotation`, so the
    smoke check here is limited to generation and formatting, not `build_runner`

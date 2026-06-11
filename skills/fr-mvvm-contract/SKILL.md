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
- Generate page models with explicit `@Freezed(...)`, not handwritten
  `copyWith`.
- Do not add `FrViewModel` / method-mode content here.
- Treat the contract dart file as the only long-lived source of truth.
- Let the AI analyze the page internally first; if the generator still needs a
  JSON spec, keep it temporary and do not commit it as a parallel design
  artifact.
- Then pass that temporary spec to the Python generator to produce the final
  Dart files.

Use the installed `flowr-usage` skill first for Flutter-facing API semantics.
If event semantics or shared FlowR behavior matter, load
`skills/flowr-dart-usage/SKILL.md` before `skills/flowr-usage/SKILL.md`.
If the target project does not already have `freezed` installed, load
`skills/flowr-dart-usage/references/freezed-install.md` before scaffolding the
page.
If the page will use `bff` mode, load
`skills/fr-mvvm-contract/references/fr-acdd.md` before designing the DTO
contract.
If the page will use `bff` mode and the target project does not already
have `fr_acdd`, load
`skills/fr-mvvm-contract/references/fr-acdd-install.md` before scaffolding the
page.

## Scaffolding Requirements

- Run `skills/fr-mvvm-contract/scripts/new_page.py` with
  `--spec-file <json>`.
- The generator produces:
  - `XxxPage` or `XxxView`
  - `_XxxPageView` or `_XxxViewBody`
  - a generated `FrBlocViewModel<...>` subclass
  - one generated sealed event base class
  - one generated primary `@Freezed(...)` model
- Generated contract files include:
  - `import 'package:freezed_annotation/freezed_annotation.dart';`
  - `part '<contract_name>.freezed.dart';`
- Target project runtime deps need `freezed_annotation`.
- Target project dev deps need `freezed` and `build_runner`.
- `bff` pages also need `fr_acdd` in the target package dependencies.
- Run code generation after scaffolding.
- If the project has not installed those yet, follow
  `skills/flowr-dart-usage/references/freezed-install.md`.
- If the page uses `bff` mode and `fr_acdd` is missing, follow
  `skills/fr-mvvm-contract/references/fr-acdd-install.md`.

## First Checks

- Follow `AGENTS.md`: Flutter and Dart commands use `fvm`; Python commands use
  `uv`.
- Before editing code, run `git status --short`. If unrelated uncommitted
  changes exist, ask whether to commit or ignore them.
- Do not add hidden compatibility switches for breaking changes. Explain the
  behavior change explicitly.

## Input Gate

- The required analysis inputs are:
  - `figmaUrl`
  - `api`
- `figmaUrl` must point to the source design that the page should follow.
- `api` must be exactly one of:
  - `NONE`
  - `BFF`
  - `BFF-JSON`
  - `BFF-PROTO`
  - a concrete API/OpenAPI reference
- `NONE` means the page has no backend API contract for now.
- `BFF` means the AI must derive the backend DTO boundary and upstream API
  split from the UI plus nearby project context.
- `BFF-JSON` means the page uses `BFF`, and the derived export format should
  be `JSON`.
- `BFF-PROTO` means the page uses `BFF`, and the derived export format should
  be `PROTO`.
- A concrete API/OpenAPI reference means the AI must read that source before
  finalizing DTO boundaries, loading paths, and error/empty/loading states.
- If either required input is missing, stop and ask for it instead of
  generating page code directly.

## Source-First Inputs

- Read the Figma URL before generating or editing page code. Extract the
  relevant frame/screen structure, repeated UI patterns, component names, text,
  interaction hints, and visual hierarchy.
- Inspect nearby page folders, shared `page/widget.dart` usage, and theme
  constraints before deciding which widgets stay page-private versus shared.
- If the page is in `bff` mode, use the Figma screen structure to decide the
  DTO boundaries and the upstream API split before writing models. Do not
  assume one page implies one API.
- In `bff` mode, analyze whether the screen composes multiple independent
  data sources. Multi-tab, dashboard, and mixed-feed screens often need
  multiple APIs combined by the BFF. Example: a notifications page with three
  tabs usually maps to three notification list APIs or three filtered upstream
  queries, not one oversized API that returns all tab payloads together.
- If `api` points to an OpenAPI document or API URL/file, read that API data
  before generating or editing page code. Extract the endpoint/use case,
  request parameters, response schema, error/loading/empty states, and the data
  source that should feed the view model.
- Use the extracted Figma and API facts to fill the contract comment sections
  first. Do not treat the URL or file path as enough context by itself.
- If `api` is `NONE`, keep the contract section as `API: none`.
- In `bff` mode, hide `API:` and use `BFF-API:` for the pre-analysis result.
- In `bff` mode, the `BFF-API` contract section must record the pre-analysis
  result: list each upstream API, its owned DTO slice, and whether the page
  needs fan-out aggregation, sequential bootstrap, or per-tab lazy loading.
- In `bff` mode, render one API block per upstream branch. The first line
  should be `METHOD <BASE>/...`; following lines should list DTO refs such as
  `[SummaryReq], [SummaryModel]`.
- Use source data and nearby pages to decide `State Ownership` before creating
  page-private state. Top-level, parent-owned, feature-shared, and cached
  remote state should be referenced as external owners instead of copied into
  the generated primary model.
- Keep page-local state outside exported `fr_acdd` DTO classes. In `bff`
  mode, `@FrAcddDto` is for backend-transfer DTOs only.
- When `exportFormat` resolves to `JSON`, do not add protobuf `tag` values
  just in case. Omit bare `@FrAcddField()` annotations entirely; add
  `@FrAcddField(...)` only when the field needs `include: false`, custom
  `wireName`, explicit `nestedRef`, or a protobuf `tag` for `PROTO`.
- If a provided Figma or API source cannot be accessed, say so before writing
  code and continue only with an explicit fallback from the user or with
  clearly marked assumptions.

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
   Require `figmaUrl` and `api` first. Read the Figma URL, nearby
   pages/components/theme constraints, and any concrete API/OpenAPI source
   before deciding widget boundaries, reused widgets, state fields, events, or
   models. In `bff` mode, also decide the upstream API split and whether the
   page bootstraps all APIs together or loads some branches lazily.

2. If the target project does not already use `freezed`, install it first by
   following `skills/flowr-dart-usage/references/freezed-install.md`.

   If the page uses `bff` mode, load
   `skills/fr-mvvm-contract/references/fr-acdd.md` before finalizing the DTO
   contract.

   If the page uses `bff` mode and the target project does not already have
   `fr_acdd`, install it first by following
   `skills/fr-mvvm-contract/references/fr-acdd-install.md`.

3. Inspect nearby page folders or run:

```bash
uv run python skills/fr-mvvm-contract/scripts/page_context.py --target lib/page/foo_page
```

4. Analyze the page before generating code.
   The AI should first decide:
   - which models will exist
   - which widgets will exist
   - which events will exist
   - which upstream APIs exist for the page and whether one screen needs
     multiple APIs combined by the BFF
   - which API owns each DTO branch or tab payload
   - which API calls happen on page start versus tab switch / pagination /
     refresh
   - what the generated primary view model dependencies and event handlers are
   - which external view models / models are only referenced, not owned

5. Write a temporary page spec JSON only if the generator still needs it.
   Do not commit that JSON as a parallel design artifact; the generated
   `contract dart` becomes the long-lived source of truth.

6. Generate the Dart files from that spec:

```bash
uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/order_confirm_page.json
uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/order_confirm_page.json --parent account
uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/order_confirm_page.json --page-root lib/src/page
uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/order_confirm_page.json --dir /tmp/order_confirm_page --force
```

7. Review the generated files, then make only the small manual edits that the
   generator cannot express cleanly. After developers edit the `contract dart`
   file manually, treat that updated contract as the new source of truth and
   resync the remaining files from it.

## Contract File Rules

- `xxx_page.dart` or `xxx_view.dart` is the entry file and should expose the
   route-level widget at a glance.
  Keep only developer-facing contract content there: imports, `part`
  declarations, contract comments, the root widget, theme/model declarations,
  and state ownership notes.
- For `bff` pages, the contract file is also the source that `fr_acdd`
  reads before deriving `proto/json5` output.
- In `fr_acdd`, `FrAcddMode` only distinguishes `api` versus `bff`.
  `proto/json5` are export formats selected by the CLI, not extra contract
  modes.
- Always declare:

```dart
part '<contract_name>.freezed.dart';
part '<contract_name>.v.dart';
part '<contract_name>.vm.dart';
```

- Keep the contract doc comments above the root widget in this order:
  - Figma
  - API when `api` is a concrete API reference or `NONE`
  - State Ownership
  - Route
  - Reused Widgets
  - Widget Tree
  - Theme
  - Events
  - ViewModels
  - Models
  - BFF-API when `api == BFF`
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
- Do not generate `_XxxPageDimens` or similar constants-holder classes.
  Prefer responsive constraints such as full-width layout, `Expanded`,
  `Flexible`, and parent-driven sizing over copying fixed Figma pixels
  mechanically. Use direct numeric literals only when the layout semantics
  truly need them.
- Keep `Figma:` stable as the source design URL. When the page uses an
  existing API, keep `API:` near the top and omit `BFF-API:`.
- In `bff` mode, omit `API:`, place `BFF-API:` below `Models:`, and format
  each branch as a multiline block, for example
  `GET <BASE>/home-page/summary` followed by
  `[HomePortfolioSummaryReq], [HomePortfolioSummaryModel]`. During export,
  `<BASE>/...` resolves from the contract file path, with `_` converted to `-`.
  A top-level page such as `lib/page/home_page/home_page.dart` maps to
  `<BASE>/home-page/...`. A child page such as
  `lib/page/home_page/sub_page/sub_page.dart` maps to
  `<BASE>/home-page/sub-page/...`.

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
- Models are generated in the contract file with explicit `@Freezed(...)`.
- In `bff` mode, only backend-transfer DTOs should use `@FrAcddDto`. Keep
  page-local state in page models or view-model members instead of annotating
  it as DTO state.
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
- `figmaUrl`
  Required source design URL for the page.
- `api`
  Required analysis input. Must be `NONE`, `BFF`, `BFF-JSON`, `BFF-PROTO`, or
  a concrete API/OpenAPI reference.
- `state_ownership`
  Use either `"none"` or a string array.
- `widget_tree`
  String array rendered into the contract comment.

Optional fields:

- `kind`
  Optional suffix mode when `name` omits it. Must be `page` or `view`.
- `figma`
  Optional extra inline notes that will be appended after `figmaUrl` in the
  contract comment.
- `apiContract`
  Optional analyzed BFF API contract comment. In `bff` mode, use a string
  array where each item is one multiline API block. The first line should be
  `METHOD <BASE>/...`; following lines list request/response DTO refs. This
  field is required when `api` resolves to `BFF`.
- `exportFormat`
  Optional when `api` resolves to `BFF`. Must be `JSON` or `PROTO`. Defaults
  to `JSON`. `JSON` still maps to the Markdown review document exported by
  `fr_acdd` with JSON5 request/response snippets. `PROTO` maps to `.proto`.
- If `api` is `BFF-JSON` or `BFF-PROTO`, that shorthand fixes the export
  format directly. Do not also pass a conflicting `exportFormat`.
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

If `theme` is present, it supports:

- optional `doc`
- optional `declaration`
- optional `fields`
- optional `members`
- `declaration` is emitted directly above the generated `XxxTheme` class.
- If `declaration` or `members` reference generated JSON helpers such as
  `@JsonSerializable`, `_$XxxThemeFromJson`, or `_$XxxThemeToJson`, the
  generator also emits `part '<contract_name>.g.dart';`.

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
  - `@Freezed(copyWith: true, equal: true, toStringOverride: true, fromJson: false, toJson: false)`
  - the generated primary model's private constructor
  - the generated primary model's `const factory`
- `copyWith`, equality, and debug `toString` are provided by `Freezed`, not
  handwritten by this script.
- JSON factories are disabled by default in generated page models. Only enable
  them deliberately when the model truly crosses a JSON boundary.
- `@FrAcddDto`-style DTOs should stay single-constructor data classes. Do not
  use Freezed unions for DTO extraction targets.
- In `bff` mode, keep `@FrAcddDto` for backend-transfer DTOs only. Do not
  represent page-local state as DTO kind state in newly generated code.
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
    "figmaUrl": "https://www.figma.com/file/example/order-confirm",
    "figma": "Checkout confirmation screen with summary and submit CTA.",
    "api": "BFF-PROTO",
    "apiContract": [
      "GET <BASE>/order-confirm-page/summary\n[OrderConfirmSummaryReq], [OrderConfirmSummaryModel]",
      "GET <BASE>/order-confirm-page/coupon-preview\n[OrderConfirmCouponPreviewReq], [OrderConfirmCouponPreviewModel]",
      "POST <BASE>/order-confirm-page/submit\n[OrderConfirmSubmitReq], [OrderConfirmSubmitResp]"
    ],
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

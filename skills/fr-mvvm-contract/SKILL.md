---
name: fr-mvvm-contract
description: Create or migrate FlowR Flutter pages to a contract-first MVVM layout with `xxx_page.dart`, `xxx_page.v.dart`, and `xxx_page.vm.dart`. Use when splitting page code into contract/view/view-model part files under `lib/page`, scaffolding new page folders, or enforcing contract doc blocks, `FrProvider` ownership, theme/model placement, and optional FrBloc event summaries.
---

# Fr Contract MVVM

Create or update FlowR Flutter pages in a contract-first layout. The contract
file is the entry and overview; the view and view-model live in `part` files.

Use the installed `flowr-usage` skill first for Flutter-facing API semantics.
If event semantics or shared FlowR behavior matter, load
`skills/flowr-dart-usage/SKILL.md` before `skills/flowr-usage/SKILL.md`.

## First Checks

- Follow `AGENTS.md`: Flutter and Dart commands use `fvm`; Python commands use
  `uv`.
- Before editing code, run `git status --short`. If unrelated uncommitted
  changes exist, ask whether to commit or ignore them.
- Do not add hidden compatibility switches for breaking changes. Explain the
  behavior change explicitly.

## Responsibility Boundary

- Use this skill when the task is about page layout under `lib/page/...`,
  especially contract/view/view-model split files.
- Use `flowr-mvvm-creator` when the task is about traditional `*.mvvm.dart`
  files or service-level MVVM outside page folders.
- Keep `lib/page/widget.dart` for widgets reused across multiple pages. Do not
  move page-private widgets there.
- The contract file owns all imports used by both `part` files. If
  `xxx_page.vm.dart` uses `FutureOr`, import `dart:async` in `xxx_page.dart`.

## Recommended Layout

```text
lib/page/
├── widget.dart
└── xxx_page/
    ├── xxx_page.dart
    ├── xxx_page.v.dart
    └── xxx_page.vm.dart
```

## Workflow

1. Inspect nearby page folders or run:

```bash
uv run python skills/fr-mvvm-contract/scripts/page_context.py --target lib/page/foo_page
```

2. Generate a starter when creating a page:

```bash
uv run python skills/fr-mvvm-contract/scripts/new_page.py --name foo
uv run python skills/fr-mvvm-contract/scripts/new_page.py --name order_confirm --mode bloc --route AppRouter.orderConfirm
```

3. Edit the generated contract comments first, then fill view widgets, then
   finish business logic.
4. When migrating an existing page, move state contract items into
   `xxx_page.dart`, widget code into `xxx_page.v.dart`, and logic into
   `xxx_page.vm.dart`.

## Contract File Rules

- `xxx_page.dart` is the entry file and should expose the page at a glance.
- Always declare:

```dart
part 'xxx_page.v.dart';
part 'xxx_page.vm.dart';
```

- Keep the contract doc comments above `XxxPage` in this order:
  - Route: prefer `[AppRouter.fooPage]` when the router symbol is already in
    scope; otherwise use plain text to avoid unresolved doc refs.
  - Reused Widgets: list imported shared widgets from `lib/page/widget.dart`;
    if none, say `none`.
  - Widget Tree: multi-line tree using doc refs to actual view widget classes.
  - Theme: `[XxxPageTheme]` or `none`.
  - Events: one line per event for `FrBlocViewModel`; for method mode write
    `none`.
  - State: `[XxxPageViewModel], [XxxPageModel]`
- The contract file should usually contain:
  - `XxxPage`
  - `XxxPageTheme`
  - `XxxPageModel`
- `XxxPage` should return `FrProvider(...)` and then the actual UI
  implementation widget from `.v.dart`.
- For `FrBlocViewModel`, use `FrProvider.onCreated` to dispatch a startup event
  when the page needs bootstrap logic.

## View File Rules

- Start with `part of 'xxx_page.dart';`
- Keep widget code only.
- Prefer a private entry widget like `_XxxPageView` plus a few named public
  widgets that the contract comment can reference.
- Each widget may have a one-line doc comment when it carries layout meaning.
  Skip noise comments.

## ViewModel File Rules

- Start with `part of 'xxx_page.dart';`
- Keep business logic and state transitions only.
- Use `FrViewModel<XxxPageModel>` for method mode and
  `FrBlocViewModel<XxxPageEvent, XxxPageModel>` for event mode.
- Important logic may have one-line comments. Avoid widget concerns.
- Return new unequal immutable model instances. Reallocate `List`, `Map`, and
  `Set` values before emitting.

## Generator

Use the starter generator and then replace placeholders with real contract
data:

```bash
uv run python skills/fr-mvvm-contract/scripts/new_page.py --name profile
uv run python skills/fr-mvvm-contract/scripts/new_page.py --name order_confirm --mode bloc --route AppRouter.orderConfirm
```

- `--name` accepts `foo`, `foo_page`, `FooPage`, or `foo-page`.
- `--dir` overrides the output directory; default is `lib/page/<name>_page`.
- `--force` overwrites existing files.
- `--route` writes the route comment as plain text. Convert it to a doc ref
  only after the router symbol is actually imported and resolvable.

## Validation

- Format changed Dart files with `fvm dart format <paths>`.
- Run `fvm flutter analyze` or the repo's analyzer command after page
  migrations.
- When editing only this skill, run:
  - `uv run python skills/fr-mvvm-contract/scripts/page_context.py`
  - `uv run python skills/fr-mvvm-contract/scripts/new_page.py --name smoke --dir /tmp/fr_contract_mvvm_smoke --force`
  - inspect the generated files before deleting the temp dir

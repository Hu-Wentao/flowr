---
name: flowr-mvvm-creator
description: Create or update FlowR MVVM code for Flutter projects using the flowr package. Use when adding .mvvm.dart files, FlowR models, FrViewModel or FrBlocViewModel view models, FrProvider registration, FrView/FrListener/FrConsumer widgets, or migrating MVVM code after FlowR breaking changes.
---

# FlowR-MVVM Creator

Create FlowR MVVM code that matches the local `flowr` package without loading
large source files into context by default.

## First Checks

- Follow the project `AGENTS.md`: Flutter and Dart commands use `fvm`
  prefixes, for example `fvm flutter test` and `fvm dart format`.
- Before editing code, run `git status --short`. If unrelated uncommitted
  changes exist, ask whether to commit or ignore them.
- Do not read FlowR source files by default. Start with the compact context
  script and open only the specific file it flags as ambiguous.

## Compact Context

Run this before generating or migrating MVVM code:

```bash
uv run python skills/flowr-mvvm-creator/scripts/mvvm_context.py --target <path>
```

Use `--target` for the intended `.mvvm.dart` file or the feature directory.
The script prints current local API facts, equal-value guardrails, and nearby
existing `.mvvm.dart` files. Read source manually only when the output contains
`API_NOT_FOUND`, when changing FlowR internals, or when a task needs an API not
covered by the summary.

For a starter file, prefer the generator and then edit the result to the real
state contract:

```bash
uv run python skills/flowr-mvvm-creator/scripts/new_mvvm.py --name Counter --mode method --output lib/service/counter.mvvm.dart
uv run python skills/flowr-mvvm-creator/scripts/new_mvvm.py --name Counter --mode bloc --output lib/service/counter.mvvm.dart
```

## Core Rules

- Import `package:flowr/flowr_mvvm.dart`.
- Use `FrViewModel<M>` for method-driven state such as `login()`, `refresh()`,
  `selectUser(user)`, or `setLocale(locale)`.
- Use `FrBlocViewModel<E, M>` when callers naturally dispatch events with
  `vm.add(Event())`.
- Method-driven VMs update with `update((old) => ...)` or `put(newModel)`;
  bloc-driven event handlers emit with `emit(...)` and read current `state`.
- Models should be immutable: `final` fields, `const` constructor when
  possible, and `copyWith`.
- `put(value)` and `update(...)` follow Cubit equality semantics: equal values
  do not emit. Always return a new unequal model when the UI should rebuild.
- For collection fields, create new `List`, `Map`, or `Set` instances instead
  of mutating existing collections.
- Do not add compatibility switches for equal-value re-emission; the public
  config API does not expose one. If any breaking-change compatibility setting
  is required, explicitly tell the user what changed and why.

## Layout

Default to the existing local convention. If none exists, use:

```text
lib/service/
├── app.mvvm.dart
├── db.service.dart
└── user/
    ├── user.mvvm.dart
    └── cart/
        └── cart.mvvm.dart
```

- A `.mvvm.dart` file should contain the model, one ViewModel, and only the
  small reusable widgets tightly coupled to that state contract.
- Put cross-cutting services in `*.service.dart`. Extend `FrService` only when
  the service needs FlowR logging, `runCatching`, slowly helpers, or disposal.

## Implementation Workflow

1. Run `mvvm_context.py` and inspect nearby `.mvvm.dart` examples from its
   output only if they are relevant.
2. Identify the state contract: fields, async operations, services, and UI
   events.
3. Generate a starter with `new_mvvm.py` when useful, then replace placeholder
   fields/actions with the real contract.
4. Register the ViewModel with `FrProvider`, `FrProvider.di`, or
   `FrProvider.value` based on ownership.
5. Build UI with `FrView`, `FrListener`, `FrConsumer`, or `FrMultiListener`.
6. Keep widget-only formatting and navigation concerns out of the ViewModel.

## Validation

- Format changed Dart files with `fvm dart format <paths>`.
- Run focused tests with `fvm flutter test <package-or-test-path>` when widgets,
  providers, or shared behavior are touched.
- Run `fvm dart analyze` or the package-specific analyzer command when shared
  APIs are changed.
- When editing only this skill, run:
  `uv run python skills/flowr-mvvm-creator/scripts/mvvm_context.py` and
  `uv run python skills/flowr-mvvm-creator/scripts/new_mvvm.py --name Smoke --mode method`,
  then check `git diff -- skills/flowr-mvvm-creator`.

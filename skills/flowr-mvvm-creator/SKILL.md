---
name: flowr-mvvm-creator
description: Create or update FlowR MVVM files for Flutter projects that use the flowr package. Use when adding or migrating .mvvm.dart files, generating FlowR models and FrViewModel/FrBlocViewModel classes, wiring FrProvider ownership, or following this repository's default MVVM file layout.
---

# FlowR-MVVM Creator

Create FlowR MVVM files that match a project's chosen feature layout. This
skill handles file creation, local MVVM conventions, and starter generation. It
does not define the general FlowR API rules.

If the `flowr-usage` skill is installed, use it first for general Flutter API
semantics. If the repo is pure `flowr_dart` without `flowr`, a dedicated pure
Dart skill is a better fit when available. Otherwise continue with the minimal
guardrails below and inspect the local package only for APIs that are
ambiguous.

## First Checks

- Follow the project `AGENTS.md`: Flutter and Dart commands use `fvm`
  prefixes, for example `fvm flutter test` and `fvm dart format`.
- Before editing code, run `git status --short`. If unrelated uncommitted
  changes exist, ask whether to commit or ignore them.
- Do not read FlowR source files by default. Start with the compact context
  script and open only the specific file it flags as ambiguous.

## Responsibility Boundary

- Use this skill when the task is about creating or migrating `.mvvm.dart`
  files, choosing a local MVVM layout, generating a starter model/ViewModel, or
  finding nearby MVVM examples.
- Use the installed `flowr-usage` skill, when available, for general Flutter
  `flowr`, `FrUnion`, provider, or widget-facing API guidance.
- If the repo only uses `flowr_dart` without `flowr`, a dedicated pure Dart
  skill is a better fit when available.
- Projects may keep their own feature/file layout. Follow nearby examples before
  applying this skill's default layout.
- Do not force `lib/service/...` when the host project already has a clear
  architecture.

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

- Import `package:flowr/flowr_mvvm.dart` in generated Flutter MVVM files.
- Use `FrViewModel<M>` for method-driven state and `FrBlocViewModel<E, M>` for
  event-driven state.
- Models should be immutable: `final` fields, `const` constructor when possible,
  and `copyWith`.
- Equal states do not emit. Always return a new unequal model when the UI should
  rebuild, and allocate new `List`, `Map`, or `Set` instances.
- FlowR view-model streams are bloc-native streams and do not replay current
  state to new subscribers; use `value` or `state` for synchronous reads.
- Do not add hidden compatibility switches for breaking changes. If requested,
  explicitly tell the user what behavior changed and why.

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

1. Load the installed `flowr-usage` skill when available, then use
   `mvvm_context.py` to confirm local APIs.
2. Run `mvvm_context.py` and inspect nearby `.mvvm.dart` examples from its
   output only if they are relevant.
3. Identify the state contract: fields, async operations, services, and UI
   events.
4. Generate a starter with `new_mvvm.py` when useful, then replace placeholder
   fields/actions with the real contract.
5. Register the ViewModel with `FrProvider`, `FrProvider.di`, or
   `FrProvider.value` based on ownership.
6. Build UI with `FrView`, `FrListener`, `FrConsumer`, or `FrMultiListener`.
7. Keep widget-only formatting and navigation concerns out of the ViewModel.

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

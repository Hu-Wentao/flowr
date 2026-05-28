---
name: flowr-usage
description: Use FlowR Flutter APIs correctly in projects that use the flowr package. Use when writing or reviewing FrViewModel/FrBlocViewModel widgets, FrProvider setup, FrUnion state, or widget-facing flowr usage, even when the project has its own file layout. For pure Dart FlowR/FlowB code, use flowr-dart-usage.
---

# FlowR Usage

Use `flowr` Flutter APIs correctly without assuming a specific project file
layout.

## First Checks

- Follow the project `AGENTS.md`: this repository uses `fvm` for Flutter and
  Dart commands, for example `fvm dart test` and `fvm flutter analyze`.
- Before editing code, run `git status --short`. If unrelated uncommitted
  changes exist, ask whether to commit or ignore them.
- Prefer the project's existing architecture. This skill covers Flutter-facing
  `flowr` API usage, not where files must live.
- If the request is mainly about pure Dart `FlowR<T>`, `FlowB<E, S>`, stream
  helper semantics, or shared logic outside Flutter widgets, first load
  `../flowr-dart-usage/SKILL.md`.

## Imports

- Flutter MVVM code: import `package:flowr/flowr_mvvm.dart`.
- Import `dart:async` when public methods use `FutureOr`, `Stream`, or
  `StreamSubscription` types directly.
- Do not import `flowr/src/...` from application code.

## State Semantics

- `FrViewModel<M>` and `FrBlocViewModel<E, M>` inherit bloc-native equal-state
  suppression and non-replayable stream behavior from the underlying FlowR
  layers.
- Return a new unequal immutable model instance when the UI should rebuild.
- For `List`, `Map`, and `Set` fields, allocate a new collection before
  emitting.
- If the task depends on raw `FlowR` or `FlowB` semantics, read
  `../flowr-dart-usage/SKILL.md` instead of re-deriving behavior from source.
- If a breaking-change compatibility setting is requested, explicitly tell the
  user what behavior changed and why. Do not hide it behind config.

## flowr Flutter Usage

Define models as `FrModel`-compatible immutable objects. Use
`FrViewModel<M>` for method-driven Flutter state:

```dart
class CounterModel {
  final int value;

  const CounterModel({this.value = 0});

  CounterModel copyWith({int? value}) =>
      CounterModel(value: value ?? this.value);
}

class CounterViewModel extends FrViewModel<CounterModel> {
  CounterViewModel() : super(const CounterModel());

  FutureOr<CounterModel?> increment() =>
      update((old) => old.copyWith(value: old.value + 1));
}
```

Use `FrBlocViewModel<E, M>` when callers naturally dispatch events:

```dart
class CounterViewModel
    extends FrBlocViewModel<CounterEvent, CounterModel> {
  CounterViewModel() : super(const CounterModel()) {
    on<CounterIncremented>(
      (event, emit) => emit(state.copyWith(value: state.value + 1)),
    );
  }
}
```

Register ownership with `FrProvider`:

```dart
FrProvider(
  (context) => CounterViewModel(),
  child: const CounterPage(),
);
```

- Use `FrProvider.value` for an existing instance, such as dialog/subtree reuse.
- Use `FrProvider.multi` for multiple providers.
- `FrProvider` disposes `DisposeMx` and closes bloc `Closable` instances.
- `FrProvider.di` and `FrUnion` are advanced opt-in patterns; load
  `references/fr-provider-di.md` or `references/fr-union.md` only when the
  request already explicitly uses them.

Build UI with:

```dart
FrView<CounterViewModel, CounterModel>(
  builder: (context, snap, child) => Text('${snap.data.value}'),
);
```

- `FrView` rebuilds from state.
- `FrListener` handles side effects.
- `FrConsumer` combines listener and builder.
- `FrMultiListener` groups listeners.
- `FrSnap` is a record: `(vm: VM, data: M)`.
- `FrView`, `FrListener`, `FrConsumer`, and `FrViewU` route view models through
  bloc-native UI components.

## References

Load these only when the request touches the package or scenario:

- `references/fr-provider-di.md`: `FrProvider.di`, GetIt ownership, and
  Provider-vs-DI lookup rules.
- `references/fr-union.md`: `FrUnion`, tagged models, `FrUnionViewModel`, and
  `FrViewU`.
- `references/fr-mvvm-env.md`: environment selector package usage.
- `references/fr-mvvm-locale.md`: locale state and locale switcher usage.
- `references/fr-mvvm-theme.md`: theme switching, ThemeExtension helpers, built-in and JSON-config theme sources, and image scheme usage.
- `references/fr-mvvm-user.md`: user selector/session state package usage.

## Validation

- Format changed Dart files with `fvm dart format <paths>`.
- For Flutter package/app code, run `fvm flutter test` for touched widgets or
  providers.
- Run `fvm dart analyze` or `fvm flutter analyze` when shared APIs or package
  surfaces change.

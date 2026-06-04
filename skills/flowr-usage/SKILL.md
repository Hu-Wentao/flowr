---
name: flowr-usage
description: Use FlowR Flutter APIs correctly in projects that use the flowr package. Use when writing or reviewing FrViewModel/FrBlocViewModel widgets, FrProvider setup, FrUnion state, FrView/FrListener/FrConsumer usage, autoDisposeNotifier and other Flutter-specific ownership patterns, or package extensions such as fr_mvvm_theme/locale/env/user, even when the project has its own file layout.
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
- If the repo depends on `flowr`, it also implicitly depends on `flowr_dart`.
  Shared `FlowR`/`FlowB` semantics still come from `flowr_dart`.
- If the `flowr-dart-usage` skill is installed, load it first for shared core
  behavior such as `logger`, `logE`, `runCatching`, `skpIf`, `skpNull`,
  `update(...)`, debounce/throttle/mutex, `DisposeMx`, and bloc-native stream
  semantics. The installed skill file is `skills/flowr-dart-usage/SKILL.md`.
- If `flowr-dart-usage` is not installed, explicitly ask the user to install
  it before continuing.
- If the user declines to install `flowr-dart-usage`, continue with the
  minimal fallback rules in this skill instead of inventing local variants.
- If the repo only depends on `flowr_dart` and does not use `flowr`, do not
  use this skill; use `flowr-dart-usage` directly.

## Imports

- Flutter MVVM code: import `package:flowr/flowr_mvvm.dart`.
- Import `dart:async` when public methods use `FutureOr`, `Stream`, or
  `StreamSubscription` types directly.
- Do not import `flowr/src/...` or `flowr_dart/src/...` from application code.

## Shared Core Fallback

- `package:flowr/flowr_mvvm.dart` re-exports the public `flowr_dart` APIs that
  Flutter users normally need.
- `FrViewModel<M>` extends `FlowR<M>` and is the method-driven path.
- `FrBlocViewModel<E, M>` extends `FlowB<E, M>` and is the event-driven path.
- `value` is the legacy alias of `state`.
- Public callers of `FrBlocViewModel` should dispatch `add(event)` rather than
  rely on `put`.
- `FrViewModel` and `FrBlocViewModel` already inherit FlowR logging helpers
  and shared helper mixins through `FlowR`/`FlowB`; do not re-implement
  `logger`, `logE`, `runCatching`, debounce/throttle/mutex, or `autoDispose`
  primitives in app code.
- `put(value)` and `update(...)` follow bloc equality semantics: if the new
  value equals the current value, no new stream event is emitted.
- `stream` is bloc-native and does not replay the current state to new
  subscribers; use `value` or `state` for synchronous reads.
- `putError` logs and forwards errors to the bloc/cubit error channel.
- `skpNull(value, 'reason')` and `skpIf(condition, 'reason')` cancel a flow
  without treating it as a failure.
- Use `autoDisposeNotifier(notifier)` for owned `ChangeNotifier` instances such
  as `FocusNode`, `TextEditingController`, or custom notifiers.
- `FrProvider` disposes `DisposeMx` instances automatically. For manually owned
  view models outside `FrProvider`, call `dispose()` or `close()` when done.

## State Semantics

- `FrViewModel<M>` and `FrBlocViewModel<E, M>` inherit bloc-native equal-state
  suppression and non-replayable stream behavior from the underlying FlowR
  layers.
- Return a new unequal immutable model instance when the UI should rebuild.
- For `List`, `Map`, and `Set` fields, allocate a new collection before
  emitting.
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

- Installed `flowr-dart-usage` skill at `skills/flowr-dart-usage/SKILL.md`:
  source of truth for shared `FlowR`/`FlowB` semantics inherited by `flowr`.
- `references/flowr-install.md`: adding `flowr` to a Flutter project,
  `FrProvider` ownership, and first `FrViewModel` plus `FrView` wiring.
- `references/fr-provider-di.md`: `FrProvider.di`, GetIt ownership, and
  Provider-vs-DI lookup rules.
- `references/fr-vm-communication.md`: multi-VM communication, route results,
  `FrProvider.value` reuse, and one-way VM coordination patterns.
- `references/fr-union.md`: `FrUnion`, tagged models, `FrUnionViewModel`, and
  `FrViewU`.
- `references/fr-mvvm-env-install.md`: installing `fr_mvvm_env`, root provider
  placement, and app-wide environment state wiring.
- `references/fr-mvvm-env.md`: environment selector usage after install.
- `references/fr-mvvm-locale-install.md`: installing `fr_mvvm_locale`, root
  locale state wiring, and `MaterialApp(locale: ...)` integration.
- `references/fr-mvvm-locale.md`: locale switcher usage after install.
- `references/fr-mvvm-theme-install.md`: installing `fr_mvvm_theme`, app-owned
  theme model setup, root `ThemeData(extensions: ...)` injection, and shared
  theme tokens such as colors, spacing, padding, and component sizes.
- `references/fr-mvvm-theme.md`: built-in theme switching, page theme reads,
  and page-scoped theme values after install.
- `references/fr-mvvm-theme-advance.md`: runtime-loaded theme JSON, file/http
  resources, `theme://` rewriting, and custom `IThemeViewModel` loading.
- `references/fr-mvvm-user-install.md`: installing `fr_mvvm_user`, shared
  session state wiring, and root provider placement.
- `references/fr-mvvm-user.md`: user selector/session usage after install.

## Validation

- Format changed Dart files with `fvm dart format <paths>`.
- For Flutter package/app code, run `fvm flutter test` for touched widgets or
  providers.
- Run `fvm dart analyze` or `fvm flutter analyze` when shared APIs or package
  surfaces change.

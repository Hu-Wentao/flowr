---
name: flowr-usage
description: Use FlowR Flutter APIs correctly in projects that use the flowr package. Use when writing or reviewing FrViewModel/FrBlocViewModel widgets, FrProvider setup, FrUnion state, widget-facing flowr usage, FlowR logging (`logger`, `logF/logI/logW/logE`, `putError`), `runCatching`/`skpIf`/`skpNull`, debounce/throttle/mutex scheduling, autoDispose/dispose behavior, or the shared FlowR basics inherited from flowr_dart, even when the project has its own file layout.
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
- This skill must remain usable on its own. Do not assume sibling skills are
  installed when explaining inherited `FlowR` or `FlowB` behavior.
- If the repo only depends on `flowr_dart` and does not use `flowr`, you may
  suggest installing the dedicated `flowr-dart-usage` skill when available.

## Imports

- Flutter MVVM code: import `package:flowr/flowr_mvvm.dart`.
- Import `dart:async` when public methods use `FutureOr`, `Stream`, or
  `StreamSubscription` types directly.
- Do not import `flowr/src/...` or `flowr_dart/src/...` from application code.

## Shared FlowR Basics

- `package:flowr/flowr_mvvm.dart` re-exports the public `flowr_dart` APIs that
  Flutter users normally need.
- `FrViewModel<M>` extends `FlowR<M>` and is the method-driven path.
- `FrBlocViewModel<E, M>` extends `FlowB<E, M>` and is the event-driven path.
- `FrViewModel` and `FrBlocViewModel` already inherit FlowR logging helpers
  through `FlowR`/`FlowB`; do not re-implement `logger`, `logE`, or parallel
  ad-hoc logging methods in app code.
- `FrViewModel` and `FrBlocViewModel` already inherit FlowR helper mixins for
  `runCatching`/`skpIf`/`skpNull`, debounce/throttle/mutex, and
  `autoDispose`; do not re-implement those primitives in app code.
- `value` is the legacy alias of `state`.
- Use `update(...)` when the next state depends on the current state or may
  fail:

```dart
FutureOr<CounterModel?> increment() => update(
  (old) => old.copyWith(value: old.value + 1),
  onError: (error, stackTrace) => putError(error, stackTrace),
);
```

- Public callers of `FrBlocViewModel` should dispatch `add(event)` rather than
  rely on `put`.
- `put(value)` and `update(...)` follow bloc equality semantics: if the new
  value equals the current value, no new stream event is emitted.
- `stream` is bloc-native and does not replay the current state to new
  subscribers; use `value` or `state` for synchronous reads.
- `putError` logs and forwards errors to the bloc/cubit error channel.
- `skpNull(value, 'reason')` and `skpIf(condition, 'reason')` cancel a flow
  without treating it as a failure.

## Logging

- When a user asks to add log printing inside a FlowR view model, first use the
  built-in helpers: `logger`, `logF`, `logI`, `logW`, `logE`, and `logS`.
- Do not implement a new `logE`, `logger`, `printLog`, extension, or mixin
  wrapper unless the task explicitly asks to extend FlowR itself.
- Use `logger('message')` for ordinary trace logs near `update(...)`.
- Use `logI`, `logW`, or `logE` when the severity matters.
- Use `putError(error, stackTrace)` when the failure should also reach the
  bloc/cubit error channel, not just the logger.
- `FrViewModel` and `FrBlocViewModel` default `logExtra` to `LogExtra.self`
  outside release mode, so you usually do not need to override it just to show
  method locations.
- If an `update(...)` body is async, `await update(...)` so log call sites stay
  accurate.
- Load `references/fr-logging.md` when the task asks to add logs, tune log
  levels, wire `Logger.root`, or decide between `logger`, `logE`, and
  `putError`.

## Control Flow

- Use `update(...)` for `FrViewModel<M>` state changes.
- Public callers of `FrBlocViewModel` should still dispatch `add(event)`; use
  `runCatching(...)` inside the view model only for shared side effects or
  helper flows, not as a replacement for bloc events.
- `skpIf(...)` and `skpNull(...)` throw `SkipError`, which stops the current
  flow without being treated as a failure.
- Do not use deprecated `ignoreSkipError`; control SkipError visibility with
  logger level instead.
- Load `references/fr-run-catching.md` when the task asks to skip a flow, catch
  failures without surfacing them as errors, or decide whether to use
  `runCatching`, `skpIf`, or `skpNull`.

## Scheduling And Disposal

- `debounceTag` and `throttleTag` only apply when `slowlyMs > 0`.
- `mutexTag` is independent of `slowlyMs` and ignores overlapping work with the
  same tag.
- Tags are scoped to a single view model instance. Reuse a stable tag per
  logical action.
- Use `autoDispose(subscription)` for stream subscriptions created by a view
  model.
- Use `autoDisposeNotifier(notifier)` for owned `ChangeNotifier` instances such
  as `FocusNode`, `TextEditingController`, or custom notifiers.
- `FrProvider` disposes `DisposeMx` instances automatically. For manually owned
  view models outside `FrProvider`, call `dispose()` or `close()` when done.
- Load `references/fr-slowly.md` when the task asks for debounce, throttle,
  mutex, or lock-state behavior.
- Load `references/fr-disposal.md` when the task asks about
  `autoDispose`, `autoDisposeNotifier`, `subBy`, notifier cleanup, `dispose`,
  or `close`.
- Load `references/fr-update.md` when the task asks for deeper `update(...)`
  semantics such as `onError`, `logging`, or scheduling tags on updates.

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

- `references/fr-provider-di.md`: `FrProvider.di`, GetIt ownership, and
  Provider-vs-DI lookup rules.
- `references/fr-logging.md`: FlowR logging helpers, `Logger.root` setup, and
  when to use `logger`, `logE`, or `putError`.
- `references/fr-run-catching.md`: `runCatching`, `skpIf`, `skpNull`,
  `SkipError`, and failure-vs-skip control flow in view models.
- `references/fr-slowly.md`: debounce/throttle/mutex scheduling for view model
  actions.
- `references/fr-disposal.md`: `DisposeMx`, `autoDispose`,
  `autoDisposeNotifier`, `subBy`, and Provider-owned disposal.
- `references/fr-update.md`: `FrViewModel.update(...)`, `onError`, `logging`,
  and scheduling tags on updates.
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

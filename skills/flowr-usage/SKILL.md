---
name: flowr-usage
description: Use FlowR APIs correctly across Dart and Flutter projects. Use when writing or reviewing flowr_dart FlowR/FlowB code, flowr FrViewModel/FrBlocViewModel widgets, FrProvider setup, FrUnion state, stream helpers, or migration after FlowR breaking changes, even when the project has its own file layout.
---

# FlowR Usage

Use FlowR APIs correctly without assuming a specific project file layout.

## First Checks

- Follow the project `AGENTS.md`: this repository uses `fvm` for Flutter and
  Dart commands, for example `fvm dart test` and `fvm flutter analyze`.
- Before editing code, run `git status --short`. If unrelated uncommitted
  changes exist, ask whether to commit or ignore them.
- Prefer the project's existing architecture. This skill covers FlowR API usage,
  not where files must live.

## Imports

- Pure Dart code: import `package:flowr_dart/flowr_dart.dart`.
- Flutter MVVM code: import `package:flowr/flowr_mvvm.dart`.
- Import `dart:async` when public methods use `FutureOr`, `Stream`, or
  `StreamSubscription` types directly.
- Do not import `flowr/src/...` or `flowr_dart/src/...` from application code.

## flowr_dart Core

Use `FlowR<T>` for method-driven state:

```dart
class Counter extends FlowR<int> {
  Counter() : super(0);

  int increment() => put(value + 1);
}
```

Use `update` when the next state depends on the current state and may fail:

```dart
FutureOr<UserState?> refresh() => update(
  (old) async => old.copyWith(user: await api.loadUser()),
  onError: (error, stackTrace) => putError(error, stackTrace),
);
```

Use `FlowB<E, S>` for event-driven state:

```dart
sealed class CounterEvent {
  const CounterEvent();
}

class CounterIncremented extends CounterEvent {
  const CounterIncremented();
}

class CounterBloc extends FlowB<CounterEvent, int> {
  CounterBloc() : super(0) {
    on<CounterIncremented>((event, emit) => emit(state + 1));
  }
}
```

Rules:

- `FlowR<T>` extends `Cubit<T>` and exposes `value` as the legacy name for
  `state`.
- `FlowB<E, S>` extends `Bloc<E, S>` and should be driven from `add(event)`.
- `FlowB.put` is protected/test-only style; public callers should dispatch
  events.
- `put(value)` and `update(...)` follow bloc equality semantics: if
  `newValue == currentValue`, no stream event is emitted.
- `stream` uses bloc-native semantics. It does not replay the current state to
  new subscribers; use `value` or `state` for synchronous reads.
- Do not add `valueStream` overrides or compatibility switches to restore
  replayable streams.
- `dispose()` is kept for legacy FlowR APIs; bloc-native code may use `close()`.

## State Rules

- Prefer immutable state: `final` fields, `const` constructors, `copyWith`, and
  value equality when the project already uses it.
- To trigger a UI update, return a new unequal model instance.
- For `List`, `Map`, and `Set` fields, allocate a new collection before
  emitting:

```dart
update((old) => old.copyWith(items: [...old.items, item]));
```

- Do not mutate an existing state object and call `put(old)`.
- Use `skpNull(value, 'name')` or `skpIf(condition, 'reason')` to cancel a flow
  without treating it as a failure.
- If a breaking-change compatibility setting is requested, explicitly tell the
  user what behavior changed and why. Do not hide it behind config.

## Stream Helpers

Use normal `Stream<T>` helpers on `FlowR.stream` and `FlowB.stream`:

```dart
final labels = counter.stream.distinctWith((count) => 'count: $count');
final evenValues = counter.stream.where((count) => count.isEven);
final uniqueValues = counter.stream.distinctUnique();
```

- `distinctBy((event) => event.field)` filters consecutive events by a selected
  key.
- `distinctWith((event) => mapped)` maps then de-duplicates consecutive mapped
  values.
- `distinctUnique()` filters duplicates across the whole stream history.
- Legacy `ValueStream` helpers such as `mapValue` and `whereValue` are only for
  actual `ValueStream<T>` instances, not FlowR view-model streams.

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

- Use `FrProvider.di` for GetIt-created instances that should be pulled into the
  widget tree.
- Use `FrProvider.value` for an existing instance, such as dialog/subtree reuse.
- Use `FrProvider.multi` for multiple providers.
- `FrProvider` disposes `DisposeMx` and closes bloc `Closable` instances.

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

## FrUnion

Use `FrUnionViewModel` for small global typed state sets:

```dart
FrConfig.initialize(
  frUnion: FrUnion.of({CounterModel(), UserModel()}),
);
```

- `FrUnion.of({...})` accepts plain model values.
- `FrUnion.ofTaggedModel({(model, 'tag')})` or `FrUnionViewModel.ofTag(...)`
  supports multiple values of the same type.
- Read typed values with `FrViewU<M>` or `vm.streamBy<M>(tag: ...)`.
- Update typed values with `vm.updateBy<M>((old) => next, tag: ...)`.
- Avoid a single global `FrUnionViewModel` for complex app domains with unclear
  ownership.

## References

Load these only when the request touches the package or scenario:

- `references/fr-mvvm-env.md`: environment selector package usage.
- `references/fr-mvvm-locale.md`: locale state and locale switcher usage.
- `references/fr-mvvm-theme.md`: theme switching, ThemeExtension helpers, built-in and JSON-config theme sources, and image scheme usage.
- `references/fr-mvvm-user.md`: user selector/session state package usage.
- `references/migration.md`: detailed migration after FlowR breaking changes.

## Validation

- Format changed Dart files with `fvm dart format <paths>`.
- For pure Dart package code, run `fvm dart test` or focused tests.
- For Flutter package/app code, run `fvm flutter test` for touched widgets or
  providers.
- Run `fvm dart analyze` or `fvm flutter analyze` when shared APIs or package
  surfaces change.

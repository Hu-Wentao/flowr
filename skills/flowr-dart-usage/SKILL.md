---
name: flowr-dart-usage
description: Use flowr_dart APIs correctly in pure Dart or shared logic. Use when writing or reviewing FlowR/FlowB state classes, update/put behavior, stream helpers, immutable state emission rules, or migration after flowr_dart breaking changes, even when the project has its own file layout.
---

# FlowR Dart Usage

Use `flowr_dart` APIs correctly without Flutter or MVVM assumptions.

## First Checks

- Follow the project `AGENTS.md`: this repository uses `fvm` for Flutter and
  Dart commands, for example `fvm dart test` and `fvm flutter analyze`.
- Before editing code, run `git status --short`. If unrelated uncommitted
  changes exist, ask whether to commit or ignore them.
- Prefer the project's existing architecture. This skill covers pure Dart FlowR
  API usage, not where files must live.

## Imports

- Import `package:flowr_dart/flowr_dart.dart`.
- Import `dart:async` when public methods use `FutureOr`, `Stream`, or
  `StreamSubscription` types directly.
- Do not import `flowr_dart/src/...` from application code.

## FlowR Core

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
- To trigger updates, return a new unequal model instance.
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
  actual `ValueStream<T>` instances, not FlowR or FlowB streams.

## Validation

- Format changed Dart files with `fvm dart format <paths>`.
- Run `fvm dart test` or focused tests for touched pure Dart packages.
- Run `fvm dart analyze` when shared APIs or package surfaces change.

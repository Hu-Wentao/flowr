# FlowR Core

Use this reference for every `FlowR` or `FlowB` task. In a Dart-only package,
this is the only FlowR reference to load.

## Imports

- Import `package:flowr_dart/flowr_dart.dart` in a pure Dart package.
- Import `dart:async` only when public APIs expose `FutureOr`, `Stream`, or
  `StreamSubscription`.
- Do not import `flowr_dart/src/...`.

## State And Events

Use `FlowR<T>` for method-driven state:

```dart
class Counter extends FlowR<int> {
  Counter() : super(0);

  int increment() => put(value + 1);
}
```

Use `update` when the next state depends on the current state or can fail:

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

- `FlowR<T>` extends `Cubit<T>`; `value` aliases `state`.
- `FlowB<E, S>` extends `Bloc<E, S>`; public callers dispatch `add(event)`.
  Treat `FlowB.put` as protected/test-only style.
- `put(value)` and `update(...)` suppress equal state. Return a new unequal,
  immutable state when observers must rebuild.
- Do not mutate an existing `List`, `Map`, or `Set`; allocate a new collection
  before emission.
- `stream` is bloc-native and does not replay current state. Use `state` or
  `value` for a synchronous read. Do not add replay compatibility wrappers.

## Built-in Helpers

- Use inherited `logger`, `logF`, `logI`, `logW`, `logE`, and `logS`; do not
  create app-level wrappers for them.
- Use `putError(error, stackTrace)` when the failure should reach the bloc/cubit
  error channel.
- Use `runCatching(...)` for shared work that needs FlowR skip/error handling.
- `skpIf(...)` and `skpNull(...)` throw `SkipError` to stop a flow without
  treating it as failure. Control visibility through logger level, not
  `ignoreSkipError`.
- `debounceTag` and `throttleTag` work only with `slowlyMs > 0`; `mutexTag` is
  independent and ignores concurrent work with the same instance-scoped tag.
- Register owned subscriptions with `autoDispose(...)`; manually owned values
  must be closed or disposed.

## Streams

```dart
final labels = counter.stream.distinctWith((count) => 'count: $count');
final evenValues = counter.stream.where((count) => count.isEven);
final uniqueValues = counter.stream.distinctUnique();
```

- `distinctBy` filters consecutive values by a selected key.
- `distinctWith` maps and de-duplicates consecutive values.
- `distinctUnique` filters duplicates across stream history.
- `mapValue` and `whereValue` are only for real `ValueStream<T>` instances,
  never `FlowR.stream` or `FlowB.stream`.

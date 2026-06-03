---
name: flowr-dart-usage
description: Use flowr_dart APIs correctly in pure Dart or shared logic. Use when writing or reviewing FlowR/FlowB state classes, update/put behavior, FlowR logging (`logger`, `logF/logI/logW/logE`, `putError`), `runCatching`/`skpIf`/`skpNull`, debounce/throttle/mutex scheduling, autoDispose/dispose behavior, stream helpers, immutable state emission rules, or migration after flowr_dart breaking changes, including the shared core semantics inherited by projects that depend on `flowr`, even when the project has its own file layout.
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
- If a project depends on `flowr`, it implicitly depends on `flowr_dart`; this
  skill remains the source of truth for shared `FlowR`/`FlowB` semantics.
- When both `flowr-usage` and `flowr-dart-usage` are installed, handle shared
  core behavior here first and let `flowr-usage` handle Flutter-specific
  widgets, providers, and MVVM extensions.

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
- `FlowR` and `FlowB` already inherit FlowR logging helpers through
  `LoggableMx`; do not re-implement `logger`, `logE`, or ad-hoc wrappers in
  application code.
- `FlowR` and `FlowB` already inherit FlowR helper mixins for
  `runCatching`/`skpIf`/`skpNull`, debounce/throttle/mutex, and
  `autoDispose`; do not re-implement those primitives in application code.
- `put(value)` and `update(...)` follow bloc equality semantics: if
  `newValue == currentValue`, no stream event is emitted.
- `stream` uses bloc-native semantics. It does not replay the current state to
  new subscribers; use `value` or `state` for synchronous reads.
- Do not add `valueStream` overrides or compatibility switches to restore
  replayable streams.
- `dispose()` is kept for legacy FlowR APIs; bloc-native code may use `close()`.

## Logging

- When a task asks to add log printing inside a `FlowR` or `FlowB` class, first
  use the built-in helpers: `logger`, `logF`, `logI`, `logW`, `logE`, and
  `logS`.
- Do not implement a new `logE`, `logger`, extension, or mixin wrapper unless
  the task explicitly asks to change FlowR internals.
- Use `logger('message')` for ordinary trace logs near `update(...)`.
- Use `logI`, `logW`, or `logE` when the severity matters.
- Use `putError(error, stackTrace)` when the failure should also reach the
  bloc/cubit error channel, not just the logger.
- If an `update(...)` body is async, `await update(...)` so log call sites stay
  accurate.
- Load `references/flowr-logging.md` when the task asks to add logs, tune log
  levels, wire `Logger.root`, or decide between `logger`, `logE`, and
  `putError`.

## Control Flow

- Use `update(...)` for `FlowR<T>` state changes.
- Use `runCatching(...)` for non-state work or shared async/sync work that
  should reuse FlowR skip/error handling.
- `skpIf(...)` and `skpNull(...)` throw `SkipError`, which stops the current
  flow without being treated as a failure.
- Do not use deprecated `ignoreSkipError`; control SkipError visibility with
  logger level instead.
- Load `references/flowr-run-catching.md` when the task asks to skip a flow,
  catch failures without throwing, or decide whether to use `runCatching`,
  `skpIf`, or `skpNull`.

## Scheduling And Disposal

- `debounceTag` and `throttleTag` only apply when `slowlyMs > 0`.
- `mutexTag` is independent of `slowlyMs` and ignores overlapping work with the
  same tag.
- Tags are scoped to a single `FlowR`/`FlowB` instance. Reuse a stable tag per
  logical action.
- Use `autoDispose(subscription)` to register stream subscriptions for cleanup.
- In manually owned pure Dart code, call `dispose()` or `close()` when the
  instance is no longer used.
- Load `references/flowr-slowly.md` when the task asks for debounce, throttle,
  mutex, or lock-state behavior.
- Load `references/flowr-disposal.md` when the task asks about
  `autoDispose`, `subBy`, `dispose`, or `close`.
- Load `references/flowr-update.md` when the task asks for deeper `update(...)`
  semantics such as `onError`, `logging`, or scheduling tags on updates.

## State Rules

- Prefer immutable state: `final` fields, `const` constructors, `copyWith`, and
  value equality when the project already uses it.
- When a task needs new `@freezed` model/state classes or a repo does not yet
  have `freezed` installed, load `references/freezed-install.md` first.
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

## References

- `references/freezed-install.md`: installing `freezed_annotation`,
  `freezed`, and `build_runner`, plus the minimal `@freezed` scaffold and code
  generation commands.
- `references/flowr-dart-install.md`: adding `flowr_dart` to a pure Dart or
  shared logic package, entrypoint logger setup, and the first `FlowR`/`FlowB`
  scaffold.
- `references/flowr-logging.md`: FlowR logging helpers, `Logger.root` setup,
  and when to use `logger`, `logE`, or `putError`.
- `references/flowr-run-catching.md`: `runCatching`, `skpIf`, `skpNull`,
  `SkipError`, and failure-vs-skip control flow.
- `references/flowr-slowly.md`: debounce/throttle/mutex scheduling and lock
  semantics.
- `references/flowr-disposal.md`: `DisposeMx`, `autoDispose`, `subBy`,
  `dispose`, and `close`.
- `references/flowr-update.md`: `update(...)`, `onError`, `logging`, and
  scheduling tags on state updates.

## Validation

- Format changed Dart files with `fvm dart format <paths>`.
- Run `fvm dart test` or focused tests for touched pure Dart packages.
- Run `fvm dart analyze` when shared APIs or package surfaces change.

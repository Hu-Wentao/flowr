# flowr_logging

Use this reference when a task asks to add log printing, report errors, wire
FlowR logging output, or decide whether a `FlowR`/`FlowB` class should call
`logger`, `logI`, `logW`, `logE`, or `putError`.

## Existing API

- `FlowR` and `FlowB` inherit `LoggableMx`.
- Available protected helpers already exist:
  `logger`, `logF`, `logI`, `logW`, `logE`, and `logS`.
- `putError(error, stackTrace)` logs and forwards the error to the bloc/cubit
  error channel.
- `logger(...)` defaults to the runtime type as the logger name unless a custom
  `name` is passed.

## Patterns

Use `logger` for normal trace logging around updates:

```dart
class Counter extends FlowR<int> {
  Counter() : super(0);

  int increment() => update((old) {
        logger('increment -> ${old + 1}');
        return old + 1;
      })!;
}
```

Use `logE` when you need an explicit error-level log but do not want to emit to
the bloc error channel:

```dart
Future<void> sync() async {
  try {
    await repo.sync(state);
  } catch (error, stackTrace) {
    logE(
      'sync failed',
      error: error,
      stackTrace: stackTrace,
    );
  }
}
```

Use `putError` when the failure should be observable by FlowR error handling:

```dart
FutureOr<UserState?> refresh() => update(
  (old) async => old.copyWith(user: await api.loadUser()),
  onError: (error, stackTrace) => putError(error, stackTrace),
);
```

Configure the app-level logger once near startup:

```dart
Logger.root.level = Level.INFO;
Logger.root.onRecord.listen(LoggableMx.devLogRecordPrinter);
```

Set `Logger.root.level = Level.FINE` when you need normal `put`, debounce,
throttle, mutex, or skip-flow diagnostics.

## Rules

- Do not add a custom `logE` implementation to application classes that
  already extend `FlowR` or `FlowB`.
- Do not replace FlowR logging with raw `print(...)` unless the user explicitly
  asks for that behavior.
- Prefer `logger('message')` for simple tracing and `logI`/`logW`/`logE` when
  the severity is part of the requirement.
- If an `update(...)` callback is async, call `await update(...)` so log
  location metadata points to the right app method.

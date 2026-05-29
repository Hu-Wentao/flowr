# fr_logging

Use this reference when a task asks to add log printing, report errors, wire
FlowR logging output, or decide whether a view model should call `logger`,
`logI`, `logW`, `logE`, or `putError`.

## Existing API

- `FrViewModel` and `FrBlocViewModel` inherit `LoggableMx` through
  `FlowR`/`FlowB`.
- Available protected helpers already exist:
  `logger`, `logF`, `logI`, `logW`, `logE`, and `logS`.
- `putError(error, stackTrace)` logs and forwards the error to the bloc/cubit
  error channel.
- Flutter view models default `logExtra` to `LogExtra.self` outside release
  mode, so call-site locations usually work without extra overrides.

## Patterns

Use `logger` for normal trace logging around state updates:

```dart
class UserViewModel extends FrViewModel<UserModel> {
  UserViewModel() : super(const UserModel());

  FutureOr<UserModel?> rename(String nextName) => update((old) {
        logger('rename -> $nextName');
        return old.copyWith(name: nextName);
      });
}
```

Use `logE` when you need an explicit error-level log but do not want to emit to
the bloc error channel:

```dart
Future<void> saveDraft() async {
  try {
    await repo.save(state);
  } catch (error, stackTrace) {
    logE(
      'saveDraft failed',
      error: error,
      stackTrace: stackTrace,
    );
  }
}
```

Use `putError` when the failure should be observable by FlowR error handling:

```dart
FutureOr<UserModel?> refresh() => update(
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

- Do not add a custom `logE` implementation to app view models that already
  extend `FrViewModel`, `FrBlocViewModel`, `FlowR`, or `FlowB`.
- Do not replace FlowR logging with raw `print(...)` unless the user explicitly
  asks for that behavior.
- Prefer `logger('message')` for simple tracing and `logI`/`logW`/`logE` when
  the severity is part of the requirement.
- If an `update(...)` callback is async, call `await update(...)` so log
  location metadata points to the right app method.

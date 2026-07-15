# flowr_update

Use this reference when a task asks for deeper `update(...)` behavior in
`FlowR<T>`, especially `onError`, `logging`, debounce/throttle/mutex tags, or
deprecated update helpers.

## Existing API

- `FlowR.update(updater, ...)` reads the current `value`, runs the updater, and
  forwards success through `putWithLogging(...)`.
- If the updater returns `null`, `update(...)` does not emit a new value.
- If `onError` is omitted, `update(...)` defaults to `putError(error, stackTrace)`.
- `logging(prv, cur)` customizes the success log line for that update.
- `onPutLogging` is deprecated; prefer `logging`.
- `updateRaw(...)` is deprecated; prefer `update(...)`.

## Patterns

Use `logging` when the state transition message matters:

```dart
FutureOr<UserState?> rename(String name) => update(
  (old) => old.copyWith(name: name),
  logging: (prv, cur) => 'rename: ${prv.name} -> ${cur.name}',
);
```

Override the default error path only when the task needs custom handling:

```dart
FutureOr<UserState?> refresh() => update(
  (old) async => old.copyWith(user: await api.loadUser()),
  onError: (error, stackTrace) {
    logW('refresh failed', error: error, stackTrace: stackTrace);
    return null;
  },
);
```

## Rules

- Use `update(...)` when the next state depends on the current state.
- Return a new unequal value when listeners should observe a change.
- A custom `onError` suppresses the default `putError(...)`; call `putError`
  manually inside `onError` if the error should still reach the bloc/cubit
  error channel.
- `debounceTag`, `throttleTag`, and `mutexTag` on `update(...)` are forwarded
  into `runCatching`; load `flowr-slowly.md` when scheduling details matter.

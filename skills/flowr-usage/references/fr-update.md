# fr_update

Use this reference when a task asks for deeper `FrViewModel.update(...)`
behavior, especially `onError`, `logging`, debounce/throttle/mutex tags, or
deprecated update helpers.

## Existing API

- `FrViewModel.update(updater, ...)` is the standard method-driven state change
  path inherited from `FlowR`.
- If the updater returns `null`, `update(...)` does not emit a new value.
- If `onError` is omitted, `update(...)` defaults to `putError(error, stackTrace)`.
- `logging(prv, cur)` customizes the success log line for that update.
- `onPutLogging` is deprecated; prefer `logging`.
- `updateRaw(...)` is deprecated; prefer `update(...)`.

## Patterns

Use `logging` when the state transition message matters:

```dart
FutureOr<UserModel?> rename(String name) => update(
  (old) => old.copyWith(name: name),
  logging: (prv, cur) => 'rename: ${prv.name} -> ${cur.name}',
);
```

Override the default error path only when the task needs custom handling:

```dart
FutureOr<UserModel?> refresh() => update(
  (old) async => old.copyWith(user: await api.loadUser()),
  onError: (error, stackTrace) {
    logW('refresh failed', error: error, stackTrace: stackTrace);
    return null;
  },
);
```

## Rules

- Use `update(...)` for `FrViewModel` state changes when the next model depends
  on the current model.
- Return a new unequal model when listeners should observe a change.
- A custom `onError` suppresses the default `putError(...)`; call `putError`
  manually inside `onError` if the error should still reach the bloc/cubit
  error channel.
- `debounceTag`, `throttleTag`, and `mutexTag` on `update(...)` are forwarded
  into `runCatching`; load `fr-slowly.md` when scheduling details matter.
- For `FrBlocViewModel`, keep public state changes event-driven with `add(...)`
  and `on<Event>(...)`; do not turn it into a method-driven `update(...)` API.

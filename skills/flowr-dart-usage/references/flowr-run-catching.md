# flowr_run_catching

Use this reference when a task asks to skip a flow, catch failures without
throwing, or decide whether a `FlowR`/`FlowB` class should use
`runCatching`, `skpIf`, or `skpNull`.

## Existing API

- `runCatching<R>(block, ...)` runs sync or async work and normalizes error
  handling.
- `skpIf(condition, reason)` throws `SkipError` when the condition is true.
- `skpNull(value, reason)` throws `SkipError` when the value is null, otherwise
  returns the non-null value.
- `FlowR.runCatching` and `FlowB.runCatching` log `SkipError` as
  `SKIPPED: ...` and return `null`.
- Unhandled non-skip failures default to a warning log in `FlowR`/`FlowB`.

## Patterns

Use `runCatching` for non-state work or shared side effects:

```dart
Future<bool?> syncDraft() => runCatching<bool>(
  () async {
    final draft = skpNull(repo.currentDraft, 'draft');
    await api.sync(draft);
    return true;
  },
  onFailure: (error, stackTrace) {
    logW('syncDraft failed', error: error, stackTrace: stackTrace);
    return false;
  },
);
```

Use `skpIf` or `skpNull` to stop a flow intentionally without treating it as a
failure:

```dart
FutureOr<UserState?> refresh() => update((old) async {
  final userId = skpNull(old.userId, 'userId');
  skpIf(old.loading, 'refresh already running');
  return old.copyWith(user: await api.loadUser(userId));
});
```

## Rules

- Use `SkipError` semantics only for expected non-failure exits. Do not hide
  real validation or transport errors behind `skpIf`.
- `runCatching` returns `null` when the block returns `null` or the flow is
  skipped.
- `runCatching` accepts `slowlyMs`, `debounceTag`, `throttleTag`, and
  `mutexTag`; load `flowr-slowly.md` when scheduling behavior matters.
- Do not use deprecated `ignoreSkipError`; in current `FlowR`/`FlowB`
  integration, SkipError is always handled explicitly.

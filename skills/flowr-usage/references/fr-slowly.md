# fr_slowly

Use this reference when a task asks for debounce, throttle, mutex, or lock
state behavior in `FrViewModel` or `FrBlocViewModel`.

## Existing API

- `debounce(tag, duration, action, {maxDuration})` waits until calls stop, then
  runs the last action.
- `throttle(tag, duration, action, {ensureLast = false})` runs immediately and
  skips overlapping triggers during the cooldown window.
- `mutex(tag, action)` runs immediately and ignores overlapping calls with the
  same tag until the current action finishes.
- `isDebounceLocked`, `isThrottleLocked`, and `isMutexLocked` expose protected
  lock checks.

## Rules

- `debounceTag` and `throttleTag` only take effect when `slowlyMs > 0`.
- `mutexTag` does not depend on `slowlyMs`.
- Tags are scoped to one view model instance. Reuse a stable tag per logical
  action and avoid sharing one tag across unrelated work.
- Debounce keeps the last trigger. Throttle keeps the first trigger in the
  window. Mutex keeps the first running action and drops overlaps.
- These helpers log at `Level.FINE`. Set `Logger.root.level = Level.FINE` or
  lower when the task needs to inspect their behavior.

## Patterns

Debounce a search-style update:

```dart
FutureOr<SearchModel?> search(String query) => update(
  (old) async => old.copyWith(result: await api.search(query)),
  debounceTag: 'search',
  slowlyMs: 300,
);
```

Prevent overlapping refresh work:

```dart
FutureOr<UserModel?> refresh() => update(
  (old) async => old.copyWith(user: await api.loadUser()),
  mutexTag: 'refresh',
);
```

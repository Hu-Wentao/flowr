# fr_run_catching

Use this reference when a task asks to skip a FlowR view-model flow, catch
failures without throwing, or decide whether to use `runCatching`, `skpIf`, or
`skpNull` inside `FrViewModel` or `FrBlocViewModel`.

## Existing API

- `FrViewModel` and `FrBlocViewModel` inherit `runCatching`, `skpIf`, and
  `skpNull` from FlowR.
- `skpIf` and `skpNull` throw `SkipError`.
- In FlowR integration, `SkipError` is logged as `SKIPPED: ...` and returns
  `null`.
- Unhandled non-skip failures default to the normal FlowR failure path.

## Patterns

Use `runCatching` for shared side effects in a view model:

```dart
Future<bool?> syncDraft() => runCatching<bool>(
  () async {
    final draft = skpNull(state.draft, 'draft');
    await api.sync(draft);
    return true;
  },
);
```

Use `skpIf` or `skpNull` inside `update(...)` when the state flow should stop
quietly:

```dart
FutureOr<UserModel?> rename(String? nextName) => update((old) {
  final safeName = skpNull(nextName, 'nextName');
  skpIf(safeName == old.name, 'name unchanged');
  return old.copyWith(name: safeName);
});
```

## Rules

- Use `runCatching` for side effects or shared helper flows; do not replace a
  `FrBlocViewModel` event API with ad-hoc `runCatching` calls from widgets.
- Use `SkipError` semantics only for expected non-failure exits. Do not hide
  real validation or transport errors behind `skpIf`.
- Do not use deprecated `ignoreSkipError`; in current FlowR integration,
  SkipError is already handled explicitly.
- `runCatching` accepts scheduling tags; load `fr-slowly.md` when debounce,
  throttle, or mutex behavior matters.

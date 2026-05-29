# fr_disposal

Use this reference when a task asks about `DisposeMx`, `autoDispose`,
`autoDisposeNotifier`, `subBy`, Provider-owned disposal, `dispose`, or
`close`.

## Existing API

- `FrViewModel` and `FrBlocViewModel` inherit `DisposeMx` and
  `SubsAutoDisposeMx`.
- `autoDispose(subscription, {tag})` registers a `StreamSubscription` for
  cleanup.
- `autoDisposeNotifier(notifier, {tag})` registers an owned `ChangeNotifier`
  for cleanup.
- `subBy(tag)` reads back a tracked subscription.
- `FrProvider` disposes `DisposeMx` instances automatically and closes bloc
  `Closable` objects.

## Patterns

Register a stream subscription for cleanup:

```dart
class LocaleViewModel extends FrViewModel<LocaleModel> {
  LocaleViewModel(Stream<Locale> upstream) : super(const LocaleModel()) {
    autoDispose(upstream.listen(updateLocale), tag: 'locale-upstream');
  }
}
```

Register a notifier owned by the view model:

```dart
final focusNode = autoDisposeNotifier(FocusNode(), tag: 'search-focus');
```

## Rules

- If a view model is created by `FrProvider`, do not add extra manual disposal
  from the widget just to clean up the same resources.
- For manually owned view models outside `FrProvider`, call `dispose()` or
  `close()` when the instance is no longer used.
- `subBy(tag)` assumes the tag exists; only use it when the same task controls
  registration.
- Prefer `autoDisposeNotifier` for owned `FocusNode`, `TextEditingController`,
  or custom `ChangeNotifier` instances instead of bespoke cleanup registries.

# flowr_disposal

Use this reference when a task asks about `DisposeMx`, `autoDispose`,
`subBy`, `dispose`, or `close`.

## Existing API

- `DisposeMx` is the base disposal hook.
- `SubsAutoDisposeMx` adds `autoDispose(subscription, {tag})` and `subBy(tag)`.
- `autoDispose(...)` accepts nullable subscriptions and stores them by tag.
- `FlowR.close()` and `FlowB.close()` dispose helper resources once and then
  close the bloc/cubit.
- `FlowR.dispose()` and `FlowB.dispose()` are legacy sync wrappers around
  `close()`.

## Patterns

Register subscriptions for cleanup:

```dart
class Counter extends FlowR<int> {
  Counter(Stream<int> upstream) : super(0) {
    autoDispose(upstream.listen((event) => put(event)), tag: 'upstream');
  }
}
```

Read back a tracked subscription only when the task really needs it:

```dart
final StreamSubscription<int> sub = counter.subBy('upstream');
```

## Rules

- In manually owned pure Dart code, call `dispose()` or `close()` when the
  instance is no longer used.
- Do not manually cancel every tracked subscription right before `dispose()`
  unless the task needs early cancellation; `autoDispose` already handles final
  cleanup.
- `subBy(tag)` assumes the tag exists; only use it when the same task controls
  registration.
- Avoid adding a second parallel subscription-management layer when the class
  already extends `FlowR` or `FlowB`.

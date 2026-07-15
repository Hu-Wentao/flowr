# flowr_dart install

Use this reference when a task adds `flowr_dart` to a pure Dart package or
shared logic layer for the first time.

## Package setup

- Add `flowr_dart` to the package that directly defines `FlowR` or `FlowB`
  classes.
- Import `package:flowr_dart/flowr_dart.dart`.
- If the same feature also owns Flutter widgets, put Flutter MVVM code in a
  package that depends on `flowr`; keep `flowr_dart` for pure Dart layers.

## Minimal scaffold

```dart
import 'package:flowr_dart/flowr_dart.dart';

class Counter extends FlowR<int> {
  Counter() : super(0);

  Future<int?> increment() => update((old) => old + 1);
}

Future<void> main() async {
  Logger.root.level = Level.INFO;
  Logger.root.onRecord.listen(LoggableMx.devLogRecordPrinter);

  final counter = Counter();
  await counter.increment();
  print('counter: ${counter.value}');
  await counter.close();
}
```

## Rules

- Use `FlowR<T>` for method-driven state and `FlowB<E, S>` for event-driven
  state.
- Configure `Logger.root` once in the app or executable entrypoint, not inside
  every `FlowR` class.
- Call `dispose()` or `close()` when a manually owned instance is no longer
  used.
- Keep Flutter UI, `BuildContext`, and widget ownership out of `flowr_dart`
  packages.
- After install, load `references/flowr-update.md`,
  `references/flowr-run-catching.md`, or `references/flowr-logging.md` only
  when the task needs those deeper semantics.

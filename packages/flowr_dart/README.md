# FlowR Dart

State management based on **Reactive** programming for pure Dart.

## Install

```shell
dart pub add flowr_dart
```

> [!TIP]
> If you are using **Flutter**, it is highly recommended to use the [**flowr**](https://pub.dev/packages/flowr) package, which provides MVVM support and Flutter-specific features.

## Getting started

```dart
import 'package:flowr_dart/flowr_dart.dart';

class Counter extends FlowR<int> {
  @override
  final int initValue;

  Counter({required this.initValue});

  incrementCounter() => update((old) {
        logger('incrementCounter: $old');
        return old + 1;
      });

  incrementSlowly() => update(
        (old) async {
          await Future<void>.delayed(const Duration(milliseconds: 300));
          return old + 1;
        },
        mutexTag: 'counter',
      );
}

Future<void> main() async {
  Logger.root.level = Level.INFO;
  Logger.root.onRecord.listen(LoggableMx.devLogRecordPrinter);

  final counter = Counter(initValue: 0);
  await counter.incrementCounter();
  print('counter: ${counter.value}');

  counter.dispose();
}
```

## Core APIs

- `FlowR<T>` stores the current value in a `ValueStream<T>`.
- `update` reads the current value, runs an updater, catches failures, and calls `put` on success.
- `runCatching` is available for non-state work that should share the same error and skip handling.
- `skpIf` and `skpNull` throw `SkipError`, which stops the current flow without treating it as a failure.
- `autoDispose(subscription)` cancels registered stream subscriptions when `dispose` is called.

## Concurrency

`update` and `runCatching` can be scheduled with:

- `debounceTag`: wait until calls stop, then run the last call.
- `throttleTag`: run at most once during the configured window.
- `mutexTag`: run immediately and ignore overlapping calls with the same tag.
- `slowlyMs`: window size in milliseconds for debounce and throttle.

Tags are scoped to the `FlowR` instance. Use stable tag values for each independent action.

## ValueStream helpers

```dart
final names = counter.stream.distinctWith((count) => 'count: $count');
final evenValues = counter.stream.whereValue((count) => count.isEven);
```

- `mapValue` maps both stream events and synchronous `value` access.
- `distinctBy` keeps the latest emitted value for the selected key.
- `distinctWith` maps then de-duplicates mapped values.
- `whereValue` keeps the latest value that passed the filter. If no value has passed yet, `hasValue` is `false`, `valueOrNull` is `null`, and `value` throws.

## Logging

FlowR uses `package:logging`. Configure the root logger once in your app:

```dart
Logger.root.level = Level.INFO;
Logger.root.onRecord.listen(LoggableMx.devLogRecordPrinter);
```

Set `Logger.root.level = Level.FINE` to see normal `put`, debounce, throttle, mutex, and `SkipError` logs.

## Disposal

Call `dispose` when a `FlowR` instance is no longer used. This closes the state subject, cancels subscriptions registered through `autoDispose`, and disposes pending debounce, throttle, or mutex timers.

## Run example

> Demo **FlowR: for dart** [main.dart](https://github.com/Hu-Wentao/flowr/blob/master/examples/example/lib/main.dart)

```shell
# From workspace root
dart run examples/example/lib/main.dart
```

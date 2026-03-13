## Features
State management based on **Reactive** programming for pure dart.

## install
```shell
dart pub add flowr_dart
```

## Getting started

## Usage

```dart
class Counter extends FlowR<int> {
  @override
  final int initValue;

  Counter({required this.initValue});

  /// [update] is powerful:
  /// - Automatic state management (ValueStream)
  /// - Error handling (runCatching)
  /// - Concurrency control (debounce, throttle, mutex)
  incrementCounter() =>
      update((old) {
        logger('incrementCounter: $old');
        return old + 1;
      });
}

main() async {
  final counter = Counter(initValue: 0);
  await counter.incrementCounter();
  print('counter: ${counter.value}');
}
```

### Run example:

> Demo **FlowR: for dart** [main.dart](examples/example/lib/main.dart)

```shell
flutter run examples/example/main.dart
```
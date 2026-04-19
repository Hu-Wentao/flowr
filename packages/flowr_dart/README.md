# FlowR Dart
State management based on **Reactive** programming for pure dart.

## install
```shell
dart pub add flowr_dart
```

> [!TIP]
> If you are using **Flutter**, it is highly recommended to use the [**flowr**](https://pub.dev/packages/flowr) package, which provides MVVM support and Flutter-specific features.

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
  incrementCounter() => update((old) {
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

> Demo **FlowR: for dart** [main.dart](https://github.com/Hu-Wentao/flowr/blob/master/examples/example/lib/main.dart)

```shell
# From workspace root
dart run examples/example/lib/main.dart
```

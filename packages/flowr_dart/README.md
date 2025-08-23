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
# FlowR
State management for the MVVM pattern based on **Reactive** programming.

## install
```shell
dart pub add flowr
```

## Features

- Reactive State Management: power by rxdart
    - Independent of BuildContext
    - debounce / throttle
    - ...

- MVVM pattern
    - Support `StreamBuilder`
    - `FrStreamBuilder` / `FrView`

- One-way data flow

## Getting started

## Usage

```dart
/// 0. define Model

class CounterModel {
  int value;

  CounterModel(this.value)
}

/// 1. define ViewModel
class CounterViewModel extends FrViewModel<CounterModel> {
  @override
  final CounterModel initValue;

  CounterViewModel({required this.initValue});

  incrementCounter() =>
          update((old) {
            logger('incrementCounter: $old');
            return old..value += 1;
          });
}

/// ------------------------------------------
main() {
  /// 2.a get ViewModel instance
  final counter = CounterViewModel(initValue: CounterModel(0));

  /// 2.b Or use Provider
  FrProvider(
            (c) => CounterViewModel(initValue: CounterModel(1)),
    child: YourApp(), // ...
  );
// get instance
  final counter = context.read<CounterViewModel>();

  /// 2.c Or use DI
  GetIt.I.registerSingleton<Counter>(Counter(initValue: 0));
// get instance
  final counter = context.readGlobal<CounterViewModel>();

  /// ------------------------------------------
  /// 3.a use ViewModel by StreamBuilder
  StreamBuilder(
    stream: counter.stream,
    builder: (context, snapshot) {
      return Text(
        '${snapshot.data}',
        style: Theme
                .of(context)
                .textTheme
                .headlineMedium,
      );
    },
  );

  /// 3.b / 3.c use ViewModel by FrStreamBuilder / FrView
  FrStreamBuilder(
    vm: context.read<CounterViewModel>(),
    stream: (vm) => vm.stream,
    builder: (context, snapshot) {
      return Column(
        children: [
          Text('${snapshot.data}'),
          Text('Get vm by `snapshot.vm` [${snapshot.vm.runtimeType}]instance'),
        ],
      );
    },
  );
}
```

### Run example:

> Demo1 FlowR [main.dart](example/lib/main.dart)
```shell
flutter run example/main.dart
```
> Demo2 FlowR-MVVM [main_mvvm.dart](example/lib/main_mvvm.dart)
```shell
flutter run example/lib/main_mvvm.dart
```
> Demo3 FlowR-MVVM with Provider [main_mvvm_with_provider.dart](example/lib/main_mvvm_with_provider.dart)
```shell
flutter run example/lib/main_mvvm_with_provider.dart
```
> Demo4 FlowR-MVVM with DI [main_mvvm_with_di.dart](example/lib/main_mvvm_with_di.dart)
```shell
flutter run example/lib/main_mvvm_with_di.dart
```


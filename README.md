# FlowR 
state management package for the MVVM pattern based on reactive programming.

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



## Getting started

## Usage

```dart
/// 1. define ViewModel
class Counter extends FlowR<int> {
  @override
  final int initValue;

  Counter({required this.initValue});

  incrementCounter() => update((old) {
    logger('incrementCounter: $old');
    return old + 1;
  });
}

/// 2.a get ViewModel instance
final counter = Counter(initValue: 0);

/// 2.b Or use Provider
FrViewModelProvider(
(c) => UserViewModel(initValue: UserModel('foo', 1)),
child: // ...
)
final counter = context.read<UserViewModel>();

/// 2.c Or use DI
GetIt.I.registerSingleton<Counter>(Counter(initValue: 0));
final counter = context.readGlobal<UserViewModel>();
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


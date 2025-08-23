# FlowR MonoRepo

---

A predictable state management library that helps implement the BLoC design pattern.

| Package                                                                       | Desc                             | Pub                                                                                                |
|-------------------------------------------------------------------------------|----------------------------------|----------------------------------------------------------------------------------------------------|
| [flowr_dart](https://github.com/Hu-Wentao/bloc/tree/main/packages/flowr_dart) | Base FlowR for pure Dart         | [![pub package](https://img.shields.io/pub/v/flowr_dart.svg)](https://pub.dev/packages/flowr_dart) |
| [flowr](https://github.com/Hu-Wentao/bloc/tree/main/packages/flowr)           | MVVM State Managment for Flutter | [![pub package](https://img.shields.io/pub/v/flowr.svg)](https://pub.dev/packages/flowr)           |
| [flowr_arch](https://github.com/Hu-Wentao/bloc/tree/main/packages/flowr_arch) | IRepository, ITable ... for App  | [![pub package](https://img.shields.io/pub/v/flowr_arch.svg)](https://pub.dev/packages/flowr_arch) |

---

## Quick Start

```shell
dart pub add flowr
```

```dart
/// 1. define ViewModel
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

/// ------------------------------------------
main() {
  /// 2.a get ViewModel instance
  final counter = Counter(initValue: 0);

  /// 2.b Or use Provider
  FrProvider(
        (c) => UserViewModel(initValue: UserModel('foo', 1)),
    child: YourView(), // ...
  );
  
  final counter = context.read<UserViewModel>();

  /// 2.c Or use DI
  GetIt.I.registerSingleton<Counter>(Counter(initValue: 0));
  final counter = context.readGlobal<UserViewModel>();

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
    vm: context.read<UserViewModel>(),
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

> Demo3 FlowR-MVVM with
> Provider [main_mvvm_with_provider.dart](example/lib/main_mvvm_with_provider.dart)

```shell
flutter run example/lib/main_mvvm_with_provider.dart
```

> Demo4 FlowR-MVVM with DI [main_mvvm_with_di.dart](example/lib/main_mvvm_with_di.dart)

```shell
flutter run example/lib/main_mvvm_with_di.dart
```


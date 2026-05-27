# FlowR MonoRepo

---

A predictable state management library that helps implement the BLoC design pattern.

| Package                                                                                 | Desc                                                                                    | Pub                                                                                                          |
|-----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| [flowr_dart](https://github.com/Hu-Wentao/flowr/tree/main/packages/flowr_dart)           | Base FlowR library for pure Dart. Core logic for state and concurrency.                  | [![pub package](https://img.shields.io/pub/v/flowr_dart.svg)](https://pub.dev/packages/flowr_dart)           |
| [flowr](https://github.com/Hu-Wentao/flowr/tree/main/packages/flowr)                     | MVVM State Management for Flutter. Adds FrViewModel, FrView, and Providers.             | [![pub package](https://img.shields.io/pub/v/flowr.svg)](https://pub.dev/packages/flowr)                     |
| [fr_mvvm_env](https://github.com/Hu-Wentao/flowr/tree/main/packages/fr_mvvm_env)         | Environment management (Dev/Staging/Prod) with built-in Dropdown UI.                    | [![pub package](https://img.shields.io/pub/v/fr_mvvm_env.svg)](https://pub.dev/packages/fr_mvvm_env)         |
| [fr_mvvm_locale](https://github.com/Hu-Wentao/flowr/tree/main/packages/fr_mvvm_locale)   | Localization management with built-in Switch UI and easy context extensions.            | [![pub package](https://img.shields.io/pub/v/fr_mvvm_locale.svg)](https://pub.dev/packages/fr_mvvm_locale)   |
| [fr_mvvm_theme](https://github.com/Hu-Wentao/flowr/tree/main/packages/fr_mvvm_theme)     | Theme switching with ThemeExtension helpers, image scheme parsing, and JSON color conversion. | [![pub package](https://img.shields.io/pub/v/fr_mvvm_theme.svg)](https://pub.dev/packages/fr_mvvm_theme)     |
| [fr_mvvm_user](https://github.com/Hu-Wentao/flowr/tree/main/packages/fr_mvvm_user)       | User session/profile management with built-in Dropdown UI.                              | [![pub package](https://img.shields.io/pub/v/fr_mvvm_user.svg)](https://pub.dev/packages/fr_mvvm_user)       |
             
---

## MVVM Helper Packages

`fr_mvvm_theme` supports two common theme sources:

- Built-in app themes declared in Dart code.
- Dynamic themes loaded from downloaded or local JSON config files.

The example at
[`packages/fr_mvvm_theme/example`](packages/fr_mvvm_theme/example) demonstrates
both sources. It defines a built-in theme in code, then loads
`assets/theme_config.json` and converts JSON color strings through
`json_serializable` with `FrColorCvt`.

## Quick Start (FlowR)

```shell
dart pub add flowr
```

```dart
/// 0. define Model

class CounterModel {
  final int value;

  CounterModel(this.value);

  CounterModel copyWith({int? value}) => CounterModel(value ?? this.value);
}

/// 1. define ViewModel
class CounterViewModel extends FrViewModel<CounterModel> {
  CounterViewModel({required CounterModel initialState}) : super(initialState);

  incrementCounter() =>
      update((old) {
        logger('incrementCounter: $old');
        return old.copyWith(value: old.value + 1);
      });
}

/// ------------------------------------------
main() {
  /// 2.a create global ViewModel instance
  final counter = CounterViewModel(initialState: CounterModel(0));

  /// 2.b.1 Or use Provider register ViewModel instance
  FrProvider(
        (c) => CounterViewModel(initialState: CounterModel(1)),
    child: YourApp(), // ...
  );
  // 2.b.2 get instance from Provider
  final counter = context.read<CounterViewModel>();

  /// 2.c.1 Or use DI  register ViewModel instance
  GetIt.I.registerSingleton<CounterViewModel>(
    CounterViewModel(initialState: CounterModel(0)),
  );
  // 2.c.2 get instance
  final counter = context.readGlobal<CounterViewModel>();

  /// ------------------------------------------
  /// 3.a read Model from ViewModel by StreamBuilder
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

> Demo1 **FlowR: for dart** [main.dart](https://github.com/Hu-Wentao/flowr/blob/master/examples/example/lib/main.dart)

```shell
dart run examples/example/lib/main.dart
```

> Demo2 **FlowR-MVVM: for flutter** [main_mvvm.dart](https://github.com/Hu-Wentao/flowr/blob/master/examples/example/lib/main_mvvm.dart)

```shell
flutter run examples/example/lib/main_mvvm.dart
```

> Demo3 **FlowR-MVVM with
> Provider** [main_mvvm_with_provider.dart](https://github.com/Hu-Wentao/flowr/blob/master/examples/example/lib/main_mvvm_with_provider.dart)

```shell
flutter run examples/example/lib/main_mvvm_with_provider.dart
```

> Demo4 **FlowR-MVVM with DI** [main_mvvm_with_di.dart](https://github.com/Hu-Wentao/flowr/blob/master/examples/example/lib/main_mvvm_with_di.dart)

```shell
flutter run examples/example/lib/main_mvvm_with_di.dart
```

> Demo5 **FlowR-MVVM with Concurrency control (debounce/throttle/mutex)** [02_concurrency.mvvm.dart](examples/quick_start_mvvm/lib/02_concurrency.mvvm.dart)

```shell
flutter run examples/quick_start_mvvm/lib/02_concurrency.mvvm.dart
```

# FlowR MonoRepo

[![skills.sh](https://skills.sh/b/Hu-Wentao/flowr)](https://skills.sh/Hu-Wentao/flowr)

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

## Recommended Packages

| Package                                                                                 | Desc                                                                                    | Pub                                                                                                          |
|-----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| [efficient_dio_logger](https://github.com/Hu-Wentao/efficient_dio_logger)             | Dio interceptor for large-request projects with single-line JSON logging and automatic truncation for oversized values. | [![pub package](https://img.shields.io/pub/v/efficient_dio_logger.svg)](https://pub.dev/packages/efficient_dio_logger) |
| [drift_duckdb](https://github.com/Hu-Wentao/drift_duckdb)                             | A drift database implementation for DuckDB, allowing you to use DuckDB as a backend for drift. | [![pub package](https://img.shields.io/pub/v/drift_duckdb.svg)](https://pub.dev/packages/drift_duckdb) |

## Agent Skills

This repository ships local agent skills for FlowR Dart usage, Flutter MVVM
usage, and contract-first MVVM page scaffolding. See
[`skills/README.md`](skills/README.md) for the available skills and usage
examples.

---

## Quick Start (FlowR)

```shell
dart pub add flowr
```

### Basic Usage

```dart
class CounterModel {
  final int value;
  const CounterModel(this.value);

  CounterModel copyWith({int? value}) => CounterModel(value ?? this.value);
}

class CounterViewModel extends FrViewModel<CounterModel> {
  CounterViewModel() : super(const CounterModel(0));

  void increment() => update((old) => old.copyWith(value: old.value + 1));
}

final counterVm = CounterViewModel();

FrStreamBuilder(
  vm: counterVm,
  stream: (vm) => vm.stream,
  builder: (context, snapshot) {
    final value = snapshot.data?.value ?? 0;
    return Column(
      children: [
        Text('$value'),
        ElevatedButton(
          onPressed: counterVm.increment,
          child: const Text('Increment'),
        ),
      ],
    );
  },
);
```

Runnable example:
[main_mvvm.dart](https://github.com/Hu-Wentao/flowr/blob/master/examples/example/lib/main_mvvm.dart)

```shell
fvm flutter run examples/example/lib/main_mvvm.dart
```

### Advanced Usage

- [Pure Dart example](https://github.com/Hu-Wentao/flowr/blob/master/examples/example/lib/main.dart)
- [Provider integration](https://github.com/Hu-Wentao/flowr/blob/master/examples/example/lib/main_mvvm_with_provider.dart)
- [DI integration](https://github.com/Hu-Wentao/flowr/blob/master/examples/example/lib/main_mvvm_with_di.dart)
- [Concurrency control](examples/quick_start_mvvm/lib/02_concurrency.mvvm.dart)

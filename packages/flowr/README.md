# FlowR
State management for the MVVM pattern based on **Reactive** programming.

> [!TIP]
> This package is built on top of [**flowr_dart**](https://pub.dev/packages/flowr_dart), which provides the core reactive logic for pure Dart.

## install
```shell
dart pub add flowr
```

## Features

- Reactive State Management: powered by bloc/flutter_bloc
    - Independent of BuildContext
    - debounce / throttle
    - ...

- MVVM pattern
    - Support `StreamBuilder`
    - `FrView`, `FrListener`, and `FrConsumer`
    - `FrViewC` for Cubit-style view models and `FrViewB` for Bloc-style view models

- One-way data flow

## Getting started

## Usage

```dart
import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

/// 0. define Model
class CounterModel {
  final int value;

  CounterModel(this.value);

  CounterModel copyWith({int? value}) => CounterModel(value ?? this.value);

  @override
  String toString() => 'CounterModel(value: $value)';
}

/// 1. define ViewModel
class CounterViewModel extends FrViewModel<CounterModel> {
  @override
  final CounterModel initValue;

  CounterViewModel({required this.initValue});

  void incrementCounter() => update((old) {
        logger('incrementCounter: $old');
        return old.copyWith(value: old.value + 1);
      });
}

void main() {
  runApp(
    FrProvider(
      (c) => CounterViewModel(initValue: CounterModel(0)),
      child: const MaterialApp(home: CounterPage()),
    ),
  );
}

class CounterPage extends StatelessWidget {
  const CounterPage({super.key});

  @override
  Widget build(BuildContext context) {
    final counter = context.read<CounterViewModel>();

    return Scaffold(
      body: Center(
        child: FrView<CounterViewModel, CounterModel>(
          builder: (context, s, child) {
            return Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('${s.data}'),
                Text('Get vm by `s.vm` [${s.vm.runtimeType}] instance'),
              ],
            );
          },
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: counter.incrementCounter,
        child: const Icon(Icons.add),
      ),
    );
  }
}
```

`FlowR` now follows bloc equality semantics. Do not rely on in-place model mutation plus `put/update`; return a new state instance when the UI should rebuild. `FrConfig.initialize(emitEqualValues: true)` is no longer supported.

For GetIt DI, register a ViewModel and then read it with `context.read<T>()`.
`context.read<T>()` reads Provider first, then GetIt.

```dart
GetIt.I.registerLazySingleton<CounterViewModel>(
  () => CounterViewModel(initValue: CounterModel(0)),
);

final counter = context.read<CounterViewModel>();
```

## Additional information

### Extensions
Check out these specialized extensions for common MVVM patterns:
- [**fr_mvvm_env**](https://pub.dev/packages/fr_mvvm_env): Environment management (Dev/Staging/Prod).
- [**fr_mvvm_locale**](https://pub.dev/packages/fr_mvvm_locale): Localization management.
- [**fr_mvvm_user**](https://pub.dev/packages/fr_mvvm_user): User session/profile management.

### Run example:

> **FlowR-MVVM: for flutter** [main_mvvm.dart](https://github.com/Hu-Wentao/flowr/blob/master/examples/example/lib/main_mvvm.dart)

```shell
flutter run examples/example/lib/main_mvvm.dart
```

> **FlowR-MVVM with
> Provider** [main_mvvm_with_provider.dart](examples/example/lib/main_mvvm_with_provider.dart)

```shell
flutter run examples/example/lib/main_mvvm_with_provider.dart
```

> **FlowR-MVVM with DI** [main_mvvm_with_di.dart](examples/example/lib/main_mvvm_with_di.dart)

```shell
flutter run examples/example/lib/main_mvvm_with_di.dart
```

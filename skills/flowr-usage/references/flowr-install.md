# flowr install

Use this reference when a task adds `flowr` to a Flutter project for the first
time or wires the first `FrProvider` and `FrView` tree.

## Package setup

- Add `flowr` to the Flutter app or package that imports `FrViewModel`,
  `FrProvider`, `FrView`, `FrListener`, or `FrConsumer`.
- Import `package:flowr/flowr_mvvm.dart`.
- Do not import `flowr/src/...` from app code.
- `flowr` already depends on `flowr_dart`; only add a direct `flowr_dart`
  dependency when a separate pure Dart package imports it directly.

## Minimal scaffold

```dart
import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

class CounterModel {
  final int value;

  const CounterModel(this.value);

  CounterModel copyWith({int? value}) => CounterModel(value ?? this.value);
}

class CounterViewModel extends FrViewModel<CounterModel> {
  CounterViewModel() : super(const CounterModel(0));

  Future<CounterModel?> increment() =>
      update((old) => old.copyWith(value: old.value + 1));
}

void main() {
  runApp(
    FrProvider(
      (context) => CounterViewModel(),
      child: const MaterialApp(home: CounterPage()),
    ),
  );
}

class CounterPage extends StatelessWidget {
  const CounterPage({super.key});

  @override
  Widget build(BuildContext context) {
    final vm = context.read<CounterViewModel>();

    return Scaffold(
      body: Center(
        child: FrView<CounterViewModel, CounterModel>(
          builder: (context, snap, _) => Text('${snap.data.value}'),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: vm.increment,
        child: const Icon(Icons.add),
      ),
    );
  }
}
```

## Ownership and placement

- Put `FrProvider` above the subtree that owns the view model.
- Wrap `MaterialApp` when the state is app-wide; wrap a page subtree when the
  state is page-scoped.
- Use `FrProvider.value` for an existing instance and `FrProvider.multi` when a
  subtree owns multiple view models.
- Use `FrViewModel<M>` for method-driven state and `FrBlocViewModel<E, M>` when
  callers should dispatch events with `add(event)`.

## Rules

- `FrView`, `FrListener`, `FrConsumer`, and `FrMultiListener` all assume
  bloc-native non-replayable stream behavior.
- Return a new unequal state instance when the UI should rebuild.
- If the task also needs GetIt-backed ownership, load
  `references/fr-provider-di.md`.
- Shared `FlowR` and `FlowB` semantics come from this skill's resolved core
  instructions.

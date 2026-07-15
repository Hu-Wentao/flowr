# FlowR Flutter

Load this reference only when the resolver selects the Flutter route.

## Imports And Models

- Import `package:flowr/flowr_mvvm.dart` for Flutter MVVM code.
- `FrViewModel<M>` extends `FlowR<M>` for method-driven state.
- `FrBlocViewModel<E, M>` extends `FlowB<E, M>` for event-driven state; public
  callers use `add(event)`.
- Models should be immutable and compatible with the project's `FrModel`
  conventions. Equal-state suppression and non-replayable streams still apply.

```dart
class CounterModel {
  final int value;

  const CounterModel({this.value = 0});

  CounterModel copyWith({int? value}) =>
      CounterModel(value: value ?? this.value);
}

class CounterViewModel extends FrBlocViewModel<CounterEvent, CounterModel> {
  CounterViewModel() : super(const CounterModel()) {
    on<CounterIncremented>(
      (event, emit) => emit(state.copyWith(value: state.value + 1)),
    );
  }
}
```

## Ownership And UI

```dart
FrProvider(
  (context) => CounterViewModel(),
  child: FrView<CounterViewModel, CounterModel>(
    builder: (context, snap, child) => Text('${snap.data.value}'),
  ),
);
```

- `FrProvider` owns and disposes instances created by its factory. Use
  `FrProvider.value` only for an existing instance; use `FrProvider.multi` for
  several owned providers.
- Use `autoDisposeNotifier(notifier)` for an owned `ChangeNotifier`, such as a
  `FocusNode` or `TextEditingController`.
- `FrView` rebuilds UI from state. `FrListener` handles side effects,
  `FrConsumer` combines both, and `FrMultiListener` groups listeners.
- `FrSnap` is `(vm: VM, data: M)`.
- `FrProvider.di` and `FrUnion` are advanced opt-in patterns. Load their
  dedicated references only when the task explicitly uses them.

# FlowR Migration Notes

Use this reference for migration work after FlowR breaking changes.

## Equal Value Emission

FlowR follows bloc equality semantics. Calling `put(value)` or returning the
same/equal object from `update` does not emit.

Migrate code like this:

```dart
// Wrong: mutates current state, then emits an equal/same instance.
final items = value.items;
items.add(item);
put(value);
```

```dart
// Correct: creates new state and collection instances.
update((old) => old.copyWith(items: [...old.items, item]));
```

Do not add hidden config switches for equal-value re-emission. If a temporary
compatibility layer is explicitly requested, document the behavior and removal
plan in the user-facing response.

## Stream Semantics

`FlowR.stream`, `FlowB.stream`, `FrViewModel.stream`, and
`FrBlocViewModel.stream` use bloc-native semantics:

- new subscribers receive future events only;
- current state is read synchronously through `value` or `state`;
- do not restore `valueStream` overrides on FlowR view models.

Migrate code that expects replay:

```dart
final current = vm.value;
final sub = vm.stream.listen(handleNextState);
```

For widgets, prefer `FrView`, `FrListener`, or `FrConsumer` instead of manually
depending on replayable streams.

## API Names

- Use `FrBlocViewModel<E, M>` for event-driven Flutter MVVM.
- Do not generate `FrViewB` or `FrViewC`; those names were removed from the
  supported public API.
- Use `FlowR<T>` for method-driven pure Dart state and `FlowB<E, S>` for
  event-driven pure Dart state.

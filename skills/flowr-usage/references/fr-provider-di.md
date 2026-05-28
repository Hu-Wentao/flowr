# fr_provider_di

Use this reference when a task explicitly uses `FrProvider.di`, `GetIt`, or
DI-first FlowR ownership.

## API

- `FrProvider<VM>.di(...)` reads `VM` from `GetIt` and injects it into the
  widget tree.
- `FrProvider.readDI<T>({bool nothrow = false, GetIt? di})` reads a registered
  object directly from the DI container.
- `FrProvider.of<T>(context, onlyProvider: ...)` controls Provider-vs-DI lookup
  order.
- `FrProvider.value(...)` is the reuse path for an existing instance when the
  widget tree should not own construction.

## Pattern

```dart
final getIt = GetIt.I
  ..registerLazySingleton<CounterViewModel>(() => CounterViewModel());

FrProvider<CounterViewModel>.di(
  di: getIt,
  child: const CounterPage(),
);
```

```dart
final vm = FrProvider.of<CounterViewModel>(context, onlyProvider: true);
```

## Rules

- Prefer plain `FrProvider((context) => VM(), ...)` unless the app already
  chose DI ownership.
- Prefer `registerLazySingleton` for view models used with `FrProvider.di`; it
  matches the built-in dispose-and-reset behavior.
- `singleton` or other constant registrations are not auto-disposed by
  `FrProvider.di`; prefer `FrProvider.value` when reusing a long-lived shared
  instance.
- `onlyProvider: false` means Provider first then DI. `onlyProvider: true`
  means Provider only. `onlyProvider: null` means DI first then Provider.

# fr_union

Use this reference when a task explicitly uses `FrUnion`, `FrUnionViewModel`,
or `FrViewU`.

## API

- `FrConfig.initialize(frUnion: FrUnion.of({...}))` registers a global
  `FrUnionViewModel`.
- `FrUnion.of({...})` accepts plain model values. Use
  `FrUnion.ofTaggedModel({(model, 'tag')})` when the same model type appears
  more than once.
- `FrUnionViewModel` exposes `streamBy<M>(tag: ...)` and
  `updateBy<M>((old) => next, tag: ...)`.
- `FrViewU<M>` reads a typed value from `FrUnionViewModel`.

## Pattern

```dart
FrConfig.initialize(
  frUnion: FrUnion.of({CounterModel()}),
);
```

```dart
FrViewU<CounterModel>(
  builder: (context, snap, child) => Text('${snap.data}'),
);
```

```dart
FrConfig.initialize(
  frUnion: FrUnion.ofTaggedModel({
    (UserModel(name: 'A'), ''),
    (UserModel(name: 'B'), 'secondary'),
  }),
);
```

## Rules

- Treat `FrUnion` as a special global-state shortcut for small typed state sets,
  not as the default architecture for large app domains.
- Every model type and tag pair must have an initial value in `FrUnion`.
- `FrUnion.of({...})` must receive either only plain models or only tagged
  tuples; do not mix both forms in one set.
- Prefer extension methods on `FrUnionViewModel` to wrap domain actions instead
  of scattering `updateBy` calls through widgets.

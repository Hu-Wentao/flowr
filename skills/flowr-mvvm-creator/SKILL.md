---
name: flowr-mvvm-creator
description: Create or update FlowR MVVM code for Flutter projects using the flowr package. Use when adding .mvvm.dart files, FlowR models, FrViewModel or FrBlocViewModel view models, FrProvider registration, FrView/FrListener/FrConsumer widgets, or migrating MVVM code after FlowR breaking changes.
---

# FlowR-MVVM Creator

Create FlowR MVVM blocks that match the current `flowr` package in this
repository.

## First Checks

- Follow the project `AGENTS.md`: Flutter and Dart commands use `fvm`
  prefixes, for example `fvm flutter test` and `fvm dart format`.
- Before editing code, check `git status --short`. If there are unrelated
  uncommitted changes, ask the user whether to commit or ignore them before
  modifying files.
- Read the local package source before relying on memory:
  `packages/flowr/lib/flowr_mvvm.dart`,
  `packages/flowr/lib/src/view_model.dart`,
  `packages/flowr/lib/src/view.dart`, and
  `packages/flowr/CHANGELOG.md`.
- Prefer existing local MVVM layout and naming. Search for nearby `.mvvm.dart`
  files and mirror their module structure.

## FlowR 6.x Rules

FlowR is now bloc-native. Generate code for the APIs that exist in this repo:

- `FrViewModel<M>` is the method-driven ViewModel base. It extends the
  FlowR/Cubit-style core and exposes `value`, `state`, `stream`,
  `valueStream`, `put`, and protected `update`.
- `FrBlocViewModel<E, M>` is the event-driven ViewModel base. It extends the
  FlowB/Bloc-style core. Public UI actions should call `vm.add(Event())`;
  event handlers should emit new states.
- `FrView`, `FrListener`, and `FrConsumer` accept any
  `StateStreamable<M>` FlowR ViewModel, including `FrViewModel` and
  `FrBlocViewModel`.
- If a request mentions `FrViewC`, verify the class exists in the installed
  package before generating it. In this repository the method-driven class is
  `FrViewModel`.

### Breaking Change: Equal Values

FlowR follows Cubit equality semantics. `put(value)` and `update` do not emit
when `value == currentValue`.

Always create a new state/model instance when UI should rebuild:

```dart
class UserModel {
  final String name;
  final int age;

  const UserModel({required this.name, required this.age});

  UserModel copyWith({String? name, int? age}) => UserModel(
        name: name ?? this.name,
        age: age ?? this.age,
      );
}

class UserViewModel extends FrViewModel<UserModel> {
  UserViewModel() : super(const UserModel(name: 'guest', age: 0));

  FutureOr<UserModel?> setAge(int age) => update(
        (old) => old.copyWith(age: age),
      );
}
```

Do not generate this pattern for new code:

```dart
update((old) => old..age = old.age + 1); // wrong for FlowR 6.x
```

If a model uses value equality, the next model must be unequal by value. For
collection fields, create new `List`, `Map`, or `Set` instances instead of
mutating an existing collection in place.

Do not add `FrConfig.initialize(emitEqualValues: true)`. It is no longer a
compatibility escape hatch and throws in current FlowR. If a task requires any
compatibility setting for a breaking change, explicitly tell the user what was
changed and why; never hide compatibility behavior in generated code.

## File Layout

Default to this structure unless the existing app uses another convention:

```text
lib/
└── service/
    ├── app.mvvm.dart
    ├── db.service.dart
    └── user/
        ├── user.mvvm.dart
        └── cart/
            ├── cart.mvvm.dart
            └── item.mvvm.dart
```

- A `.mvvm.dart` file should contain the model, one ViewModel, and small
  reusable View widgets only when those widgets are tightly coupled to the
  state contract.
- Put cross-cutting services in `*.service.dart`. A service should extend
  `FrService` when it needs FlowR logging, `runCatching`, slowly helpers, or
  auto-disposal.
- Top-level app lifecycle state can live in `app.mvvm.dart`; authenticated
  session state can live under `user/`; lower-level user-owned state can live
  below that module.

## Generation Workflow

1. Identify the state contract: fields, async operations, external services,
   and UI events.
2. Choose the ViewModel base:
   - Use `FrViewModel<M>` for method-driven state such as `login()`,
     `refresh()`, `selectUser(user)`, or `setLocale(locale)`.
   - Use `FrBlocViewModel<E, M>` for event-driven state where the UI or other
     systems naturally dispatch events.
3. Make the model immutable: `final` fields, `const` constructor when possible,
   and `copyWith`.
4. Keep the ViewModel free of widget-only concerns. It may depend on services
   or repositories, but UI formatting belongs in widgets.
5. Register the ViewModel with `FrProvider`, `FrProvider.di`, or
   `FrProvider.value` depending on ownership.
6. Build UI with `FrView`, `FrListener`, `FrConsumer`, or `FrMultiListener`.
7. Format and validate with FVM commands.

## Templates

### Method-Driven MVVM

```dart
import 'dart:async';

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/widgets.dart';

class CounterModel {
  final int value;
  final bool loading;

  const CounterModel({
    this.value = 0,
    this.loading = false,
  });

  CounterModel copyWith({
    int? value,
    bool? loading,
  }) =>
      CounterModel(
        value: value ?? this.value,
        loading: loading ?? this.loading,
      );
}

class CounterViewModel extends FrViewModel<CounterModel> {
  CounterViewModel() : super(const CounterModel());

  FutureOr<CounterModel?> increment() => update(
        (old) => old.copyWith(value: old.value + 1),
      );

  Future<void> refresh() async {
    await update((old) => old.copyWith(loading: true));
    await runCatching(
      () async {
        // Load data here.
        return value.copyWith(loading: false);
      },
      onSuccess: put,
      onFailure: (error, stackTrace) {
        put(value.copyWith(loading: false));
        putError(error, stackTrace);
        return null;
      },
    );
  }
}

class CounterText extends StatelessWidget {
  const CounterText({super.key});

  @override
  Widget build(BuildContext context) {
    return FrView<CounterViewModel, CounterModel>(
      builder: (context, s, child) => Text('${s.data.value}'),
    );
  }
}
```

### Event-Driven MVVM

```dart
import 'package:flowr/flowr_mvvm.dart';

sealed class CounterEvent {
  const CounterEvent();
}

class CounterIncremented extends CounterEvent {
  const CounterIncremented();
}

class CounterModel {
  final int value;

  const CounterModel({this.value = 0});

  CounterModel copyWith({int? value}) => CounterModel(
        value: value ?? this.value,
      );
}

class CounterViewModel extends FrBlocViewModel<CounterEvent, CounterModel> {
  CounterViewModel() : super(const CounterModel()) {
    on<CounterIncremented>(
      (event, emit) => emit(state.copyWith(value: state.value + 1)),
    );
  }
}
```

Use it from UI like this:

```dart
context.read<CounterViewModel>().add(const CounterIncremented());
```

### Provider Registration

Provider owns and disposes the ViewModel:

```dart
FrProvider(
  (context) => CounterViewModel(),
  child: const CounterPage(),
);
```

Inject a GetIt-registered ViewModel into the widget tree:

```dart
GetIt.I.registerLazySingleton<CounterViewModel>(CounterViewModel.new);

FrProvider<CounterViewModel>.di(
  child: const CounterPage(),
);
```

Use `.value` only when ownership is elsewhere, such as dialogs or existing
instances:

```dart
FrProvider.value(
  value: context.read<CounterViewModel>(),
  child: const CounterDialog(),
);
```

## View Widgets

Use `FrView` for rendering:

```dart
FrView<CounterViewModel, CounterModel>(
  buildWhen: (previous, current) => previous.value != current.value,
  builder: (context, s, child) {
    return Text('${s.data.value}');
  },
);
```

Use `FrListener` for side effects:

```dart
FrListener<CounterViewModel, CounterModel>(
  listener: (context, previous, current, vm) {
    if (current.value > previous.value) {
      // Show a snack bar, navigate, etc.
    }
  },
  child: const CounterPageBody(),
);
```

Use `FrConsumer` when one widget needs both rendering and side effects:

```dart
FrConsumer<CounterViewModel, CounterModel>(
  listener: (context, previous, current, vm) {},
  builder: (context, s, child) => Text('${s.data.value}'),
);
```

## Validation

- Format changed Dart files with `fvm dart format <paths>`.
- Run focused tests with `fvm flutter test <package-or-test-path>` when Flutter
  widgets or providers are touched.
- Run `fvm dart analyze` or the package-specific analyzer command when shared
  APIs are changed.
- When editing only this skill, at minimum re-read `SKILL.md` and check
  `git diff -- skills/flowr-mvvm-creator/SKILL.md` for accidental stale API
  names or hidden compatibility instructions.

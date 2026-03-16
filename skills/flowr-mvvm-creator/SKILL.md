---
name: flowr-mvvm-creator
description: Create a reactive MVVM state management module or business logic service in a Flutter project using the `flowr` and `flowr_dart` packages. Trigger this whenever the user wants to add, generate, or set up a new ViewModel (.vm.dart), Model, or Service (.srv.dart) in `lib/service/`, or when they ask about implementing the FlowR-MVVM pattern.
---

# FlowR-MVVM Creator
This skill provides comprehensive guidance for architecting and implementing state management using the FlowR-MVVM pattern.

## Core Concepts

FlowR-MVVM is a reactive state management framework built on `rxdart`. It enforces a one-way data flow and decouples business logic from the UI.

### 1. The Model (M)
The state container. It should be a plain object or a dedicated class.
- **Mutable vs Immutable**: While `flowr` supports both, using immutable models or deep-copying in `update` is recommended for predictability.

### 2. The ViewModel (VM)
Manages the state and provides methods for the View to trigger actions.
- **Inheritance**: Extends `FrViewModel<M>`.
- **Initialization**: Must implement `initValue`.
- **Updates**: Use the `update` method to modify state. It handles error catching and concurrency.
- **Lifecycle**: ViewModels are automatically disposed of when the providing `FrProvider` is removed from the tree.

### 3. The View (V)
The UI layer that listens to the ViewModel.
- **Widgets**: `FrView`, `FrStreamBuilder`, `ValueStreamBuilder`, `ValueStreamListener`.
- **DI**: Access ViewModels via `context.read<VM>()` (Provider-based) or `context.readGlobal<VM>()` (GetIt-based).

---

## Anatomy of a FlowR-MVVM Module

Modules are primarily organized within the `lib/service/` directory, following strict naming conventions for clarity and separation of concerns.

### 1. State Management (`lib/service/<name>.vm.dart`)
Contains the Model (M) and ViewModel (VM).
- **Views**: Simple View widgets can be included here for convenience. However, it is strongly recommended to place complex or standard views in the UI layer (e.g., `lib/pages/`).

### 2. Pure Services (`lib/service/<name>.srv.dart`)
Contains pure service logic, such as database handlers (`db.srv.dart`) or API clients.
- **Inheritance**: MUST inherit from `FrService` (or `IService` with `DisposeMx`) to ensure consistent lifecycle management.
- **Content**: Business logic that does not necessarily manage a reactive state Model.

### Directory Structure Example
```
lib/
├── service/
│   ├── user/
│   │   ├── user.vm.dart (Model + ViewModel + Optional simple View)
│   │   └── user_api.srv.dart (User-related API service)
│   ├── db.srv.dart (Global database service)
├── pages/
│   └── user/
│       └── profile_page.dart (Complex View/UI layer using FrView)
```

### Implementation Template (`lib/service/user.vm.dart`)

```dart
import 'package:flowr/flowr_mvvm.dart';

// --- Model ---
class UserModel {
  String name;
  int age;
  UserModel(this.name, this.age);
}

// --- ViewModel ---
class UserViewModel extends FrViewModel<UserModel> {
  @override
  final UserModel initValue;

  UserViewModel({required this.initValue});

  // Basic update
  void updateName(String name) => update((old) => old..name = name);

  // Concurrency controlled update (Debounce)
  void search(String query) => update(
    (old) async {
      // search logic...
      return old;
    },
    debounceTag: 'search_user',
    slowlyMs: 300,
  );

  // Conditional update (Skip)
  void updateAge(int? age) => update((old) {
    final newAge = skpNull(age, 'Age cannot be null');
    skpIf(newAge < 0, 'Age cannot be negative');
    return old..age = newAge;
  });
}

// --- View ---
class UserView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return FrView<UserViewModel, UserModel>(
      builder: (context, snapshot) {
        final data = snapshot.data!;
        return Text('User: ${data.name}, Age: ${data.age}');
      },
    );
  }
}
```

---

## Advanced Features

### 1. Concurrency Control
The `update` method supports several concurrency tags:
- `debounceTag`: Postpones execution until after a specified silence period (`slowlyMs`).
- `throttleTag`: Limits execution frequency to once per `slowlyMs`.
- `mutexTag`: Ensures only one instance of the task runs at a time (exhaustive behavior).

### 2. Error & Flow Control
- `skpIf(condition, reason)`: Throws a `SkipError` if the condition is met, silently canceling the `update`.
- `skpNull(obj, reason)`: Ensures a value is non-null or cancels the update.
- `runCatching`: For wrapping non-state-updating logic with similar error handling and concurrency control.

### 3. Dependency Injection
- **Provider**: `FrProvider(create: (c) => MyVM(), child: ...)`
- **GetIt**: `FrProvider.di(child: ...)` (Requires `GetIt.I.registerSingleton<MyVM>(...)`)
- **Reading**: `context.read<MyVM>()` reads from Provider first, then Global (GetIt) by default.

### 4. Alternative: ChangeNotifier Integration
If you need to use `Consumer<VM>` or standard `ChangeNotifierProvider`, use `FrChangeNotifierVM`:
```dart
class MyLegacyVM extends FrChangeNotifierVM<MyModel> {
  @override
  final MyModel initValue;
  MyLegacyVM({required this.initValue});
}

// Usage in UI
Consumer<MyLegacyVM>(
  builder: (context, vm, child) => Text(vm.value.name),
)
```

### 5. Mixins
- `NtfAutoDisposeMx`: Call `autoDisposeNotifier(myFocusNode)` to automatically dispose of Flutter objects.
- `SubsAutoDisposeMx`: Call `autoDispose(mySubscription)` for manual stream subscriptions.
- `SlowlyMx`: Access raw `debounce`, `throttle`, and `mutex` methods.

---

## Best Practices

1.  **Surgical Updates**: Keep `update` blocks small and focused.
2.  **Explicit Tags**: Use unique `String` tags for `debounce`, `throttle`, and `mutex` within a ViewModel.
3.  **Logger Usage**: Use `logger('message')` inside the ViewModel for automated logging with stack trace information.
4.  **Testing**: Mix in `TestLoggableMx` in your tests to see `logger` output in the console.
5.  **Reactive Extensions**: Use `distinctBy` or `mapValue` on `vm.stream` for fine-grained UI rebuilding.

```dart
// Optimized Rebuild
ValueStreamBuilder<UserModel, int>(
  stream: vm.stream.distinctBy((user) => user.age),
  builder: (context, user, _) => Text('Age: ${user.age}'),
)
```

# FlowR MVVM Patterns

These patterns are distilled from the package examples and source code so the skill remains self-contained after installation in a user project. Do not assume the user's project contains this repository's `examples/` directory.

## Minimal Scalar ViewModel

Use scalar state for one-value state such as counters, flags, selected indexes, search text, or a simple theme mode.

```dart
import 'package:flowr/flowr_mvvm.dart';

class CounterVM extends FrViewModel<int> {
  @override
  final int initValue;

  CounterVM(this.initValue);

  Future<void> incrementCounter() async => update((old) => old + 1);
}
```

Direct use:

```dart
final counter = CounterVM(0);
await counter.incrementCounter();
counter.value; // 1
counter.dispose();
```

## Provider-Scoped ViewModel

Use `FrProvider` when the ViewModel lifetime should follow the widget tree.

```dart
FrProvider(
  (context) => UserViewModel(
    initValue: const UserModel(name: 'foo', age: 1),
  ),
  child: const MaterialApp(home: UserPage()),
);
```

Read the VM from UI actions:

```dart
context.read<UserViewModel>().updateAge(2);
```

## Immutable Model

Prefer immutable model classes for generated feature state.

```dart
class UserModel {
  final String name;
  final int age;

  const UserModel({required this.name, required this.age});

  UserModel copyWith({
    String? name,
    int? age,
  }) =>
      UserModel(
        name: name ?? this.name,
        age: age ?? this.age,
      );

  @override
  String toString() => 'UserModel(name: $name, age: $age)';
}

class UserViewModel extends FrViewModel<UserModel> {
  @override
  final UserModel initValue;

  UserViewModel({required this.initValue});

  void updateAge([int? age]) => update((old) {
        logger('age: $age');
        return old.copyWith(age: age ?? old.age + 1);
      });

  void updateName(String name) => update(
        (old) {
          skpIf(name == old.name, 'name unchanged');
          return old.copyWith(name: name);
        },
        logging: (previous, current) =>
            'Name Change ${previous.name} => ${current.name}',
      );

  Future<void> updateNameAsync(String name) async => await update((old) async {
        await Future.delayed(const Duration(seconds: 1));
        return old.copyWith(name: name);
      });
}
```

## Mutable Model

Use mutable model updates only when matching an existing project style.

```dart
class UserModel {
  String name;
  int age;

  UserModel(this.name, this.age);

  @override
  String toString() => 'UserModel(name: $name, age: $age)';
}

class UserViewModel extends FrViewModel<UserModel> {
  @override
  final UserModel initValue;

  UserViewModel({required this.initValue});

  void addAge(int amount) => update((old) {
        logger('addAge: $amount');
        return old..age = old.age + amount;
      });
}
```

## FrView

`FrView` reads the VM via `context.read<VM>()` and rebuilds from the VM stream. The builder receives a record with `s.vm` and `s.data`.

```dart
FrView<UserViewModel, UserModel>(
  builder: (context, s, child) {
    return Column(
      children: [
        Text('${s.data}'),
        Text('VM: ${s.vm.runtimeType}'),
      ],
    );
  },
);
```

Limit rebuilds with `buildWhen`:

```dart
FrView<UserViewModel, UserModel>(
  buildWhen: (previous, current) => previous.name != current.name,
  builder: (context, s, child) => Text(s.data.name),
);
```

## FrMultiProvider

Use `FrMultiProvider` for multiple FlowR services or VMs.

```dart
FrMultiProvider(
  providers: [
    FrProvider(
      (context) => UserViewModel(
        initValue: const UserModel(name: 'foo', age: 1),
      ),
    ),
  ],
  child: const MaterialApp(home: UserPage()),
);
```

## GetIt / Injectable DI

Use DI when the user's project already uses `get_it` / `injectable`, or when a VM must be shared outside a widget subtree.

```dart
import 'package:flowr/flowr_mvvm.dart';
import 'package:my_app/di.config.dart';

@lazySingleton
class UserViewModel extends FrViewModel<UserModel> {
  @override
  UserModel get initValue => const UserModel(name: 'foo', age: 1);
}

@InjectableInit()
configureDI() => GetIt.I.init();
```

Initialize before `runApp`:

```dart
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  configureDI();
  runApp(const MyApp());
}
```

Expose the DI instance to a subtree:

```dart
FrProvider<UserViewModel>.di(
  child: const UserPage(),
);
```

After adding injectable annotations, run:

```shell
fvm dart run build_runner build
```

Do not generate `*.config.dart` manually.

## Concurrency Control

`update` and `runCatching` support FlowR's `slowly` tags.

```dart
class ConcurrencyVM extends FrViewModel<int> {
  @override
  int get initValue => 0;

  Future<void> addWithMutex() async {
    await update(
      (old) async {
        logger('Mutex: start');
        await Future.delayed(const Duration(seconds: 1));
        logger('Mutex: end');
        return old + 1;
      },
      mutexTag: 'add',
    );
  }

  void addWithDebounce() {
    update(
      (old) => old + 1,
      debounceTag: 'add',
      slowlyMs: 500,
    );
  }

  void addWithThrottle() {
    update(
      (old) => old + 1,
      throttleTag: 'add',
      slowlyMs: 500,
    );
  }
}
```

Use unique tags per operation within a VM, such as `profile_refresh`, `profile_search`, or `cart_checkout`.

## Service

Use `FrService` for lifecycle-aware business logic that does not itself need to be UI state.

```dart
import 'package:flowr/flowr_mvvm.dart';

class WeatherApiService extends FrService {
  Future<void> fetch() async {
    await runCatching(
      () async {
        logger('fetch weather');
        // TODO: call API/client/repository.
      },
      mutexTag: 'weather_fetch',
    );
  }
}
```

Inject services into VMs through constructors.

## Unit Test

Test ViewModels directly unless widget behavior is the target.

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:my_app/service/user/user.vm.dart';

void main() {
  test('updateAge changes age', () async {
    final vm = UserViewModel(
      initValue: const UserModel(name: 'foo', age: 1),
    );

    vm.updateAge(3);

    expect(vm.value.age, 3);
    vm.dispose();
  });
}
```

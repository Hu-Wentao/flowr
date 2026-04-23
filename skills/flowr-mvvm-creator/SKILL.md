---
name: flowr-mvvm-creator
description: Create FlowR MVVM modules for Flutter: `.vm.dart` ViewModels, state Models, optional simple Views, Provider/GetIt DI wiring, and `.srv.dart` services under `lib/service/`. Trigger when the user wants to add, generate, scaffold, or explain a FlowR-MVVM state module or service. Do not trigger for generic Flutter pages, generic provider usage, or test-only requests unless a FlowR ViewModel/module is also being created.
---

# FlowR MVVM Creator

Use this skill to create or explain FlowR MVVM modules in the user's Flutter project. This skill must be self-contained after installation: do not assume the target project contains this repository's `examples/` directory or package example files.

## References

Load bundled references only when needed:

- `references/mvvm_patterns.md`: distilled FlowR MVVM patterns for scalar VMs, immutable/mutable models, `FrView`, provider, DI, concurrency, services, and tests.
- `references/mvvm_components.md`: packaged `fr_mvvm_env`, `fr_mvvm_user`, and `fr_mvvm_locale` usage. Read it for environment, user, locale, language, account switcher, API host switcher, or app settings state.

Prefer packaged components before generating a custom VM for environment/user/locale domains.

## Generation Script

Prefer the bundled script for new modules instead of hand-writing boilerplate:

```shell
uv run python <skill-dir>/scripts/generate_mvvm.py profile \
  --field username:String=guest \
  --field avatarUrl:String \
  --with-view
```

Resolve `<skill-dir>` to this skill's installed directory, not the user's project directory. When using this skill, bundled scripts and references live beside `SKILL.md`.

Common options:

- `--state immutable|mutable|scalar`: generated state shape; default is `immutable`.
- `--field name:Type=default`: add a model field. Omit `=default` to make the constructor argument required in non-DI code.
- `--scalar-type int --scalar-initial 0`: scalar VM state, such as counters or theme indexes.
- `--with-view`: add a small `StatelessWidget` demo view in the VM file.
- `--with-service`: add `<feature>_api.srv.dart` and inject the service into the VM constructor.
- `--di`: generate an injectable/GetIt-friendly VM with `@lazySingleton` and `initValue` getter.
- `--output-dir lib/service/<feature>`: override the target directory.
- `--dry-run`: print generated files before writing.

After generation, inspect the output and adapt business methods, validation, service calls, and UI placement to the app.

## Workflow

1. Identify the module name, target directory, state fields, actions, and whether the user wants a pure service, a ViewModel, a simple View, DI wiring, or tests.
2. Check whether an existing packaged component fits: environment/API host uses `fr_mvvm_env`; user/account switching uses `fr_mvvm_user`; locale/language uses `fr_mvvm_locale`. Load `references/mvvm_components.md` for those cases.
3. Prefer the bundled `scripts/generate_mvvm.py` for initial custom files, resolving it relative to this skill's installed directory, then patch the generated Dart for domain-specific behavior.
4. Prefer `lib/service/<feature>/<feature>.vm.dart` for feature state and `lib/service/<feature>/<feature>_api.srv.dart` or `<feature>.srv.dart` for pure services. Use `lib/service/db.srv.dart` only for truly global services.
5. Import `package:flowr/flowr_mvvm.dart` for standard MVVM code. Import `package:flowr/flowr_mvvm_support.dart` only when using `FrChangeNotifierVM` or provider `Consumer`.
6. Generate small, explicit state transitions through public ViewModel methods. Keep UI widgets optional and simple; suggest `lib/pages/<feature>/` for complex screens.
7. If editing an existing app, match its current dependency injection and folder style. If no style exists, default to `FrProvider`/`FrMultiProvider`, not global singletons.
8. After creating files, run formatting and the narrowest relevant Flutter/Dart validation available through `fvm` if this is a real repo edit.

## Core API

- `FrViewModel<M>` extends FlowR and owns a seeded `ValueStream<M>`.
- Implement initial state as either `@override final M initValue;` with a constructor or `@override M get initValue => ...;`.
- Read state with `vm.value`; listen with `vm.stream`.
- Update state with `update((old) => newValue)`. Await `update` when the updater is `async`.
- `FrProvider((c) => MyVM(...), child: ...)` creates and disposes the VM with the widget tree.
- `FrMultiProvider(providers: [...], child: ...)` groups multiple FlowR providers.
- `context.read<MyVM>()` reads Provider first, then GetIt. `context.read<MyVM>(onlyProvider: true)` forces Provider. `context.read<MyVM>(onlyProvider: null)` checks GetIt first.
- `FrView<MyVM, MyModel>(builder: (context, s, child) => ...)` exposes `s.data` and `s.vm`.
- `FrListener` handles side effects; `FrConsumer` combines listener and builder.
- `FrService` is for lifecycle-aware non-UI services and already includes logging, concurrency helpers, `runCatching`, and subscription auto-dispose.

## ViewModel Templates

### Minimal Scalar State

Use for counters, toggles, search text, theme mode, and simple values.

```dart
import 'package:flowr/flowr_mvvm.dart';

class CounterVM extends FrViewModel<int> {
  @override
  final int initValue;

  CounterVM(this.initValue);

  Future<void> increment() async => update((old) => old + 1);
  void reset() => update((old) => initValue);
}
```

### Immutable Model State

Default to immutable fields and `copyWith` for multi-field feature state.

```dart
import 'package:flowr/flowr_mvvm.dart';

class ProfileModel {
  final String username;
  final String avatarUrl;
  final bool loading;

  const ProfileModel({
    required this.username,
    required this.avatarUrl,
    this.loading = false,
  });

  ProfileModel copyWith({
    String? username,
    String? avatarUrl,
    bool? loading,
  }) =>
      ProfileModel(
        username: username ?? this.username,
        avatarUrl: avatarUrl ?? this.avatarUrl,
        loading: loading ?? this.loading,
      );

  @override
  String toString() =>
      'ProfileModel(username: $username, avatarUrl: $avatarUrl, loading: $loading)';
}

class ProfileViewModel extends FrViewModel<ProfileModel> {
  @override
  final ProfileModel initValue;

  ProfileViewModel({required this.initValue});

  void updateUsername(String username) => update((old) {
        skpIf(username == old.username, 'username unchanged');
        return old.copyWith(username: username);
      });

  Future<void> refresh() async => update(
        (old) async {
          logger('refresh profile');
          return old.copyWith(loading: false);
        },
        mutexTag: 'profile_refresh',
        logging: (p, c) => 'Profile refresh ${p.loading} => ${c.loading}',
      );
}
```

Use mutable models only when matching existing project style:

```dart
class UserModel {
  String name;
  int age;

  UserModel(this.name, this.age);
}

class UserViewModel extends FrViewModel<UserModel> {
  @override
  final UserModel initValue;

  UserViewModel({required this.initValue});

  void addAge(int value) => update((old) => old..age = old.age + value);
}
```

## View Templates

### Provider-Scoped Simple View

```dart
class ProfileView extends StatelessWidget {
  const ProfileView({super.key});

  @override
  Widget build(BuildContext context) {
    return FrProvider(
      (c) => ProfileViewModel(
        initValue: const ProfileModel(username: 'guest', avatarUrl: ''),
      ),
      child: FrView<ProfileViewModel, ProfileModel>(
        builder: (context, s, child) {
          return Text('${s.data.username} ${s.data.avatarUrl}');
        },
      ),
    );
  }
}
```

For complex views, keep the VM in `lib/service/<feature>/<feature>.vm.dart` and put UI in `lib/pages/<feature>/`.

### Reading Actions From UI

```dart
FloatingActionButton(
  onPressed: () => context.read<ProfileViewModel>().refresh(),
  child: const Icon(Icons.refresh),
)
```

### Rebuild Filtering

```dart
FrView<ProfileViewModel, ProfileModel>(
  buildWhen: (p, c) => p.username != c.username,
  builder: (context, s, child) => Text(s.data.username),
)
```

## Provider And DI

Default provider setup:

```dart
return FrMultiProvider(
  providers: [
    FrProvider(
      (c) => ProfileViewModel(
        initValue: const ProfileModel(username: 'guest', avatarUrl: ''),
      ),
    ),
  ],
  child: const MaterialApp(home: ProfilePage()),
);
```

GetIt/injectable setup when the project already uses DI or the user asks for DI:

```dart
import 'package:flowr/flowr_mvvm.dart';
import 'package:my_app/di.config.dart';

@lazySingleton
class ProfileViewModel extends FrViewModel<ProfileModel> {
  @override
  ProfileModel get initValue =>
      const ProfileModel(username: 'guest', avatarUrl: '');
}

@InjectableInit()
configureDI() => GetIt.I.init();
```

Then initialize DI before `runApp` and read with `context.read<ProfileViewModel>()` or use `FrProvider<ProfileViewModel>.di()` to expose the DI instance to a subtree. After adding injectable annotations, run `fvm dart run build_runner build`.

## Services

Use `.srv.dart` for business logic that does not own UI state or for dependencies used by VMs.

```dart
import 'package:flowr/flowr_mvvm.dart';

class WeatherApiService extends FrService {
  Future<WeatherDto?> fetchCurrent(String city) async {
    return await runCatching<WeatherDto>(
      () async {
        // TODO: call API client.
        return WeatherDto(city: city, temperature: 0);
      },
      mutexTag: 'weather_fetch_$city',
    );
  }
}

class WeatherDto {
  final String city;
  final int temperature;

  const WeatherDto({required this.city, required this.temperature});
}
```

When a VM depends on a service, prefer constructor injection:

```dart
class WeatherViewModel extends FrViewModel<WeatherModel> {
  final WeatherApiService api;

  @override
  final WeatherModel initValue;

  WeatherViewModel({required this.api, required this.initValue});
}
```

## Concurrency And Flow Control

Use tags that are unique within the VM.

```dart
Future<void> save() async => update(
      (old) async {
        logger('save start');
        // await repository.save(old);
        return old;
      },
      mutexTag: 'profile_save',
    );

void search(String query) => update(
      (old) => old.copyWith(query: query),
      debounceTag: 'profile_search',
      slowlyMs: 300,
    );

void trackTap() => update(
      (old) => old.copyWith(tapCount: old.tapCount + 1),
      throttleTag: 'profile_tap',
      slowlyMs: 500,
    );
```

- `mutexTag`: ignore overlapping async executions.
- `debounceTag`: execute after quiet time.
- `throttleTag`: execute at most once per interval.
- `skpIf(condition, reason)`: skip an update without treating it as failure.
- `skpNull(value, reason)`: unwrap nullable input or skip.
- `logging: (previous, current) => ...`: log meaningful state transitions.
- `logger('message')`: log from VM/service with FlowR context.

## Tests

When creating tests with a module, test the VM directly unless widget behavior is specifically requested.

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:my_app/service/profile/profile.vm.dart';

void main() {
  test('updateUsername changes profile name', () async {
    final vm = ProfileViewModel(
      initValue: const ProfileModel(username: 'guest', avatarUrl: ''),
    );

    vm.updateUsername('wyatt');

    expect(vm.value.username, 'wyatt');
    vm.dispose();
  });
}
```

## Quality Rules

- Keep VM methods named after user/business actions, not UI events: `refresh`, `save`, `updateUsername`, `selectItem`.
- Keep `update` blocks focused and side effects explicit.
- Prefer immutable `copyWith` models for generated code.
- Await async `update` calls in VM methods and tests.
- Dispose manually created VMs in tests.
- Do not put complex screens in service files; only include small demo/simple widgets when requested.
- Do not generate build output such as `*.config.dart`; instruct the user or run build_runner in the project when needed.

## MVVM Component Generation Rules

Use these rules when scripting or manually generating FlowR MVVM components:

1. Reuse packaged components first for common app state: `fr_mvvm_env`, `fr_mvvm_user`, and `fr_mvvm_locale` are documented in `references/mvvm_components.md`.
2. File naming: feature state goes to `lib/service/<feature>/<feature>.vm.dart`; pure API/business services go to `lib/service/<feature>/<feature>_api.srv.dart` unless the service is global.
3. Class naming: `<Feature>Model` stores state, `<Feature>ViewModel` extends `FrViewModel<<Feature>Model>`, and `<Feature>ApiService` extends `FrService`.
4. State shape: use scalar state only for one-value modules; use immutable model classes with `final` fields, `const` constructor, `copyWith`, and `toString` for normal feature state; use mutable models only to match existing code.
5. Initialization: non-DI VMs expose `@override final M initValue` and accept it in the constructor; DI VMs use `@lazySingleton`, a no-arg or injectable constructor, and `@override M get initValue => ...`.
6. Updates: every generated field gets an `update<FieldName>` method; methods call `update`, guard no-op writes with `skpIf`, and return `old.copyWith(...)` for immutable models.
7. Async actions: generated refresh/fetch/save actions use `Future<void>`, await async `update` or `runCatching`, log with `logger`, and use stable tags such as `<feature>_refresh` or `<feature>_fetch`.
8. Views: generated views are minimal demos only. They wrap local VMs with `FrProvider` or DI VMs with `FrProvider<VM>.di`, then render state through `FrView<VM, M>` and `s.data`.
9. Services: generated `.srv.dart` files contain lifecycle-aware service classes extending `FrService`; VMs receive services through constructor injection.
10. DI codegen: generate annotations and instructions, not `*.config.dart`; run `fvm dart run build_runner build` after editing DI modules.
11. Validation: format generated Dart and run the narrowest relevant test. For generated VM tests, instantiate the VM directly, call action methods, assert `vm.value`, then dispose the VM.

# Packaged FlowR MVVM Components

This repo includes packaged MVVM components for common app state. Prefer these packages before generating a custom ViewModel for environment, user, or locale selection.

## Selection Guide

- Use `fr_mvvm_env` for app environment selection such as development, staging, production, API host, or tenant.
- Use `fr_mvvm_user` for current user selection, user token state, or a debug/test user switcher.
- Use `fr_mvvm_locale` for locale/language selection and locale string formatting.
- Wrap each component ViewModel with `FrProvider` or expose a DI instance with `FrProvider<VM>.di`.
- The packaged views are small `MenuAnchor` selector widgets; put larger app settings screens in `lib/pages/...` and embed the packaged selector there.

## fr_mvvm_env

Package import:

```dart
import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:fr_mvvm_env/fr_mvvm_env.dart';
```

Core API:

- `EnvModel`: base state model with `env` id.
- `IEnvViewModel<M extends EnvModel>`: base VM contract with `Iterable<M> get all` and `updateEnv(M? env)`.
- `FrEnvViewModel`: simple concrete VM for `EnvModel`.
- `FrEnvDropdownView<VM, M>`: selector view.

Simple built-in model:

```dart
class AppEnvViewModel extends FrEnvViewModel {
  AppEnvViewModel()
      : super(
          const EnvModel(env: 'Development'),
          all: const [
            EnvModel(env: 'Development'),
            EnvModel(env: 'Staging'),
            EnvModel(env: 'Production'),
          ],
        );
}

FrProvider(
  (context) => AppEnvViewModel(),
  child: const MaterialApp(
    home: Scaffold(
      body: Center(child: FrEnvDropdownView<AppEnvViewModel, EnvModel>()),
    ),
  ),
);
```

Custom env model with extra fields:

```dart
class MyEnv extends EnvModel {
  final String url;

  const MyEnv({required super.env, required this.url});

  @override
  String toString() => 'MyEnv(env: $env, url: $url)';
}

class MyEnvViewModel extends IEnvViewModel<MyEnv> {
  @override
  Iterable<MyEnv> all = const [
    MyEnv(env: 'dev', url: 'http://localhost:8080'),
    MyEnv(env: 'uat', url: 'http://localhost:9090'),
  ];

  @override
  MyEnv get initValue => const MyEnv(
        env: 'dev',
        url: 'http://localhost:8080',
      );
}
```

Custom selector button:

```dart
FrEnvDropdownView<MyEnvViewModel, MyEnv>(
  buildBtn: (context, ctrl, env) => InkWell(
    onTap: () => ctrl.isOpen ? ctrl.close() : ctrl.open(),
    child: Text('$env'),
  ),
);
```

## fr_mvvm_user

Package import:

```dart
import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:fr_mvvm_user/fr_mvvm_user.dart';
```

Core API:

- `UserModel`: base state model with `userId` and optional `token`.
- `IUserViewModel<M extends UserModel>`: base VM contract with `updateUser(M? user)`.
- `FrUserViewModel`: simple concrete VM for `UserModel`.
- `FrUserDropdownView<VM, M>`: selector view with explicit `options`.

Simple user switcher:

```dart
class AppUserViewModel extends FrUserViewModel {
  AppUserViewModel() : super(const UserModel(userId: 'user0'));
}

FrProvider(
  (context) => AppUserViewModel(),
  child: MaterialApp(
    home: Scaffold(
      body: Center(
        child: FrUserDropdownView<AppUserViewModel, UserModel>(
          options: const [
            UserModel(userId: 'user1', token: 'abc'),
            UserModel(userId: 'user2'),
          ],
        ),
      ),
    ),
  ),
);
```

Custom user model:

```dart
class MyUserModel extends UserModel {
  final String name;

  const MyUserModel({super.userId, this.name = '', super.token});

  @override
  String toString() => 'MyUserModel(name: $name; ${super.toString()})';
}

class MyUserViewModel extends IUserViewModel<MyUserModel> {
  @override
  final MyUserModel initValue;

  MyUserViewModel({this.initValue = const MyUserModel(userId: 'user0')});
}

FrUserDropdownView<MyUserViewModel, MyUserModel>(
  options: const [
    MyUserModel(userId: 'user1', name: 'test', token: 'abc'),
    MyUserModel(userId: 'user2'),
  ],
);
```

Do not use `UserModel.init`; the current source exposes `const UserModel({this.userId = '', this.token})`.

## fr_mvvm_locale

Package import:

```dart
import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:fr_mvvm_locale/fr_mvvm_locale.dart';
```

Core API:

- `ILocaleViewModel`: base VM contract for `Locale` state.
- `FrLocaleViewModel`: concrete VM with `initValue`, optional `upstream`, and `all`.
- `FrLocaleSwitchView<VM>`: selector view.
- `LocaleX.rawToString`: formats a `Locale` with `-` or `_`.

Simple locale switcher:

```dart
class AppLocaleViewModel extends FrLocaleViewModel {
  AppLocaleViewModel({
    super.initValue = const Locale('en'),
    super.all = const [Locale('en'), Locale('zh')],
  });
}

FrProvider(
  (context) => AppLocaleViewModel(),
  child: const MaterialApp(
    home: Scaffold(
      body: Center(child: FrLocaleSwitchView<AppLocaleViewModel>()),
    ),
  ),
);
```

Useful VM members:

```dart
final locale = context.read<AppLocaleViewModel>();

locale.updateLocale(const Locale('zh'));
locale.lang; // e.g. "zh"
locale.rawToString(separator: '-'); // e.g. "zh-US" for Locale('zh') in current source
locale.stmLang; // ValueStream<String>, underscore format
locale.stmLocaleBackendFmt; // ValueStream<String>, dash format
locale.fnLang2Locale('zh_CN');
```

`FrLocaleViewModel` can sync from an upstream stream:

```dart
FrLocaleViewModel(
  initValue: const Locale('en'),
  all: const [Locale('en'), Locale('zh')],
  upstream: localeStream,
);
```

## Customizing Packaged Views

All packaged selector views expose similar hooks:

```dart
buildBtn: (context, ctrl, value) => InkWell(
  onTap: () => ctrl.isOpen ? ctrl.close() : ctrl.open(),
  child: Text('$value'),
),
buildAnchorTile: (context, value) => Text('$value'),
```

Use these hooks for local visual customization. In the current source, `buildBtn` receives the current selected value, and `buildAnchorTile` also receives the current selected value rather than the iterated menu item. For multi-section settings pages, keep the page outside the package component and embed only the selector widget.

# fr_mvvm_env install

Use this reference when a task adds `fr_mvvm_env` to a Flutter app or wires
environment state for the first time.

## Package setup

- Add `fr_mvvm_env` to the app package that imports the environment view model
  or selector widget.
- Import `package:fr_mvvm_env/fr_mvvm_env.dart`.
- `fr_mvvm_env` depends on `flowr`, so the app still uses `FrProvider` for
  ownership and subtree access.

## Root wiring

Use `FrEnvViewModel` when a static list is enough, or extend
`IEnvViewModel<M extends EnvModel>` when the app needs extra metadata such as
labels, API hosts, or feature flags.

```dart
import 'package:flutter/material.dart';
import 'package:fr_mvvm_env/fr_mvvm_env.dart';

class AppEnv extends EnvModel {
  const AppEnv({
    required super.env,
    required this.apiBaseUrl,
  });

  final String apiBaseUrl;
}

class AppEnvViewModel extends IEnvViewModel<AppEnv> {
  AppEnvViewModel()
      : super(
          const AppEnv(env: 'dev', apiBaseUrl: 'https://dev.example.com'),
        );

  @override
  List<AppEnv> get all => const [
        AppEnv(env: 'dev', apiBaseUrl: 'https://dev.example.com'),
        AppEnv(env: 'prod', apiBaseUrl: 'https://api.example.com'),
      ];
}

void main() {
  runApp(
    FrProvider(
      (context) => AppEnvViewModel(),
      child: const MaterialApp(home: HomePage()),
    ),
  );
}
```

After the provider is in place, any descendant can read the current env
through `context.read<AppEnvViewModel>().value` or render the selector with
`FrEnvDropdownView<AppEnvViewModel, AppEnv>()`.

## Rules

- Place the provider above every screen or service adapter that needs the env
  state.
- Store public env ids and display metadata in `EnvModel`; keep secrets in a
  secure config source, not in the selector state.
- If changing env should rebuild API clients or repositories, wire that
  explicitly in app code; `fr_mvvm_env` does not hot-swap unrelated singletons
  by itself.

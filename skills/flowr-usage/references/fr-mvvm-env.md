# fr_mvvm_env

Use this reference when a task touches the `fr_mvvm_env` package after the app
has already wired the package. If the task is first-time package setup or root
provider placement, load `references/fr-mvvm-env-install.md` first.

## API

- Import `package:fr_mvvm_env/fr_mvvm_env.dart`.
- `EnvModel` stores an environment id in `env`.
- Extend `IEnvViewModel<M extends EnvModel>` for custom environment state.
- Use `FrEnvViewModel` for the simple built-in implementation.
- Use `FrEnvDropdownView<VM, M>` to render a menu-based selector.

## Pattern

```dart
class AppEnv extends EnvModel {
  const AppEnv({required super.env});
}

class AppEnvViewModel extends IEnvViewModel<AppEnv> {
  AppEnvViewModel()
      : super(const AppEnv(env: 'dev'));

  @override
  List<AppEnv> get all => const [
        AppEnv(env: 'dev'),
        AppEnv(env: 'prod'),
      ];
}
```
After install, render the selector in any descendant widget:

```dart
FrEnvDropdownView<AppEnvViewModel, AppEnv>();
```

## Rules

- `updateEnv(null)` cancels with `skpNull`, so null does not change state.
- Prefer domain-specific `EnvModel` subclasses when the app needs labels,
  endpoints, or feature flags.
- Keep secrets out of `EnvModel`; store only public environment identifiers or
  display metadata.

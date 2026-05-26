# fr_mvvm_locale

Use this reference when a task touches the `fr_mvvm_locale` package.

## API

- Import `package:fr_mvvm_locale/fr_mvvm_locale.dart`.
- Extend `ILocaleViewModel` for custom locale state.
- Use `FrLocaleViewModel` for the simple built-in implementation.
- Use `FrLocaleSwitchView<VM>` to render a menu-based locale selector.
- `LocaleX.rawToString(separator: ..., dftCountry: ...)` formats locales.

## Pattern

```dart
class AppLocaleViewModel extends ILocaleViewModel {
  AppLocaleViewModel() : super(const Locale('en', 'US'));

  @override
  List<Locale> get all => const [
        Locale('en', 'US'),
        Locale('zh', 'CN'),
      ];
}
```

```dart
FrProvider(
  (context) => AppLocaleViewModel(),
  child: FrLocaleSwitchView<AppLocaleViewModel>(),
);
```

## Rules

- `updateLocale(null)` cancels with `skpNull`, so null does not change state.
- `stmLocale` is a normal `Stream<Locale>` and does not replay the current
  locale to new subscribers.
- Use `value` for synchronous locale reads such as `lang` and backend formatting.
- `fnLang2Locale` accepts compact strings such as `zh`, `zh_CN`, and `en_US`.

# fr_mvvm_locale install

Use this reference when a task adds `fr_mvvm_locale` to a Flutter app or wires
global locale state for the first time.

## Package setup

- Add `fr_mvvm_locale` to the app package that imports the locale view model or
  switcher widget.
- Import `package:fr_mvvm_locale/fr_mvvm_locale.dart`.
- The package manages locale state only; the app still owns
  `supportedLocales`, `localizationsDelegates`, and any generated localization
  classes.

## Root wiring

Use `FrLocaleViewModel` for a simple static locale list, or extend
`ILocaleViewModel` when the app needs custom upstream syncing or helpers.

```dart
import 'package:flutter/material.dart';
import 'package:fr_mvvm_locale/fr_mvvm_locale.dart';

class AppLocaleViewModel extends ILocaleViewModel {
  AppLocaleViewModel() : super(const Locale('en', 'US'));

  @override
  List<Locale> get all => const [
        Locale('en', 'US'),
        Locale('zh', 'CN'),
      ];
}

void main() {
  runApp(
    FrProvider(
      (context) => AppLocaleViewModel(),
      child: FrView<AppLocaleViewModel, Locale>(
        builder: (context, snap, _) => MaterialApp(
          locale: snap.data,
          supportedLocales: snap.vm.all.toList(),
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          home: const HomePage(),
        ),
      ),
    ),
  );
}
```

Replace `AppLocalizations.localizationsDelegates` with the project's actual
delegate list. After root wiring, any descendant can render
`FrLocaleSwitchView<AppLocaleViewModel>()`.

## Rules

- Rebuild `MaterialApp` from locale state when the whole app language should
  switch.
- Keep `supportedLocales` aligned with `snap.vm.all`; do not advertise locales
  that the app cannot actually render.
- Scope the provider lower only when locale state is local to a feature instead
  of global app language.

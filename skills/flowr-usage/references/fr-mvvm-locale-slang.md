# fr_mvvm_locale with slang

Use this reference when a Flutter app uses slang for translations while
`fr_mvvm_locale` owns the application locale state. Load
`references/slang-install.md` as well when installing slang for the first time.

## Responsibilities

Keep `fr_mvvm_locale` responsible for:

- holding the current application `Locale`;
- exposing the single application language-switching entry point;
- driving root `MaterialApp` rebuilds from locale state;
- accepting upstream locale state or application-level language preferences.

Keep slang responsible for:

- managing translation resource files;
- generating type-safe translation accessors;
- generating the supported locale list;
- returning current-locale translations through `S.`.

## View model integration

Use `AppLocaleViewModel` as the only locale write entry point. Use
`LocaleSettings` only inside that view model to synchronize slang:

```dart
import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:fr_mvvm_locale/fr_mvvm_locale.dart';

import '../i18n/strings.g.dart';

class AppLocaleViewModel extends ILocaleViewModel {
  AppLocaleViewModel() : super(supported.first) {
    _syncSlang(value);
  }

  static final supported =
      AppLocaleUtils.supportedLocales.toList(growable: false);

  @override
  List<Locale> get all => supported;

  @override
  FutureOr<Locale?> updateLocale(Locale? locale) {
    if (locale == null) return null;

    final resolved = fnLang2Locale(locale.toLanguageTag());
    _syncSlang(resolved);
    return super.updateLocale(resolved);
  }

  void _syncSlang(Locale locale) {
    LocaleSettings.setLocaleRawSync(locale.toLanguageTag());
  }
}
```

Derive the supported locales from `AppLocaleUtils.supportedLocales`. Do not
duplicate a manual list such as `Locale('zh', 'CN')` and
`Locale('en', 'US')` in the view model.

## Root wiring

Keep the root application driven by FlowR locale state:

```dart
FrView<AppLocaleViewModel, Locale>(
  builder: (context, locale, child) => MaterialApp.router(
    locale: locale.data,
    supportedLocales: locale.vm.all,
    localizationsDelegates: GlobalMaterialLocalizations.delegates,
    routerConfig: appRouter,
  ),
)
```

Switch languages through the view model:

```dart
context.read<AppLocaleViewModel>().updateLocale(targetLocale);
```

Do not call slang locale setters from pages or components:

```dart
LocaleSettings.setLocale(...);
LocaleSettings.setLocaleRaw(...);
LocaleSettings.setLocaleRawSync(...);
```

## Translation access

Translate only at the presentation boundary. A ViewModel must expose semantic
state (for example `LoginIdValidationError.required`) and any interpolation
arguments, never a translated `String`, a translation key string, or an `S.`
accessor. The View maps that semantic state to the generated catalog in its
`build` method:

```dart
final validationMessage = switch (model.validationError) {
  LoginIdValidationError.required => context.S.common.loginIdRequired,
  null => null,
};

Text(context.S.common.confirm)
```

This keeps persisted validation state locale-neutral, so an existing error is
rendered again in the selected language after a language change. Do not store
the result of `S.` in a state model.

Wrap the application once with slang's `TranslationProvider`, then use
`context.S` in every widget that must react to a runtime locale change:

```dart
runApp(TranslationProvider(child: AppProviders(child: const Application())));
```

Use the top-level `S` only for non-reactive one-off reads such as tests or
startup configuration. Keep all application locale writes in
`AppLocaleViewModel`.

For backend failures, retain a backend error code and parameters where the API
provides them, then map known codes in the View. Display a backend message
directly only when the API contract guarantees that it is already localized
for the active application locale.

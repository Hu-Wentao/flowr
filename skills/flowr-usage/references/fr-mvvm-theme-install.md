# fr_mvvm_theme install

Use this reference when a task adds `fr_mvvm_theme` to a Flutter app or wires
global `ThemeExtension` injection for the first time.

## Package setup

- Add `fr_mvvm_theme` to the app package that defines theme models or reads
  `context.ofThm<T>()`.
- Import `package:fr_mvvm_theme/fr_mvvm_theme.dart`.
- If app-owned theme models use `@JsonSerializable`, also add direct
  `json_annotation` dependency and `build_runner` plus `json_serializable`
  dev-dependencies in that app package.
- If theme JSON or built-in images live under Flutter assets, declare those
  paths in the app's `flutter.assets`.

## Theme model

Use app-owned `FrPageTheme<T>` types for page-specific fields, and extend
`FrThemeModel` for the app-owned runtime theme model that holds named
page-theme fields and any extra metadata. `FrThemeModel.extensions` are
inferred from `toJson().values.whereType<FrPageTheme>()`, so runtime `toJson()`
must keep page-theme fields as `FrPageTheme` instances rather than nested maps.

```dart
import 'package:flutter/material.dart';
import 'package:fr_mvvm_theme/fr_mvvm_theme.dart';
import 'package:json_annotation/json_annotation.dart';

part 'app_theme.g.dart';

@JsonSerializable(converters: [FrColorCvt()])
class LoginPageTheme extends FrPageTheme<LoginPageTheme> {
  final Color welcomeColor;
  final String logoImg;

  const LoginPageTheme({required this.welcomeColor, required this.logoImg});

  factory LoginPageTheme.fromJson(Map<String, dynamic> json) =>
      _$LoginPageThemeFromJson(json);

  @override
  Map<String, dynamic> toJson() => _$LoginPageThemeToJson(this);
}

@JsonSerializable(createToJson: false)
class AppThemeModel extends FrThemeModel {
  final String source;
  @JsonKey(name: 'login')
  final LoginPageTheme? loginPage;

  AppThemeModel({
    required super.themeId,
    required this.source,
    this.loginPage,
    super.startAt,
    super.endAt,
    super.priority = 0,
  });

  factory AppThemeModel.fromJson(Map<String, dynamic> json) =>
      _$AppThemeModelFromJson(json);

  @override
  Map<String, dynamic> toJson() => {
    'themeId': themeId,
    'source': source,
    'startAt': startAt,
    'endAt': endAt,
    'priority': priority,
    'login': loginPage,
  };

  LoginPageTheme get loginPageTheme =>
      loginPage ??
      (throw StateError('AppThemeModel.loginPage is required.'));
}
```

You can skip `json_serializable` only when the theme model never parses JSON.
If you do, keep the same runtime `toJson()` contract shown above or you will
need to hand-write the `FrPageTheme`-to-`extensions` bridge.

## Theme layering

Treat `ThemeData` and `FrPageTheme` as complementary layers:

- Put shared Material semantics such as `colorScheme`, typography, global
  component styling, and shared layout tokens like spacing, padding, radius, or
  common component sizes in `ThemeData` or an app-owned global `ThemeExtension`.
- Put page-owned fields such as image paths, labels, page-only overrides, or
  page-scoped layout values in `FrPageTheme`.
- In widgets, read both when needed: use `Theme.of(context)` and shared theme
  extensions for global semantic and layout tokens, and `context.ofThm<T>()`
  for page-specific data.

## Root wiring

Use `FrThemeViewModel` when all themes are already in memory. Extend
`IThemeViewModel<M extends FrThemeModel>` when themes are loaded or merged at
runtime before injection into `MaterialApp`.

```dart
final builtInTheme = AppThemeModel(
  themeId: 'built_in',
  source: 'code',
  loginPage: LoginPageTheme(
    welcomeColor: Colors.black87,
    logoImg: 'asset://assets/logo/built_in.png',
  ),
);

void main() {
  runApp(
    FrProvider(
      (context) => FrThemeViewModel(builtInTheme, all: [builtInTheme]),
      child: FrView<FrThemeViewModel<AppThemeModel>, AppThemeModel>(
        builder: (context, snap, _) {
          final pageTheme = snap.data.loginPageTheme;
          return MaterialApp(
            theme: ThemeData(
              useMaterial3: true,
              colorScheme: ColorScheme.fromSeed(
                seedColor: pageTheme.welcomeColor,
              ),
              extensions: snap.data.extensions,
            ),
            home: const HomePage(),
          );
        },
      ),
    ),
  );
}
```

This root injection path is required for `context.ofThm<T>()` and
`Theme.of(context).extension<T>()` to see the active page theme.
The injected `ThemeData` and `FrPageTheme` are meant to be read together, not
to replace each other.

## Rules

- Keep business-specific page fields in the app package; `fr_mvvm_theme`
  provides infrastructure, not app-owned theme schemas.
- Without `ThemeData(extensions: snap.data.extensions)` at the app root, theme
  extensions are not globally injected.
- If an app-owned `FrThemeModel` parses JSON, prefer `json_serializable` with
  `createToJson: false` so generated `fromJson()` and runtime `toJson()` do not
  fight each other.
- Do not duplicate every shared color into `FrPageTheme`. If a value is a
  common Material semantic color, prefer `Theme.of(context).colorScheme`.
- Use `FrThemeViewModel` only for built-in themes that are already available in
  memory.
- Load `references/fr-mvvm-theme.md` for built-in switching and selector usage
  after install.
- Load `references/fr-mvvm-theme-advance.md` only when the task also needs
  downloaded JSON, local files, remote images, or `theme://` field rewriting.

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
`FrThemeModel` only when the app needs extra metadata beyond `themeId`,
`priority`, and `extensions`.

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

class AppThemeModel extends FrThemeModel {
  final String source;

  const AppThemeModel({
    required super.themeId,
    required this.source,
    super.priority,
    super.extensions,
  });
}
```

Skip `json_serializable` if the app only defines built-in themes in Dart and
does not parse theme JSON.

## Theme layering

Treat `ThemeData` and `FrPageTheme` as complementary layers:

- Put shared Material semantics such as `colorScheme`, typography, and global
  component styling in `ThemeData`.
- Put page-owned fields such as image paths, labels, or page-only overrides in
  `FrPageTheme`.
- In widgets, read both when needed: use `Theme.of(context).colorScheme` for
  shared semantic colors and `context.ofThm<T>()` for page-specific data.

## Root wiring

Use `FrThemeViewModel` when all themes are already in memory. Extend
`IThemeViewModel<M extends FrThemeModel>` when themes are loaded or merged at
runtime before injection into `MaterialApp`.

```dart
const builtInTheme = AppThemeModel(
  themeId: 'built_in',
  source: 'code',
  extensions: [
    LoginPageTheme(
      welcomeColor: Colors.black87,
      logoImg: 'asset://assets/logo/built_in.png',
    ),
  ],
);

extension AppThemeModelX on AppThemeModel {
  LoginPageTheme get loginPageTheme =>
      extensions.whereType<LoginPageTheme>().first;
}

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
- Do not duplicate every shared color into `FrPageTheme`. If a value is a
  common Material semantic color, prefer `Theme.of(context).colorScheme`.
- Use `FrThemeViewModel` only for built-in themes that are already available in
  memory.
- Load `references/fr-mvvm-theme.md` for built-in switching and selector usage
  after install.
- Load `references/fr-mvvm-theme-advance.md` only when the task also needs
  downloaded JSON, local files, remote images, or `theme://` field rewriting.

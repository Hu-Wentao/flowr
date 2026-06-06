FlowR-MVVM: Theme

## Features

Share
- `FrThemeFieldScheme` and image provider helpers for `asset://`, `file://`, `http://`, `https://`, and `theme://` values
- `FrPageTheme` for app-defined `ThemeExtension` models
- `FrThemeModel`, `IThemeViewModel`, `FrThemeViewModel`
- `FrThemeSwitchView`
- `FrColorCvt` for JSON color fields

## Usage

See the `/example` folder.

```dart
part 'app_theme.g.dart';

@JsonSerializable(converters: [FrColorCvt()])
class LoginPageTheme extends FrPageTheme<LoginPageTheme> {
  final Color welcomeColor;
  final String logoImg;

  const LoginPageTheme({
    required this.welcomeColor,
    required this.logoImg,
  });

  factory LoginPageTheme.fromJson(Map<String, dynamic> json) =>
      _$LoginPageThemeFromJson(json);

  @override
  Map<String, dynamic> toJson() => _$LoginPageThemeToJson(this);
}

@JsonSerializable()
class AppTheme extends FrThemeModel {
  final LoginPageTheme loginPage;

  AppTheme({
    required super.themeId,
    super.startAt,
    super.endAt,
    super.priority = 0,
    required this.loginPage,
  });

  factory AppTheme.fromJson(Map<String, dynamic> json) =>
      _$AppThemeFromJson(json);

  @override
  Map<String, dynamic> toJson() => _$AppThemeToJson(this);
}

final lightTheme = AppTheme(
  themeId: 'light',
  loginPage: LoginPageTheme(
    welcomeColor: Colors.black87,
    logoImg: 'asset://login/logo.png',
  ),
);
```

Use `ThemeData` for shared Material semantics, shared layout or component-size
tokens, and `FrPageTheme` for page-owned fields or page-scoped layout
overrides:

```dart
final pageTheme = lightTheme.loginPage;

MaterialApp(
  theme: ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(seedColor: pageTheme.welcomeColor),
    extensions: lightTheme.extensions,
  ),
  home: const HomePage(),
);

final colors = Theme.of(context).colorScheme;
final loginPageTheme = context.ofThm<LoginPageTheme>();
```

If your theme model parses JSON, prefer `json_serializable` for both
`fromJson()` and `toJson()`. Keep the default generated behavior so nested
`FrPageTheme` values stay visible to `FrThemeModel.extensions`.

Resolve downloaded theme files before using them:

```dart
final resolved = frThemeProcFieldValues(themeJson, {
  FrThemeFieldScheme.theme: (value) =>
      FrThemeFieldScheme.file.withScheme('/app/theme/${value.$2}'),
});
```

## Additional information

More information, please visit the [flowr](https://pub.dev/packages/flowr) package.

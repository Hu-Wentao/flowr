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
class LoginPageTheme extends FrPageTheme<LoginPageTheme> {
  final String logoImg;

  const LoginPageTheme({required this.logoImg});

  @override
  Map<String, dynamic> toJson() => {'logoImg': logoImg};
}

final lightTheme = FrThemeModel(
  themeId: 'light',
  extensions: const [LoginPageTheme(logoImg: 'asset://login/logo.png')],
);
```

Resolve downloaded theme files before using them:

```dart
final resolved = frThemeProcFieldValues(themeJson, {
  FrThemeFieldScheme.theme: (value) =>
      FrThemeFieldScheme.file.withScheme('/app/theme/${value.$2}'),
});
```

## Additional information

More information, please visit the [flowr](https://pub.dev/packages/flowr) package.

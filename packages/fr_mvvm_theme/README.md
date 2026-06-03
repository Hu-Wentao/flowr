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
  final Color welcomeColor;
  final String logoImg;

  const LoginPageTheme({
    required this.welcomeColor,
    required this.logoImg,
  });

  @override
  Map<String, dynamic> toJson() => {
    'welcomeColor': welcomeColor.toHexString,
    'logoImg': logoImg,
  };
}

final lightTheme = FrThemeModel(
  themeId: 'light',
  extensions: const [
    LoginPageTheme(
      welcomeColor: Colors.black87,
      logoImg: 'asset://login/logo.png',
    ),
  ],
);
```

Use `ThemeData` for shared Material semantics and `FrPageTheme` for page-owned
fields:

```dart
final pageTheme = lightTheme.extensions.whereType<LoginPageTheme>().first;

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

Resolve downloaded theme files before using them:

```dart
final resolved = frThemeProcFieldValues(themeJson, {
  FrThemeFieldScheme.theme: (value) =>
      FrThemeFieldScheme.file.withScheme('/app/theme/${value.$2}'),
});
```

## Additional information

More information, please visit the [flowr](https://pub.dev/packages/flowr) package.

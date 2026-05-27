# fr_mvvm_theme

Use this reference when a task touches the `fr_mvvm_theme` package.

## API

- Import `package:fr_mvvm_theme/fr_mvvm_theme.dart`.
- Use `FrThemeFieldScheme` for theme resource values:
  `asset://`, `file://`, `http://`, `https://`, `theme://`, or scheme-less asset paths.
- Extend `FrPageTheme<T extends ThemeExtension<T>>` for app-specific page theme models.
- Use `FrThemeModel` for a selected theme and its `ThemeExtension` list.
- Extend `IThemeViewModel<M extends FrThemeModel>` for custom theme state.
- Use `FrThemeViewModel` for the simple built-in implementation.
- Use `FrThemeSwitchView<VM, M>` to render a menu-based theme selector.
- Use `FrColorCvt` for JSON color fields and `String.asImageProvider` or
  `String.asImgProvider` for themed image paths.

## Pattern

```dart
class LoginTheme extends FrPageTheme<LoginTheme> {
  final String logoImg;
  final Color welcomeColor;

  const LoginTheme({
    required this.logoImg,
    required this.welcomeColor,
  });

  @override
  Map<String, dynamic> toJson() => {
        'logoImg': logoImg,
        'welcomeColor': welcomeColor.toHexString,
      };
}

final lightTheme = FrThemeModel(
  themeId: 'light',
  extensions: const [
    LoginTheme(
      logoImg: 'asset://login/logo.png',
      welcomeColor: Colors.black87,
    ),
  ],
);

class AppThemeViewModel extends FrThemeViewModel<FrThemeModel> {
  AppThemeViewModel() : super(lightTheme, all: [lightTheme]);
}
```

```dart
FrProvider(
  (context) => AppThemeViewModel(),
  child: FrView<AppThemeViewModel, FrThemeModel>(
    builder: (context, snap, child) => MaterialApp(
      theme: ThemeData(extensions: snap.data.extensions),
      home: const HomePage(),
    ),
  ),
);
```

## Rules

- Keep business-specific page fields in the app package. The shared package
  should provide theme infrastructure, not app-specific `LoginTheme` or
  `HomeTheme` field sets.
- `updateTheme(null)` cancels with `skpNull`, so null does not change state.
- `chooseTheme` prefers an explicit `themeId`; otherwise it chooses the highest
  priority active theme.
- Resolve `theme://` values to `file://` before creating image providers.
- Scheme-less values are treated as Flutter asset paths.
- The compatibility aliases `ThmFieldSch`, `PageExTheme`, `ColorCvt`,
  `parseScheme`, `withSch`, `ofThm`, and `asImgProvider` are intentionally
  available for migration.

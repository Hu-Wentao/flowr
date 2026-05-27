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
- Use `json_serializable` with `@JsonSerializable(converters: [FrColorCvt()])`
  when theme config JSON stores colors as strings.

## Pattern

### App-specific page theme

```dart
@JsonSerializable(converters: [FrColorCvt()])
class LoginTheme extends FrPageTheme<LoginTheme> {
  final String logoImg;
  final Color welcomeColor;

  const LoginTheme({
    required this.logoImg,
    required this.welcomeColor,
  });

  factory LoginTheme.fromJson(Map<String, dynamic> json) =>
      _$LoginThemeFromJson(json);

  @override
  Map<String, dynamic> toJson() => _$LoginThemeToJson(this);
}
```

### Source 1: built-in theme

Use this for themes shipped in the app binary.

```dart
const builtInLoginTheme = LoginTheme(
  logoImg: 'asset://login/logo.png',
  welcomeColor: Colors.black87,
);

const builtInTheme = AppThemeModel(
  themeId: 'built_in',
  source: 'code',
  extensions: const [
    builtInLoginTheme,
  ],
);
```

### Source 2: downloaded or local JSON config

Use this for network-downloaded configs or bundled/local files. In examples,
`assets/theme_config.json` stands in for a downloaded file.

```json
{
  "themeId": "asset_config",
  "source": "downloaded/local theme_config.json",
  "priority": 10,
  "login": {
    "welcomeColor": "#FF00695C",
    "logoImg": "asset://logo/from-theme-config.png"
  }
}
```

```dart
@JsonSerializable(explicitToJson: true)
class ThemeConfig {
  final String themeId;
  final String source;
  final int priority;
  final LoginTheme login;

  const ThemeConfig({
    required this.themeId,
    required this.source,
    required this.priority,
    required this.login,
  });

  factory ThemeConfig.fromJson(Map<String, dynamic> json) =>
      _$ThemeConfigFromJson(json);

  Map<String, dynamic> toJson() => _$ThemeConfigToJson(this);

  AppThemeModel toThemeModel() => AppThemeModel(
        themeId: themeId,
        source: source,
        priority: priority,
        extensions: [login],
      );
}
```

```dart
class AppThemeViewModel extends IThemeViewModel<AppThemeModel> {
  AppThemeViewModel() : super(builtInTheme);

  final List<AppThemeModel> _all = [builtInTheme];

  @override
  Iterable<AppThemeModel> get all => _all;

  Future<void> loadThemeConfig(String rawJson) async {
    final config = ThemeConfig.fromJson(
      jsonDecode(rawJson) as Map<String, dynamic>,
    );
    final theme = config.toThemeModel();
    _all.add(theme);
    await updateTheme(theme);
  }
}
```

```dart
FrProvider(
  (context) => AppThemeViewModel(),
  child: FrView<AppThemeViewModel, AppThemeModel>(
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
- Model both built-in themes and JSON-config themes as the same
  `FrThemeModel` subtype so the UI only consumes one state contract.
- `updateTheme(null)` cancels with `skpNull`, so null does not change state.
- `chooseTheme` prefers an explicit `themeId`; otherwise it chooses the highest
  priority active theme.
- Resolve `theme://` values to `file://` before creating image providers.
- Scheme-less values are treated as Flutter asset paths.
- The compatibility aliases `ThmFieldSch`, `PageExTheme`, `ColorCvt`,
  `parseScheme`, `withSch`, `ofThm`, and `asImgProvider` are intentionally
  available for migration.

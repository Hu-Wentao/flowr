# fr_mvvm_theme advanced

Use this reference only when a task needs more than built-in app-bundled
themes. Start from `references/fr-mvvm-theme.md`, then load this file for local
resource files, downloaded theme JSON, remote image URLs, or custom
`IThemeViewModel` loading.

## API

- Use `FrThemeFieldScheme` for theme resource values:
  `asset://`, `file://`, `http://`, `https://`, `theme://`, or scheme-less
  asset paths.
- Use `FrColorCvt` when theme config JSON stores colors as strings.
- Use `String.asImageProvider` only after the field value is a concrete
  asset/file/http/https URI.
- Extend `IThemeViewModel<M extends FrThemeModel>` when themes are loaded or
  merged at runtime.
- Use `frThemeProcFieldValues(...)` to rewrite resource placeholders such as
  `theme://` before building `ThemeExtension` objects.
- Use `FrPageTheme.injectFieldBaseUri(...)` when a local base path should be
  injected into raw asset fields.

## Pattern

### App-specific page theme model

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

### Runtime theme model

Use a custom `FrThemeModel` subtype only when runtime-loaded themes need extra
metadata such as the source:

```dart
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

### Local or downloaded JSON config

```json
{
  "themeId": "asset_config",
  "source": "downloaded/local theme_config.json",
  "priority": 10,
  "login": {
    "welcomeColor": "#FF00695C",
    "logoImg": "theme://logo/from-theme-config.png"
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

### Resolve resource fields before parsing

Use `theme://` as a placeholder in downloaded configs, then resolve it to a
real base URI before `fromJson(...)`:

```dart
Map<String, dynamic> resolveThemeJson(
  Map<String, dynamic> rawJson, {
  required String themeBaseDir,
}) => frThemeProcFieldValues(rawJson, {
  FrThemeFieldScheme.theme: (value) =>
      FrThemeFieldScheme.file.withScheme('$themeBaseDir/${value.$2}'),
});
```

For local packaged assets, inject an asset base path into theme fields:

```dart
final withAssetBase = FrPageTheme.injectFieldBaseUri(
  const LoginTheme(
    welcomeColor: Colors.black87,
    logoImg: 'logo/built-in.png',
  ),
  scheme: FrThemeFieldScheme.asset,
  baseUri: 'login/',
);
```

### Runtime loading

```dart
class AppThemeViewModel extends IThemeViewModel<AppThemeModel> {
  AppThemeViewModel({required AppThemeModel builtInTheme})
    : _all = [builtInTheme],
      super(builtInTheme);

  final List<AppThemeModel> _all;

  @override
  Iterable<AppThemeModel> get all => _all;

  Future<void> loadThemeConfig(String rawJson, {String? themeBaseDir}) async {
    final decoded = jsonDecode(rawJson) as Map<String, dynamic>;
    final resolved = themeBaseDir == null
        ? decoded
        : resolveThemeJson(decoded, themeBaseDir: themeBaseDir);
    final config = ThemeConfig.fromJson(resolved);
    final theme = config.toThemeModel();
    _all.removeWhere((item) => item.themeId == theme.themeId);
    _all.add(theme);
    await updateTheme(theme);
  }
}
```

```dart
final localJson = await rootBundle.loadString('assets/theme_config.json');
await vm.loadThemeConfig(localJson, themeBaseDir: '/tmp/app_theme');

final remoteJson = await client.readThemeJson();
await vm.loadThemeConfig(remoteJson, themeBaseDir: '/data/theme_cache');
```

## Rules

- Keep built-in-only examples in `references/fr-mvvm-theme.md`. Do not copy
  runtime-loading details back there.
- `String.asImageProvider` supports `asset://`, `file://`, `http://`, and
  `https://`, but not unresolved `theme://`.
- Removed legacy aliases such as `String.asImgProvider` should be treated as
  breaking API changes rather than restored through compatibility shims.
- Resolve `theme://` values to `file://` before creating image providers.
- `frThemeProcFieldValues(...)` throws on `http://` and `https://` by default;
  only disable that when the caller explicitly accepts direct network fields.
- Scheme-less values are treated as Flutter asset paths for compatibility with
  existing app code.

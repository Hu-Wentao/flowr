# fr_mvvm_theme

Use this reference when a task uses `fr_mvvm_theme` for built-in themes that
ship with the app binary.

If the task needs local file assets, downloaded JSON, remote image URLs, or
custom resource resolution, then load
`references/fr-mvvm-theme-advance.md`.

## API

- Import `package:fr_mvvm_theme/fr_mvvm_theme.dart`.
- Extend `FrPageTheme<T extends ThemeExtension<T>>` for app-specific page theme
  models.
- Use `FrThemeModel` for the selected theme and its `ThemeExtension` list.
- Use `FrThemeViewModel<M extends FrThemeModel>` when the app only switches
  between built-in themes.
- Use `FrThemeSwitchView<VM, M>` to render a menu-based theme selector.
- Use `json_serializable` with `@JsonSerializable(converters: [FrColorCvt()])`
  when the page theme follows the package example style.
- Use `String.asImageProvider` or `String.asImgProvider` for built-in asset
  fields that already resolve to a concrete asset URI.
- Read page theme values from `Theme.of(context).extension<T>()` or
  `context.ofThm<T>()`.

## Pattern

### App-specific page theme

```dart
part 'main.g.dart';

@JsonSerializable(converters: [FrColorCvt()])
class LoginTheme extends FrPageTheme<LoginTheme> {
  final Color welcomeColor;
  final String logoImg;

  const LoginTheme({required this.welcomeColor, required this.logoImg});

  factory LoginTheme.fromJson(Map<String, dynamic> json) =>
      _$LoginThemeFromJson(json);

  @override
  Map<String, dynamic> toJson() => _$LoginThemeToJson(this);
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

### Built-in themes

Use this for themes defined in Dart and bundled with the app.

```dart
const builtInLoginTheme = LoginTheme(
  welcomeColor: Colors.black87,
  logoImg: 'asset://logo/built-in.png',
);

const builtInTheme = AppThemeModel(
  themeId: 'built_in',
  source: 'code',
  extensions: [builtInLoginTheme],
);
```

```dart
FrProvider(
  (context) => FrThemeViewModel(builtInTheme, all: [builtInTheme]),
  child: FrView<FrThemeViewModel<AppThemeModel>, AppThemeModel>(
    builder: (context, snap, child) => MaterialApp(
      theme: ThemeData(extensions: snap.data.extensions),
      home: const HomePage(),
    ),
  ),
);
```

```dart
class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final loginTheme = context.ofThm<LoginTheme>();
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.palette, color: loginTheme.welcomeColor, size: 48),
            const SizedBox(height: 12),
            Image(image: loginTheme.logoImg.asImageProvider),
          ],
        ),
      ),
    );
  }
}
```

## Rules

- Keep business-specific page fields in the app package. The shared package
  should provide theme infrastructure, not app-specific `LoginTheme` or
  `HomeTheme` field sets.
- If built-in themes need metadata such as source, tenant, or campaign info,
  model that in an app-owned `FrThemeModel` subtype like `AppThemeModel`.
- Use `FrThemeViewModel` only when all candidate themes are already available in
  memory.
- `updateTheme(null)` cancels with `skpNull`, so null does not change state.
- `chooseTheme` prefers an explicit `themeId`; otherwise it chooses the highest
  priority active theme.
- If the task introduces local or remote theme resources, do not extend this
  file. Move those details to `references/fr-mvvm-theme-advance.md`.

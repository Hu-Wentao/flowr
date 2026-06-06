# fr_mvvm_theme

Use this reference when a task uses `fr_mvvm_theme` for built-in themes that
ship with the app binary after the app has already wired theme injection. If
the task is first-time package setup or root `ThemeData(extensions: ...)`
injection, load `references/fr-mvvm-theme-install.md` first.

If the task needs local file assets, downloaded JSON, remote image URLs, or
custom resource resolution, then load
`references/fr-mvvm-theme-advance.md`.

## API

- Import `package:fr_mvvm_theme/fr_mvvm_theme.dart`.
- Extend `FrPageTheme<T extends ThemeExtension<T>>` for app-specific page theme
  models.
- Use an app-owned `FrThemeModel` subtype for the selected theme, its named
  page-theme fields, and any extra metadata.
- Use `FrThemeViewModel<M extends FrThemeModel>` when the app only switches
  between built-in themes that are already in memory.
- Extend `IThemeViewModel<M extends FrThemeModel>` when the app loads or merges
  themes at runtime before injecting them into `MaterialApp`.
- Use `FrThemeSwitchView<VM, M>` to render a menu-based theme selector.
- `FrThemeModel.extensions` are derived from `toJson().values` entries that are
  still `FrPageTheme` instances.
- Prefer `json_serializable` for page themes and app-owned theme models that
  parse JSON. For `FrThemeModel` subtypes, prefer the default generated
  `toJson()` wrapper like `=> _$AppThemeModelToJson(this)`. With the default
  `explicitToJson: false`, nested `FrPageTheme` values stay as objects, so
  extension inference still works.
- Prefer keeping Dart field names and JSON keys identical. Use
  `@JsonKey(name: ...)` only when an existing external schema forces a rename.
- Use `String.asImageProvider` for built-in asset fields that already resolve
  to a concrete asset URI.
- Use `Theme.of(context).colorScheme` for shared Material semantic colors.
- Read page theme values from `Theme.of(context).extension<T>()` or
  `context.ofThm<T>()`.

## Pattern

### App-specific page theme

```dart
part 'main.g.dart';

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

@JsonSerializable()
class AppThemeModel extends FrThemeModel {
  final String source;
  final LoginPageTheme loginPage;

  AppThemeModel({
    required super.themeId,
    required this.source,
    required this.loginPage,
    super.startAt,
    super.endAt,
    super.priority = 0,
  });

  factory AppThemeModel.fromJson(Map<String, dynamic> json) =>
      _$AppThemeModelFromJson(json);

  @override
  Map<String, dynamic> toJson() => _$AppThemeModelToJson(this);
}
```

### Built-in themes

Use this for themes defined in Dart and bundled with the app.

```dart
const builtInLoginPageTheme = LoginPageTheme(
  welcomeColor: Colors.black87,
  logoImg: 'asset://assets/logo/built_in.png',
);

final builtInTheme = AppThemeModel(
  themeId: 'built_in',
  source: 'code',
  loginPage: builtInLoginPageTheme,
);
```

For built-in-only switching after install, `FrThemeViewModel` is enough:

```dart
final vm = FrThemeViewModel<AppThemeModel>(
  builtInTheme,
  all: [builtInTheme],
);
```

If the app follows the package example and may replace or merge themes at
runtime, keep the same install-time root injection pattern and swap in an
app-specific `IThemeViewModel` implementation:

```dart
class AppThemeViewModel extends IThemeViewModel<AppThemeModel> {
  AppThemeViewModel() : super(builtInTheme);

  @override
  Iterable<AppThemeModel> get all => [builtInTheme];
}
```

After install-time root initialization, any descendant widget can read the
active page theme with `context.ofThm<T>()` or
`Theme.of(context).extension<T>()`.

```dart
class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final pageTheme = context.ofThm<LoginPageTheme>();
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.palette, color: pageTheme.welcomeColor, size: 48),
            const SizedBox(height: 12),
            Image(image: pageTheme.logoImg.asImageProvider),
          ],
        ),
      ),
    );
  }
}
```

### PageTheme with upper `ColorScheme`

When page theme data should participate in the app-level palette, derive the
root `ThemeData.colorScheme` from the active page theme, then read both layers
inside descendant widgets.

```dart
child: FrView<AppThemeViewModel, AppThemeModel>(
  builder: (context, state, _) {
    final pageTheme = state.data.loginPage;
    return MaterialApp(
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: pageTheme.welcomeColor,
        ),
        extensions: state.data.extensions,
      ),
      home: const HomePage(),
    );
  },
),
```

```dart
class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final pageTheme = context.ofThm<LoginPageTheme>();
    final colors = Theme.of(context).colorScheme;
    return Scaffold(
      body: Center(
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: colors.primaryContainer,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: colors.outlineVariant),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Image(image: pageTheme.logoImg.asImageProvider),
                const SizedBox(height: 12),
                Text(
                  'Seed: ${pageTheme.welcomeColor.toHexString}',
                  style: TextStyle(color: colors.primary),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
```

## Rules

- Keep business-specific page fields in the app package. The shared package
  should provide theme infrastructure, not app-specific `LoginPageTheme` or
  `HomeTheme` field sets.
- The app root must own theme state with `FrProvider` and rebuild
  `MaterialApp` from `FrView`; this is the initialization path for global
  theme injection.
- If the task references the package example, follow its bootstrap shape:
  `FrProvider(AppThemeViewModel) -> FrView -> MaterialApp(theme:
  ThemeData(extensions: state.data.extensions))`.
- If built-in themes need metadata such as source, tenant, or campaign info,
  model that in an app-owned `FrThemeModel` subtype like `AppThemeModel`.
- If an app-owned `FrThemeModel` is parsed from JSON, prefer
  `json_serializable` for both `fromJson()` and `toJson()`. If you skip that,
  you must hand-write both JSON parsing and the `FrPageTheme`-to-`extensions`
  bridge.
- Do not add mirror getters like `get loginPageTheme` when the model field is
  already non-null and directly expresses the page theme.
- Use `FrThemeViewModel` only when all candidate themes are already available in
  memory.
- `updateTheme(null)` cancels with `skpNull`, so null does not change state.
- `chooseTheme` prefers an explicit `themeId`; otherwise it chooses the highest
  priority active theme.
- Do not force nested page-theme fields through `.toJson()` inside the runtime
  `FrThemeModel.toJson()`. Keep the default generated behavior so
  `FrPageTheme` instances remain visible for `extensions` inference.
- Prefer `Theme.of(context).colorScheme` for shared semantic colors. Shared
  spacing, padding, radius, and component size tokens may also live in theme
  through `ThemeData` or app-owned global `ThemeExtension`s. Keep
  `FrPageTheme` focused on page-owned fields, palette inputs, and page-scoped
  layout overrides.
- Treat removed legacy aliases such as `String.asImgProvider` as breaking API
  changes. Migrate to the canonical public names, for example
  `String.asImageProvider`.
- If the task introduces local or remote theme resources, do not extend this
  file. Move those details to `references/fr-mvvm-theme-advance.md`.

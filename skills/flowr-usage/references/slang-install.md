# slang install

Use this reference when a Flutter app needs slang translation resources and
type-safe accessors for the first time. This reference installs and configures
slang only; load `references/fr-mvvm-locale-slang.md` as well when
`fr_mvvm_locale` owns the application locale state.

## Package setup

Add slang and Flutter localization support to the app package:

```bash
fvm flutter pub add slang slang_flutter
fvm flutter pub add "flutter_localizations:{sdk: flutter}"
```

Use slang's own generator by default:

```bash
fvm dart run slang
```

Do not add `slang_build_runner` unless the target project explicitly requires
slang generation to join its unified `build_runner` workflow. In that case,
add and run it with:

```bash
fvm flutter pub add --dev slang_build_runner
fvm dart run build_runner build --delete-conflicting-outputs
```

## Minimal scaffold

Create this structure:

```text
lib/i18n/
  zh-CN.i18n.json
  en-US.i18n.json
  strings.g.dart
slang.yaml
```

- Use `zh-CN.i18n.json` as the base locale resource.
- Include `en-US.i18n.json` as the default second locale resource.
- Generate `strings.g.dart`; never edit it by hand.

Use this minimal `slang.yaml`:

```yaml
base_locale: zh-CN
fallback_strategy: base_locale
input_directory: lib/i18n
input_file_pattern: .i18n.json
output_directory: lib/i18n
output_file_name: strings.g.dart
lazy: false
locale_handling: true
flutter_integration: true
translate_var: S
```

## Code generation

Run the generator after adding or changing any `.i18n.json` file:

```bash
fvm dart run slang
```

## Rules

- Keep `translate_var: S`; do not use slang's default `t` accessor.
- Keep `lazy: false` so `fr_mvvm_locale` integration can switch synchronously
  among every generated locale.
- Keep `base_locale` aligned with an existing base translation file.
- Derive supported locales from the generated translation resources. Do not
  maintain a second locale list.
- Read user-visible translations through `S.`, for example
  `Text(S.login.title)`, never `Text(t.login.title)`.
- Follow the target repository's convention for tracking generated files. If
  it already tracks generated files, track `strings.g.dart` too.

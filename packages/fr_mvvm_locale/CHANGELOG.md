## 2.0.2 2026-07-16
* fix: pass the current locale item to custom menu tile builders.
* fix: safely parse language, country, and script locale identifiers.

## 2.0.1 2026-05-27
* docs: expand the pubspec description for pub.dev scoring.
* fix: add an explicit update method return type for lints_core analysis.
* fix: pass the `dftCountry` argument through `rawToString`.

## 2.0.0 2026-05-26
* **Breaking Change**: upgrade `flowr` dependency to `^6.0.0` to align with bloc-native FlowR semantics.
* **Migration**: consuming apps must create a new state instance before `put` or `update` for equal-value re-emission scenarios.

## 1.0.3 2026-03-21
* refactor: upgrade `flowr` to `^4.0.0`

## 1.0.2 2026-03-16
* refactor: upgrade `flowr` to `^3.0.0`

## 1.0.1 2026-03-16
* refactor: upgrade `flowr` to `^2.6.0`, remove `flowr_dart` dependency

## 1.0.0 2025-9-1
* feat
  - LocaleX
  - ILocaleViewModel, FrLocaleViewModel
  - FrLocaleSwitchView
* refactor ::skpNull
  - adapt flowr_dart: ^2.1.1 flowr: ^2.1.1

## 2.0.2 2026-07-16
* fix: pass the current environment item to custom menu tile builders.

## 2.0.1 2026-05-27
* docs: expand the pubspec description for pub.dev scoring.
* fix: add an explicit update method return type for lints_core analysis.

## 2.0.0 2026-05-26
* **Breaking Change**: upgrade `flowr` dependency to `^6.0.0` to align with bloc-native FlowR semantics.
* **Migration**: consuming apps must create a new state instance before `put` or `update` for equal-value re-emission scenarios.

## 1.1.5 2026-03-21
* refactor: upgrade `flowr` to `^4.0.0`

## 1.1.4 2026-03-16
* refactor: upgrade `flowr` to `^3.0.0`

## 1.1.3 2026-03-16
* refactor: upgrade `flowr` to `^2.6.0`, remove `flowr_dart` dependency

## 1.1.2
* feat FrEnvDropdownView add 'Tooltip'

## 1.1.1
* refactor ::skpNull
- adp flowr_dart: ^2.1.1 flowr: ^2.1.1

## 1.1.0 
- feat FrEnvDropdownView; deprecated EnvDropdownView

## 1.0.0 2025-8-18
* rename from `fr_env_mvvm` package
* feat 
  - EnvModel
  - IEnvViewModel, FrEnvViewModel
  - EnvDropdownView
* adapt Flowr 2.0.1

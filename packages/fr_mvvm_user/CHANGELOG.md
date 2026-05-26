## 2.0.0 2026-05-26
* **Breaking Change**: upgrade `flowr` dependency to `^6.0.0` to align with bloc-native FlowR semantics.
* **Migration**: consuming apps can no longer rely on `FrConfig.initialize(emitEqualValues: true)` for equal-value re-emission; create a new state instance before `put` or `update`.

## 1.0.3 2026-03-21
* refactor: upgrade `flowr` to `^4.0.0`

## 1.0.2 2026-03-16
* refactor: upgrade `flowr` to `^3.0.0`

## 1.0.1 2026-03-16
* refactor: upgrade `flowr` to `^2.6.0`, remove `flowr_dart` dependency

## 1.0.0 2025-8-30
* feat 
  - UserModel
  - IUserViewModel, FrUserViewModel
  - FrUserDropdownView
* adapt Flowr 2.0.1

# freezed install

Use this reference when a project needs `@freezed` state/model classes for the
first time, especially before using `fr-mvvm-contract` generated page models.

## Package setup

Add these dependencies to the package that directly owns the generated model
classes:

- runtime: `freezed_annotation`
- dev: `freezed`
- dev: `build_runner`
- dev: `json_serializable` when using `@FrState`, `@FrStateJson`, or any model
  that generates `fromJson`/`toJson`

Flutter package or app:

```bash
fvm flutter pub add freezed_annotation
fvm flutter pub add --dev freezed
fvm flutter pub add --dev build_runner
```

Pure Dart package:

```bash
fvm dart pub add freezed_annotation
fvm dart pub add --dev freezed
fvm dart pub add --dev build_runner
```

For `@FrState`, `@FrStateJson`, or another JSON-generating model, also run the
matching command:

```bash
fvm flutter pub add --dev json_serializable
fvm dart pub add --dev json_serializable # pure Dart package only
```

## Minimal scaffold

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'user_state.freezed.dart';

@freezed
class UserState with _$UserState {
  const UserState._();

  const factory UserState({
    @Default(false) bool loading,
    String? errorText,
  }) = _UserState;
}
```

## Code generation

Run code generation after adding or changing `@freezed` classes:

```bash
fvm dart run build_runner build --delete-conflicting-outputs
```

Use watch mode only when the task needs continuous regeneration:

```bash
fvm dart run build_runner watch --delete-conflicting-outputs
```

## Rules

- Add `part 'xxx.freezed.dart';` in the same source file as the `@freezed`
  class.
- `@FrState` and `@FrStateJson` both enable `toJson`; for either preset, also
  add `part 'xxx.g.dart';` and directly declare `json_serializable` under the
  owning package's `dev_dependencies`.
- Use `@Default(...)` for non-nullable fields with defaults.
- Use nullable field types such as `String?` or `User?` for optional nullable
  values instead of forcing `required`.
- Omit `json_serializable` only for a plain `@freezed` model whose JSON
  generation is disabled. Never handwrite `_$XxxToJson` or `_$XxxFromJson`;
  if either is missing, check the dependency and `.g.dart` part, then rerun
  build_runner.
- Follow the target repository's convention for committing generated
  `*.freezed.dart` files. If the repo already tracks generated files, commit the
  new generated file too.
- After install, return to the calling skill and continue the actual page/model
  work; this reference is only for dependency setup and generator workflow.

# Route Refactor Validation

Use this task when adding, moving, or refactoring typed Pages, `$extra`
payloads, or a group of tightly related Pages.

## Cross-page modules

Group tightly related Pages under one feature directory only when they form a
cohesive flow. Name the module export after its directory:

```text
lib/app/auth/
  auth.dart
  login/login.page.dart
  verify_mobile/verify_mobile.page.dart
  set_password/set_password.page.dart
```

Declare the complete Page inventory and each cross-page transfer on the module
export with this exact documentation shape:

```dart
/// Pages: [LoginPage], [VerifyMobilePage], [SetPasswordPage]
/// Page Data Flow:
/// - [LoginPage] -> [VerifyMobilePage] via [VerifyMobilePageExtra]: loginId, authType, tempAuthId
/// - [VerifyMobilePage] -> [SetPasswordPage] via [SetPasswordPageExtra]: authId
export 'login/login.page.dart' hide $appRoutes;
```

List every typed Page below the module directory, including URL variants that
share one component. Each flow line names its source Page, target Page,
target-owned PageExtra, and the complete transported field list.

## PageExtra ownership

- Treat `XxxPageExtra` as a route transport model, never a domain model or
  ViewModel state.
- Declare `XxxPageExtra` directly in the target `xxx.page.dart`. Do not create
  a separate file for it.
- Declare `$extra` on `XxxPage` with that type.
- Expand every PageExtra field into ordinary named fields when building
  `XxxView`; pass only the fields needed by the ViewModel.
- Keep the target component independent of its sibling Page adapter and its
  own PageExtra.
- Allow a source component to import another target `.page.dart` and construct
  its Page/PageExtra for typed navigation.

## Validation workflow

Resolve this task, run its module validator, then regenerate and verify the
Flutter project:

```bash
uv run python <skill-root>/scripts/resolve.py --task validate_routes
uv run python <skill-root>/scripts/validate_routes.py \
  --module-file lib/app/auth/auth.dart
fvm dart run build_runner build
fvm flutter analyze
fvm flutter test
```

Also run final component contract validation for every changed Page. Treat
generated route casts, preserved public URLs, `$extra` fallback behavior, and
the relevant application flow tests as required completion evidence.

## Raw navigation boundaries

`validate_routes.py` indexes every `@TypedGoRoute<XxxPage>(path: '...')` in
the owning project and scans handwritten component shells plus `.c`, `.v`,
`.vm`, and `.srv` parts. A fixed `context.go`, `context.push`, or
`context.replace` URI that matches an indexed Page is invalid. An
`AppRoutes.xxx` constant resolving to the same URI is invalid as well. Use the
reported `XxxPage(...).go/push/replace(context)` helper instead.

Dynamic expressions, interpolated URIs, BFF-returned paths, external URI
schemes, and fixed paths that do not resolve to a known typed Page remain
allowed. A deliberately retained internal compatibility boundary requires a
non-empty reason on the same or immediately preceding line:

```dart
// fr-route: compatibility-boundary legacy SDK callback contract
context.go('/legacy-callback');
```

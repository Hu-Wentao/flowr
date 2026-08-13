# Flutter Widget Preview Contract

Read this reference before creating a Widget that carries `@FrAcddPage`.

## Generated Annotation

Import `package:flutter/widget_previews.dart` from the component library and
put `@Preview(...)` on the public Widget constructor, not on the Widget class
or its typed `GoRouteData` Page:

```dart
@FrAcddPage(
  mode: FrAcddMode.bff,
  namespace: 'confirm_password',
)
class ConfirmPasswordView extends StatelessWidget {
  @Preview(
    name: 'Registration / Set Login PIN',
    group: 'confirm_password',
    size: Size(360, 780),
    wrapper: confirmPasswordPreviewWrapper,
  )
  const ConfirmPasswordView({super.key});
}
```

Populate the arguments from stable authority:

- Set `name` to the exact `Figma.Frame` title. When no Figma contract exists,
  use the public View class name without inventing product copy.
- Set `group` to the exact `@FrAcddPage.namespace`.
- Set `size` to the `Figma Fidelity.Viewport` or another explicitly approved
  viewport. Never guess a common device size.
- Set `wrapper` to a public top-level function or public static method that
  supplies every runtime dependency needed to render the preview.

Only add `brightness`, `textScaleFactor`, `theme`, or `localizations` when the
contract or project profile provides an authoritative value. All annotation
arguments must be compile-time constants.

## Wrapper And Constructor

Keep the wrapper deterministic and preview-safe. It may provide `MaterialApp`,
`FrProvider`, ViewModel fixtures, Theme, localization, or routing context. Use
local fixtures or fakes; never start real network requests, depend on an active
login, or invoke unsupported native, `dart:io`, or `dart:ffi` APIs.

Pass `--preview-wrapper-import <dart-uri>` to `draft_contract.py` when the
wrapper is declared outside the generated component library. Otherwise declare
the public wrapper in that library.

Flutter accepts constructor previews only for public Widget constructors or
factories with no required arguments. Keep the ordinary constructor eligible
when possible. If the runtime View needs required inputs, add a public named
preview constructor or factory that supplies approved fixture values and move
`@Preview(...)` to that preview entry; never invent business data.

## Compatibility

Widget Preview requires Flutter 3.35 or newer and remains experimental. Apply
this rule to newly generated `@FrAcddPage` Widgets. Do not batch-migrate
existing Widgets unless the user separately authorizes migration and the
target project meets the Flutter version requirement.

Run `fvm flutter --version` in the target project before enabling Preview.
Never infer target compatibility from the skill repository, another checkout,
or the host's default Flutter installation.

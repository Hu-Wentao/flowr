# Typed Routing

Use `go_router_builder` for every new scaffold and for route changes in a
project that has adopted typed routing.

## Dependencies and generation

Keep `go_router` in `dependencies`. Keep `go_router_builder` and
`build_runner` in `dev_dependencies`. Select a builder version compatible with
the project's Dart SDK; do not blindly copy the latest constraint.

Each independent `xxx.page.dart` declares `part 'xxx.page.g.dart';`, annotates
`XxxPage` with `@TypedGoRoute`, and mixes generated `$XxxPage` into
`GoRouteData`. Import page libraries with prefixes in root `app_router.dart`
and spread each generated route list:

```dart
import 'app/orders/orders.page.dart' as orders;
import 'app/login/login.page.dart' as login;

export 'app/orders/orders.page.dart' hide $appRoutes;
export 'app/login/login.page.dart' hide $appRoutes;

final appRouter = GoRouter(
  routes: [...orders.$appRoutes, ...login.$appRoutes],
);
```

Hide `$appRoutes` from barrel exports because every independent Page library
generates that same public symbol. Use import prefixes for aggregation.

Run:

```bash
fvm dart run build_runner build
```

Commit the generated `.g.dart` under the project's existing generated-source
policy. Never hand-edit it.

## Ownership

- `XxxPage` is the route data class and is not a Widget. Its `build` directly
  constructs `XxxView`; do not add `XxxRoute` or `XxxPageArgs` wrappers.
- Keep the component independent of `XxxPage`, `GoRouterState`, and generated
  route mixins.
- Use a constructor field named `$extra` only for non-URL state. It does not
  support reliable deep links or browser back/forward restoration, so prefer
  path/query parameters for durable navigation state.
- Use enums or supported scalar types for URL fields when that preserves the
  public URL. Preserve existing URL paths and query values during migration.
- Use a route-owned `XxxPageExtra` to group several `$extra` values. Declare it
  directly in the target `xxx.page.dart`; do not create a separate model file.
  A PageExtra is route transport, not domain data or ViewModel state. Expand
  its fields into ordinary `XxxView` fields in `XxxPage.build`. Keep
  credentials and verification tokens out of path/query.
- A page file may declare multiple `GoRouteData` Page classes for distinct URL
  variants that build the same primary View, such as `SetPasswordPage` and
  `ResetPasswordPage`. Each variant requires its own annotation and generated
  mixin; the basename-matching Page remains primary.

## Navigation

Instantiate the generated route class and call `.go(context)`,
`.push<T>(context)`, or `.replace(context)` when app code knows the target.
Use its `.location` for redirects and comparisons. Do not introduce new route
name/path constant catalogs or interpolate internal URI strings.

Raw `context.go(uri)` is allowed only when the URI is supplied by an external
or genuinely dynamic boundary, such as a validated BFF response or incoming
deep link. Validate/allowlist that URI before navigation; do not treat it as
compile-time-safe. During migration, compatibility path constants may remain
temporarily for serialized contracts and tests, but new navigation must use
generated helpers.

Reject `context.go('/fixed')`, `context.push('/fixed')`, and
`context.replace('/fixed')` when the path matches a project typed Page. Reject
`context.go(AppRoutes.xxx)` and equivalent push/replace calls for the same
reason; a compatibility path catalog is not typed navigation. Report the
target Page and direct replacement, such as `OrdersPage(...).go(context)`.

Allow dynamic expressions, BFF-returned paths, and external URI literals.
Allow a fixed internal URI only at a deliberately retained compatibility
boundary with an adjacent reason:

```dart
// fr-route: compatibility-boundary legacy SDK callback contract
context.go('/legacy-callback');
```

Do not accept an empty marker. Run `validate_routes` to index every project
typed Page and scan handwritten component navigation.

A component must remain independent of its own sibling Page adapter. It may
import another destination `.page.dart` and construct that target's Page or
PageExtra for typed navigation. For example, `login.dart` may import
`verify_mobile.page.dart`; `verify_mobile.dart` must not import
`verify_mobile.page.dart`.

## Cross-page modules

When Pages form one cohesive flow, group them under a feature module and make
the basename-matching module export document the Page inventory and Page data
flow. Read `validate_routes.md` for the required `Pages:` and
`Page Data Flow:` syntax and run the `validate_routes` task.

## Validation

After route changes, format handwritten Dart, run build_runner, run
`fvm flutter analyze`, and run route/application tests. Cover URL preservation,
query defaults, `$extra` fallback behavior, and browser/deep-link behavior when
Web is targeted.

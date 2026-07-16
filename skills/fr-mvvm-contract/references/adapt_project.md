# Existing Project Adaptation

Adapt an existing Flutter application to this skill's standard ACDD scaffold
without regenerating or overwriting the project.

## Authoritative Baseline

Read `references/acdd_scaffold.md`, then inspect the files under
`assets/acdd_scaffold/`. Those boundaries and templates define the target
structure. Use the templates as responsibility references, not files to copy
blindly over existing implementations.

Never run `scripts/acdd_scaffold.py --apply` in or over an existing project.
It accepts only an empty target and is exclusively for new projects.

## Inventory

Before editing:

1. Read repository instructions and inspect Git status.
2. Read `pubspec.yaml`, current entrypoints, application/root widget, provider
   setup, routing, environment, locale, theme, storage initialization, tests,
   and platform directories.
3. Locate feature pages, reusable feature components, and shared presentation
   components.
4. Record required initialization and behavior that the standard empty
   templates do not contain.
5. Identify missing scaffold dependencies. Add only missing dependencies; do
   not replace compatible project versions merely to match a newly generated
   project.

## Current-To-Target Mapping

Produce a concrete mapping before moving code:

| Target | Responsibility |
| --- | --- |
| `lib/main.dart` | Flutter binding initialization, required process startup, `FrStorage.init()`, and `runApp` |
| `lib/application.dart` | Root `MaterialApp.router`, localization, theme composition, and root router binding |
| `lib/app_router.dart` | Root `GoRouter` configuration and route registration |
| `lib/core/providers.dart` | Root Env, Locale, Theme, and other genuinely application-scoped providers |
| `lib/core/` | Application providers plus environment, locale, and theme models/view models |
| `lib/app/<route-segment>/` | Route feature component contracts and optional page adapters |
| `lib/app/<route-segment>/widgets/` | Plain Widgets reused only inside one route |
| `lib/components/` | Complete components reused by multiple routes, including state-owning feature components |
| `lib/widgets/` | Plain Widgets reused by multiple routes |
| `test/application_test.dart` | Root application/provider smoke coverage adapted to real startup requirements |

For every current file or responsibility, mark it `keep`, `move`, `merge`,
`replace`, or `review`. Include import, route, generated-part, and test updates
required by each move. Stop for approval when repository policy requires it;
an explicit user instruction to implement directly counts as approval of the
workflow, not permission to discard behavior.

## Migration Rules

1. Create missing target directories and files from the mapping.
2. Merge root responsibilities into `main.dart`, `application.dart`,
   `app_router.dart`, and `core/providers.dart`; preserve required startup
   ordering and side effects. Remove an old bootstrap layer only after its
   responsibilities have explicit new owners.
3. Move Env, Locale, and Theme ownership under `core/` and use the FlowR
   MVVM types shown by the standard templates. Preserve project-specific
   values and behavior.
4. Move route features toward `app/<route-segment>/` using this skill's
   source-first component layout. Keep route adapters independent from their
   component libraries.
5. Move components reused by multiple routes to `components/`, including
   state-owning feature components. Keep route-owned components with their
   route.
6. Keep one-off Widgets private in the owning component's `.v.dart`. Move plain
   Widgets reused inside one route to that route's `widgets/`; move them to
   root `widgets/` only when multiple routes reuse them. Do not give plain
   Widgets component contracts, Providers, Events, or ViewModels.
7. Update imports, exports, routes, generated `part` relationships, tests, and
   asset references atomically with each move.
8. Remove superseded files only after searches show no remaining imports,
   route references, reflection/string references, or generated dependencies.

Do not change organization identifiers, bundle/application IDs, signing,
platform targets, native configuration, deep links, route names, persistence
keys, environment values, or public component contracts unless the user
explicitly approves that change.

## Validation

Run the repository's configured commands with `fvm`:

1. Run build generation when moved or changed files affect generated parts.
2. Format changed Dart files.
3. Run focused tests for moved features and root application startup.
4. Run `fvm flutter analyze` and `fvm flutter test`, or stricter repository
   equivalents.
5. Search for stale imports, old entrypoint/bootstrap names, and obsolete file
   paths.
6. Report all breaking changes and compatibility/configuration decisions. If
   none exist, state that explicitly.

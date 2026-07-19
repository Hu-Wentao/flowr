# ACDD Project Scaffold

Use this mode only to create a new native Flutter project. Run the bundled
script for all project creation, dependency installation, template rendering,
formatting, analysis, and tests; do not reproduce those steps manually.

## Inputs

- `name`: Dart lower_snake_case project name.
- `output`: target directory; an omitted interactive value defaults to `name`.
- `org`: lowercase reverse-domain organization such as `com.example`.
- `platforms`: optional comma-separated subset of `android`, `ios`, `macos`,
  `web`, `windows`, and `linux`. Omit it or press Enter to use `android,ios`.
  macOS-specific configuration is applied only when `macos` is selected.
- `description`: optional Flutter project description.

If `name`, `output`, or `org` is missing, ask the user for it or run the script
interactively. In a non-interactive shell, the script rejects missing required
inputs instead of guessing them.

## Workflow

1. Resolve the skill directory that contains this reference.
2. Run a dry-run without writing files:

```bash
uv run python <skill-root>/scripts/acdd_scaffold.py \
  --name example_app \
  --output /absolute/path/example_app \
  --org com.example \
  --dry-run
```

3. Show the resolved path, platforms, dependencies, commands, and output files
   to the user. Stop for approval unless an active goal explicitly continues.
4. Re-run the same command with `--apply` after approval.
5. Report any failed stage and leave partial output in place for inspection.
   Never retry with overwrite or add `--force`.

Running with neither `--dry-run` nor `--apply` is a safe dry-run. Running with
`--apply` creates the selected Flutter platforms, installs `flowr`, `fr_acdd`,
`fr_mvvm_theme`, `fr_mvvm_locale`, `fr_mvvm_env`, `fr_storage`, `go_router`,
Freezed, Retrofit (`dio`, `retrofit`, dev-only `retrofit_generator`, and
`efficient_dio_logger` for Service request/response/error logging), and
the runtime `json_annotation` plus dev-only `json_serializable` code-generation
pair, then verifies the generated project.

## macOS Runtime Configuration

When `macos` is selected, the scaffold also:

- sets both the Xcode project and CocoaPods deployment targets to macOS 11.0
  for ObjectBox;
- adds `path_provider` and opens ObjectBox under the app-specific Application
  Support directory;
- creates a separate unsandboxed `Debug.entitlements` and uses an ad-hoc local
  signing identity, without an Apple Team or personal certificate;
- injects a deterministic development-only 32-byte storage key in Debug so
  startup does not depend on Keychain;
- keeps Profile and Release sandboxed, adds Keychain Sharing, and leaves
  `FrStorage` to create or load its encryption key from macOS Keychain; and
- runs format, analyze, tests, and `fvm flutter build macos --debug` without
  launching a long-lived application process.

The Debug key protects local development data from plaintext storage, but it is
embedded in the application and must never protect real secrets. Before a
Profile or Release build, configure the project's own Apple Team, Bundle ID,
signing certificate, and Keychain capability. Never copy the Debug entitlement
or development key behavior into a distributable build.

Only when the user asks to view the result, launch the generated macOS Debug
application, verify that it reaches the first frame, and capture a screenshot.
Do not make application launch part of the scaffold command.

## Generated Boundaries

- `main.dart` initializes Flutter bindings and `FrStorage`, then calls
  `runApp`; do not add a bootstrap layer.
- `application.dart` owns the root `MaterialApp.router` composition and does
  not declare a `home` widget.
- `app_router.dart` owns the root `GoRouter` and initial placeholder route.
- `core/` owns Env, Locale, Theme, and root providers.
- Empty `app/`, `components/`, and `widgets/` directories are retained with
  `.gitkeep`.
- Generate the first approved route contract under
  `lib/app/<route-segment>/`; do not generate a business page during project
  scaffolding.
- Generate components reused by multiple routes under
  `lib/components/<component-name>/`.
- Put plain Widgets reused by multiple routes under `lib/widgets/`. Put plain
  Widgets reused only inside one route under
  `lib/app/<route-segment>/widgets/` when that route is implemented.

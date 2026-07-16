# ACDD Project Scaffold

Use this mode only to create a new native Flutter project. Run the bundled
script for all project creation, dependency installation, template rendering,
formatting, analysis, and tests; do not reproduce those steps manually.

## Inputs

- `name`: Dart lower_snake_case project name.
- `output`: target directory; an omitted interactive value defaults to `name`.
- `org`: lowercase reverse-domain organization such as `com.example`.
- `platforms`: optional comma-separated list. Omit it or press Enter to use
  `android,ios`. Web and desktop targets are not supported in this mode.
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
`--apply` creates only Android/iOS projects, installs `flowr`, `fr_acdd`,
`fr_mvvm_theme`, `fr_mvvm_locale`, `fr_mvvm_env`, `fr_storage`, `go_router`,
and Freezed, then verifies the generated project.

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

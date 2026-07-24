# Extract Shared UI Workflow

`extract_shared_ui` promotes an existing UI entry only after its reuse scope
and state ownership have been audited. It is a migration workflow: retain
business behavior and route ownership while moving the reusable boundary.

## 1. Discover and classify

Run `discover_ui_reuse.py` first, then generate a no-write manifest:

```bash
uv run --script <skill-root>/scripts/extract_shared_ui.py \
  --project-root . \
  --source lib/app/auth/login/login.v.dart \
  --consumer lib/app/auth/verify_mobile/verify_mobile.v.dart \
  --symbol OnboardingLanguageToggle \
  --name language_toggle \
  --capability "语言切换"
```

The manifest records the source, consumers, target, existing capability
matches, detected ownership signals, and required manual work. It makes no
file changes unless `--apply` is supplied.

Classify an entry as a shared Widget only when it has no independent Provider,
ViewModel, Bloc/Event, API Service, or component state. Keep selected values
and callbacks owned by the consuming Page or component. A language selector,
for example, receives `value` and `onChanged`; the consuming ViewModel remains
responsible for locale persistence and dispatching its language-change Event.

When an entry owns any of those responsibilities, use the manifest as the
approved migration map, then create a component with `gen_component`. Define
the new component contract and migrate consumers only after its contract gate;
the extractor deliberately refuses `--apply` for this classification.

## 2. Review before apply

Confirm all of the following:

- no existing public component or Widget already owns the capability;
- visual and interaction contracts are genuinely compatible across consumers;
- the target public name, inputs, callback semantics, and theme ownership are
  stable;
- every affected consumer is listed explicitly; and
- state/API/Event ownership will remain with the source owner or move through
  an approved component contract.

For a private source class, give `--public-name`. The Widget extractor updates
the listed source and consumers to that public name. It refuses nested private
helper classes because those require an explicit design decision rather than a
lossy mechanical move.

## 3. Apply and verify

For an approved pure Widget migration, run the same command with `--apply`.
It creates `lib/widgets/<name>.dart`, inserts provider catalog metadata,
moves the selected class, and imports the public module in the explicitly
listed consumers. Then update the consuming Page contracts' `Widget Tree:`
and run:

```bash
uv run --script <skill-root>/scripts/discover_ui_reuse.py \
  --project-root . --capability "语言切换" --strict
fvm dart format <changed-dart-files>
fvm flutter analyze
```

The workflow does not deduplicate different designs automatically, generate a
ViewModel for a presentation Widget, or alter locale/business behavior.

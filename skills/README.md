# FlowR Skills

This directory contains local agent skills for FlowR development. Each skill
has a `SKILL.md` entry file with trigger metadata, workflow notes, examples,
and links to focused references.

## Available Skills

| Skill | Use When |
| --- | --- |
| [`flowr-dart-usage`](flowr-dart-usage/SKILL.md) | Working with pure Dart `flowr_dart` APIs such as `FlowR`, `FlowB`, `update`, logging, skip handling, scheduling, stream helpers, and disposal. |
| [`flowr-usage`](flowr-usage/SKILL.md) | Working with Flutter `flowr` APIs such as `FrViewModel`, `FrBlocViewModel`, `FrProvider`, `FrView`, `FrListener`, `FrConsumer`, `FrUnion`, and the MVVM extension packages. |
| [`fr-mvvm-contract`](fr-mvvm-contract/SKILL.md) | Creating or migrating Flutter pages to the contract-first MVVM layout with `xxx_page.dart` or `xxx_view.dart` plus their `.v.dart` / `.vm.dart` parts. |

## How To Use

Use these skills in a Codex-compatible agent environment by exposing the
directories under `skills/` as available skills, or by asking the agent to load
the specific `SKILL.md` file before making related changes.

Examples:

```text
Use skills/flowr-dart-usage/SKILL.md to review this FlowR core change.
Use skills/flowr-usage/SKILL.md when updating this Flutter MVVM page.
Use skills/fr-mvvm-contract/SKILL.md to scaffold a new contract-first page.
```

For `fr-mvvm-contract`, the helper scripts can be run from the repository root:

```bash
uv run python skills/fr-mvvm-contract/scripts/page_context.py --target lib/page/foo_page
uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/foo_page.json
uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/foo_page.json --page-root lib/src/page
uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/foo_page.json --parent account
uv run python skills/fr-mvvm-contract/scripts/new_page.py --spec-file /tmp/foo_page.json --dir /tmp/foo_page --force
```

`fr-mvvm-contract` is now bloc-only. The generator consumes a structured JSON
page spec and produces `FrBlocViewModel`, generated event/model classes, and
the contract/view/view-model file split. Set `page.kind` to `view` or use a
`*_view` page name when you need `xxx_view.dart`; the default remains
`*_page.dart`. The contract dart file is the only long-lived source of truth;
any temporary JSON spec is just generator input and should not be committed as
a parallel design artifact. Temporary page specs now require `page.figmaUrl`
and `page.api`, with optional `page.apiContract` when `page.api` is
`BFF`. Non-DTO page-local models now default to the generated `@FrState`
Freezed preset exported by `flowr` so `toJson()` is available during
debugging; use `models[].preset = "state_json"` only when a model must be
restored from JSON, or `models[].preset = "plain"` when it contains
runtime-only or non-JSON-serializable fields. Generated pages now require
`freezed_annotation`, `freezed`, `build_runner`, and a `flowr` version that
exports `FrState` / `FrStateJson` in the target project. If the target
project has not installed those yet, use
`skills/flowr-dart-usage/references/freezed-install.md` first. See
`skills/fr-mvvm-contract/SKILL.md` for the required spec shape. When a
contract page uses `bff` mode, the target project also needs `fr_acdd`; use
`skills/fr-mvvm-contract/references/fr-acdd-install.md` first if it is
missing.

When applying these skills in this repository, follow `AGENTS.md`: use `fvm`
for Flutter/Dart commands and `uv` for Python commands.

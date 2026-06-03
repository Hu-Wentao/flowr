# FlowR Skills

This directory contains local agent skills for FlowR development. Each skill
has a `SKILL.md` entry file with trigger metadata, workflow notes, examples,
and links to focused references.

## Available Skills

| Skill | Use When |
| --- | --- |
| [`flowr-dart-usage`](flowr-dart-usage/SKILL.md) | Working with pure Dart `flowr_dart` APIs such as `FlowR`, `FlowB`, `update`, logging, skip handling, scheduling, stream helpers, and disposal. |
| [`flowr-usage`](flowr-usage/SKILL.md) | Working with Flutter `flowr` APIs such as `FrViewModel`, `FrBlocViewModel`, `FrProvider`, `FrView`, `FrListener`, `FrConsumer`, `FrUnion`, and the MVVM extension packages. |
| [`fr-mvvm-contract`](fr-mvvm-contract/SKILL.md) | Creating or migrating Flutter pages to the contract-first MVVM layout with `xxx_page.dart`, `xxx_page.v.dart`, and `xxx_page.vm.dart`. |

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
page spec and produces `FrBlocViewModel`, `XxxPageEvent`, and the
contract/view/view-model file split. See
`skills/fr-mvvm-contract/SKILL.md` for the required spec shape.

When applying these skills in this repository, follow `AGENTS.md`: use `fvm`
for Flutter/Dart commands and `uv` for Python commands.

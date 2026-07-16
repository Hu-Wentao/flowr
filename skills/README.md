# FlowR Skills

This directory contains local agent skills for FlowR development. Each skill
has a `SKILL.md` entry file with trigger metadata, workflow notes, examples,
and links to focused references.

## Available Skills

| Skill | Use When |
| --- | --- |
| [`flowr-usage`](flowr-usage/SKILL.md) | Using `flowr_dart`, Flutter FlowR MVVM APIs, and optional FlowR extension packages. |
| [`fr-mvvm-contract`](fr-mvvm-contract/SKILL.md) | Creating an ACDD Flutter project or creating, validating, and evolving contract-first FlowR components and route adapters. |

## How To Use

Use these skills in a Codex-compatible agent environment by exposing the
directories under `skills/` as available skills, or by asking the agent to load
the specific `SKILL.md` file before making related changes.

Examples:

```text
Use skills/flowr-usage/SKILL.md when updating this Flutter MVVM page.
Use skills/fr-mvvm-contract/SKILL.md to create an ACDD Flutter project.
Use skills/fr-mvvm-contract/SKILL.md to draft a contract-first page.
```

`acdd_scaffold` is script-driven. Preview and apply a new Android/iOS project
with:

```bash
uv run python skills/fr-mvvm-contract/scripts/acdd_scaffold.py \
  --name example_app --output /tmp/example_app --org com.example --dry-run
uv run python skills/fr-mvvm-contract/scripts/acdd_scaffold.py \
  --name example_app --output /tmp/example_app --org com.example --apply
```

The script prompts for omitted required inputs in an interactive terminal.
Platforms default to `android,ios`. It installs FlowR, `fr_acdd`, Env, Locale,
Theme, Storage, and Freezed, renders the application root, and runs formatting,
analysis, and tests.

For contract work, resolve the project profile before drafting or validating:

```bash
uv run python skills/fr-mvvm-contract/scripts/resolve.py --task gen_page
uv run python skills/fr-mvvm-contract/scripts/draft_contract.py \
  --name order_content --dir lib/app/order_content \
  --figma-url <url> --api BFF-JSON --route <route>
```

The Dart contract remains the long-lived source of truth. No persistent JSON
spec or compatibility generator is part of the current workflow.

When applying these skills in this repository, follow `AGENTS.md`: use `fvm`
for Flutter/Dart commands and `uv` for Python commands.

---
name: flowr-usage
description: Use FlowR correctly in pure Dart or Flutter projects. Resolve the target package first, then use FlowR/FlowB core APIs or Flutter FrViewModel, FrProvider, and FrView APIs without loading Flutter rules for flowr_dart-only packages.
---

# FlowR Usage

Before FlowR work, resolve the target package:

```bash
uv run python .agents/skills/flowr-usage/scripts/resolve.py --task auto
```

Read the resolved instructions once per `instructions_id`.

## Route Selection

- `auto` is the normal entry. It reads the nearest `pubspec.yaml`.
- A package that directly depends only on `flowr_dart` and has no Flutter SDK
  dependency resolves to `core`. It loads no Flutter or `flowr` material.
- A package that directly depends on `flowr` and declares a Flutter SDK
  dependency resolves to `flutter`. It loads core rules first, then Flutter
  rules and the optional project profile.
- `flowr` without a Flutter SDK dependency is invalid. Fix the target package;
  do not silently downgrade it to the core route.
- `--task core` and `--task flutter` are explicit routes. The resolver rejects
  `flutter` for a Dart-only package.

## Common Rules

- Follow the repository `AGENTS.md` and preserve its existing architecture.
- Read core instructions for every resolved route. Flutter instructions extend
  rather than replace the core rules.
- Import only public package entry points. Do not import `flowr/src/...` or
  `flowr_dart/src/...` from application code.
- Keep package API usage here. File layout, component ownership, and contract
  decisions remain the responsibility of the calling architecture skill.

## References

Load only the reference relevant to the task:

- `references/core.md`: FlowR/FlowB, logging, state, streams, scheduling, and
  disposal rules.
- `references/flutter.md`: `FrViewModel`, `FrBlocViewModel`, `FrProvider`,
  `FrView`, listeners, and Flutter ownership rules.
- `references/flowr-dart-install.md`: add `flowr_dart` to a pure Dart package.
- `references/flowr-install.md`: add `flowr` and first Flutter provider/view.
- `references/flowr-logging.md`, `flowr-run-catching.md`, `flowr-slowly.md`,
  `flowr-disposal.md`, `flowr-update.md`: the named core concern.
- `references/freezed-install.md`: add immutable Freezed state generation.
- `references/fr-provider-di.md`, `fr-vm-communication.md`, `fr-union.md`:
  Flutter advanced provider, VM coordination, and `FrUnion` use.
- `references/fr-mvvm-*.md`: the corresponding optional Flutter extension.

## Validation

- Format changed Dart files with the package's configured Dart/Flutter tool.
- Run focused tests for the target package.
- Run the repository analyzer command when shared APIs or package surfaces
  change.

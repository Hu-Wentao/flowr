# fr_acdd install

Use this reference when a contract-first page will use `bff` mode and the
target project does not already have `fr_acdd`.

For the annotation and extraction rules after install, continue with
`skills/fr-mvvm-contract/references/fr-acdd.md`.

## Package setup

Add `fr_acdd` to the package or app that directly owns the generated contract
page files.

Published package or repo-managed dependency:

```bash
fvm flutter pub add fr_acdd
```

Pure Dart package:

```bash
fvm dart pub add fr_acdd
```

If `fr_acdd` is developed in the same repository and is not consumed from a
registry, add it as a path dependency instead of inventing a package source:

```yaml
dependencies:
  fr_acdd:
    path: ../packages/fr_acdd
```

Adjust the relative path to match the target package location.

If the target project uses `@FrState`, `@FrStateJson`, or a JSON DTO, install
`json_annotation` as a direct runtime dependency and `json_serializable` as a
direct dev dependency in the package that directly owns those models:

```bash
fvm flutter pub add json_annotation
fvm flutter pub add --dev json_serializable
```

For a pure Dart package, use `fvm dart pub add json_annotation` followed by
`fvm dart pub add --dev json_serializable`. Never install `json_annotation`
with `--dev`. Both FlowR state presets enable `toJson`, so `@FrState` needs
this generator setup even when it does not enable `fromJson`. Only a plain
`@freezed` model with JSON generation explicitly absent can omit both JSON
packages and its `.g.dart` part.

If the target project still lacks `freezed_annotation`, `freezed`,
`build_runner`, or the conditionally required JSON packages, load
`skills/flowr-usage/references/freezed-install.md` too.

## Rules

- This reference only covers dependency setup and install-time prerequisites.
- After install, return to the calling skill and continue with
  `skills/fr-mvvm-contract/references/fr-acdd.md` for DTO annotation and
  extraction rules.

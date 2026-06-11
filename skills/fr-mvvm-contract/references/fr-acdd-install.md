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

If the target project still lacks `freezed_annotation`, `freezed`, or
`build_runner`, load
`skills/flowr-dart-usage/references/freezed-install.md` too.

## Rules

- This reference only covers dependency setup and install-time prerequisites.
- After install, return to the calling skill and continue with
  `skills/fr-mvvm-contract/references/fr-acdd.md` for DTO annotation and
  extraction rules.

# Figma Release Management

Use project-wide release metadata to detect when a touched `.c.dart` contract
still points to an older Figma snapshot. Keep the concrete primary URL and
compact state node IDs in the contract; do not duplicate per-page node mappings
in project config.

## Project configuration

Configure immutable release identities in
`.agents/skills-config/fr-mvvm-contract/config.yaml`:

```yaml
figma:
  active_release: v2
  enforcement: gradual
  releases:
    v1:
      file_key: OLD_FILE_KEY
      status: archived
    v2:
      file_key: CURRENT_FILE_KEY
      status: active
    v3:
      file_key: UNAPPROVED_FILE_KEY
      status: candidate
```

`active_release` is explicit. Never infer it by sorting release names. Require
exactly that release to have `status: active`; other releases use `candidate`
or `archived`. File keys must be unique.

Use `gradual` while pages migrate when touched. Use `strict` only after every
unexcepted contract has moved to the active release.

## Resolve before touching a Figma-bound page

Run:

```bash
uv run --script <skill-root>/scripts/resolve_figma_release.py \
  --project-root . \
  --contract-file lib/app/example/example.c.dart
```

Interpret the stable statuses as follows:

- `current`: use the contract binding.
- `stale`: inspect the active release and migrate only the touched contract.
- `pinned`: retain the explicit old-release exception and report it.
- `candidate`: block; an unapproved release cannot be implementation authority.
- `unknown`: block and register the file key before reading it as authority.
- `unconfigured`: preserve the legacy contract-only behavior.

For `stale`, inspect lightweight structure in the active Figma file before
requesting design context. Search visible page-title text first and resolve
matching text nodes to their owning Frames. Match route identity, business
responsibility, navigation context, primary state, and declared state variants.
Use Frame names only as supporting evidence; never switch by Frame name alone.
Update the primary node URL, current Frame name, visible Page Title, and every
owned `Figma States` node ID only when one logical match is unambiguous. If the
page is absent, split, merged, or has several candidates, stop and request a
design decision.

After an unambiguous migration, update the touched `.c.dart`, regenerate its
derived BFF artifact, and revalidate assets, fidelity state, navigation shell,
and focused tests. Do not migrate unrelated contracts merely because they are
stale.

## Intentional old-release exception

Use an exception only when product or design has explicitly approved keeping
one page on an archived release:

```dart
/// Figma Release Override:
/// - Release: v1
/// - Reason: V2 has no approved password-error state
/// - Review After: 2026-08-15
```

`Release` must match the concrete contract URL's configured release. `Reason`
is required; `Review After` is optional and uses `YYYY-MM-DD`. Never add an
override automatically to silence stale detection. Overrides are invalid for
the active, candidate, or unknown release.

## Aggregate enforcement

The aggregate Figma audit reports release alignment separately from visual
fidelity:

- `gradual`: stale contracts pass with migration warnings; unknown, candidate,
  malformed override, and mixed-file contracts fail.
- `strict`: unexcepted stale contracts also fail.
- `pinned`: passes with its reason visible in the audit result.

This structural release result does not prove visual equivalence between
snapshots.

# Figma Fidelity Audit

Use this task when a Flutter Page or component must preserve an approved Figma
screen, its state variants, exported assets, shell ownership, routes, and
regression coverage.

## Resolve Project Authority

1. Read the resolved project profile before scanning or repairing code.
2. Discover every primary Figma contract from project `*.c.dart` files. Require
   exactly one `Figma Fidelity:` disposition. An approved contract declares
   `Viewport`, `Asset Lock`, and `Regression Test`; an unapproved contract uses
   `excluded | <reason>`. Missing dispositions fail coverage. Exclusion means
   the current implementation is not approved as Figma-faithful; never infer
   approval from it.
3. Treat `.c.dart` as the only semantic authority for the Frame, node,
   viewport, asset-lock path, and regression-test ownership. Treat the asset
   lock as derived machine state containing only export identity, repository
   path, and SHA-256. Never duplicate page ids, nodes, viewport, routes,
   visible copy, or executable source rules in that lock or another page list.
4. Run the resolved `audit` command before changes and again after repair.
5. Never weaken or remove a failing check to make the audit pass. Update a
   project check only when the authoritative Figma binding or owned invariant
   has intentionally changed.

## Repair Workflow

1. Inspect the primary Frame and all declared state Frames. Distinguish
   component instances from their source components and assign every node to
   exactly one contract owner.
2. Classify persistent navigation ownership before treating the Frame as a
   complete screen. When it is a declared shell destination, resolve and run
   `validate_navigation_shell`; reuse the one established shell and keep the
   branch View content-only. Preserve public route locations and Page adapters
   unless an approved contract change says otherwise.
3. Use exact exported assets when the asset lock records hashes. Do not
   substitute Material glyphs or redraw an export in code.
4. Implement the primary state, empty/error/filter/detail states, sheets and
   dialogs declared by the contract. Keep state and Events with the owning
   component rather than duplicating a second visual owner.
5. Add focused tests for the real navigation entry, owned states, overlays, and
   configured viewport. Use screenshots or device rendering to check spacing,
   clipping, typography, and shell continuity.

## Validation

Use `audit_figma_fidelity.py --discover` for the aggregate gate. It scans
`lib/**/*.c.dart` by default, validates every disposition and asset lock,
rejects missing/reused locks and duplicate audited bindings, verifies locked
assets are rendered by Flutter asset widgets, and requires the declared test
and viewport. Use `--asset-lock` for a focused hash-only lock check.

The lock schema is `fr-mvvm-contract.figma-assets-lock.v1`. It accepts only
`schema` and `assets`; every asset contains `name`, `path`, `source_export`,
and `sha256`. The audit is a deterministic structural gate; it complements,
but does not replace, contract validation, analyzer checks, focused Flutter
tests, and visual comparison against Figma.

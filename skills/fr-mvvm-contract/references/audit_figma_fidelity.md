# Figma Fidelity Audit

Use this task when a Flutter Page or component must preserve an approved Figma
screen, its state variants, exported assets, shell ownership, routes, and
regression coverage.

## Resolve Project Authority

1. Read the resolved project profile before scanning or repairing code.
2. Discover every primary Figma contract from project `*.c.dart` files. Require
   exactly one `Figma Fidelity:` disposition:
   `profile | <repository-relative-json>` or `excluded | <reason>`.
   Missing dispositions fail coverage. Exclusion means the current
   implementation is not approved as Figma-faithful; never infer approval from
   it.
3. Treat `.c.dart` as the authority for the Frame and profile path. Treat the
   referenced profile's viewport, project paths, source tokens, asset hashes,
   and executable checks as project facts. Do not maintain a second page list.
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
3. Use exact exported assets when the profile records hashes. Do not substitute
   Material glyphs or redraw an export in code.
4. Implement the primary state, empty/error/filter/detail states, sheets and
   dialogs declared by the profile. Keep state and Events with the owning
   component rather than duplicating a second visual owner.
5. Add focused tests for the real navigation entry, owned states, overlays, and
   configured viewport. Use screenshots or device rendering to check spacing,
   clipping, typography, and shell continuity.

## Validation

Use `audit_figma_fidelity.py --discover` for the aggregate gate. It scans
`lib/**/*.c.dart` by default, validates every disposition, cross-checks each
profile's Figma file/node against its owning contract, rejects missing or
reused profiles, and runs every discovered profile. `--profile` remains
available for a focused or legacy single-profile audit.

The profile schema remains `fr-mvvm-contract.figma-fidelity.v1`. It supports
exact asset hashes, source-token rules, unique text ownership, and paths that
must remain absent. The audit is a deterministic structural gate; it
complements, but does not replace, contract validation, analyzer checks,
focused Flutter tests, and visual comparison against Figma.

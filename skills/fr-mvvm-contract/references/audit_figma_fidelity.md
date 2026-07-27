# Figma Fidelity Audit

Use this task when a Flutter Page or component must preserve an approved Figma
screen, its state variants, exported assets, shell ownership, routes, and
regression coverage.

## Resolve Project Authority

1. Read the resolved project profile before scanning or repairing code.
2. Treat the profile's Figma file key, node ids, viewport, paths, source tokens,
   and asset hashes as project facts. They do not belong in the reusable skill.
3. Run the resolved `audit` command before changes and again after repair.
4. Never weaken or remove a failing check to make the audit pass. Update a
   project check only when the authoritative Figma binding or owned invariant
   has intentionally changed.

## Repair Workflow

1. Inspect the primary Frame and all declared state Frames. Distinguish
   component instances from their source components and assign every node to
   exactly one contract owner.
2. Reuse the established route shell and shared Widgets when their capabilities
   match. Preserve public route locations and Page adapters unless an approved
   contract change says otherwise.
3. Use exact exported assets when the profile records hashes. Do not substitute
   Material glyphs or redraw an export in code.
4. Implement the primary state, empty/error/filter/detail states, sheets and
   dialogs declared by the profile. Keep state and Events with the owning
   component rather than duplicating a second visual owner.
5. Add focused tests for the real navigation entry, owned states, overlays, and
   configured viewport. Use screenshots or device rendering to check spacing,
   clipping, typography, and shell continuity.

## Validation

The generic audit profile schema is
`fr-mvvm-contract.figma-fidelity.v1`. It supports exact asset hashes,
source-token rules, unique text ownership, and paths that must remain absent.
The audit is a deterministic structural gate; it complements, but does not
replace, contract validation, analyzer checks, focused Flutter tests, and
visual comparison against Figma.

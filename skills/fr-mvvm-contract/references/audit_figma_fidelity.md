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
   substitute Material glyphs or redraw an export in code. For every icon,
   inspect both the outer placement or hit-area box and the inner visual glyph.
   Preserve both dimensions independently in Flutter. When Figma shows a
   `20x20` or `24x24` slot containing a smaller glyph, build the slot with
   `SizedBox` or `Container`, center the exported leaf asset inside it at the
   glyph's inspected width and height, and do not stretch the leaf SVG to fill
   the slot. Never normalize unrelated glyphs to one shared visual size.
4. Implement the primary state, empty/error/filter/detail states, sheets and
   dialogs declared by the contract. Keep state and Events with the owning
   component rather than duplicating a second visual owner.
5. Reproduce typography from the inspected text nodes, including font family,
   style, weight, size, line height, letter spacing, and any text-trim behavior
   that materially changes bounds. Confirm that every required font is
   available to Flutter before treating the implementation as approved. A
   system-font fallback is a known visual deviation: obtain explicit design
   approval and declare the contract excluded until that exception becomes an
   authoritative compatibility decision.
6. Add focused tests for the real navigation entry, owned states, overlays, and
   configured viewport. Capture the implemented screen at that viewport and
   compare it with the authoritative Figma screenshot. Check spacing,
   clipping, typography, shell continuity, and each icon's placement box and
   visual glyph bounds. Widget-existence, route, asset-hash, and container-size
   assertions alone are not visual-fidelity evidence.

## Visual Approval Gate

Before replacing `Figma Fidelity: excluded | <reason>` with the approved
three-line disposition:

1. Record the authoritative Figma screenshot and the implementation screenshot
   used for comparison.
2. Inspect icon instances at the leaf asset node, not only their component
   wrappers. Verify the exported SVG's intrinsic bounds against the Figma leaf
   bounds and the Flutter leaf widget dimensions.
3. Verify typography with the actual runtime font. Matching numeric
   `fontSize`, `height`, and `fontWeight` values while rendering a different
   family does not satisfy the gate.
4. Reject approval when a small chevron, arrow, menu glyph, or other leaf asset
   is stretched to its outer slot, even if the slot itself has the correct
   size.
5. Keep the contract excluded when visual comparison is unavailable or a known
   font/asset deviation remains unapproved.

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
tests, and visual comparison against Figma. Report the structural result and
visual-approval result separately; never describe a passing structural audit
as proof that icon geometry or typography matches.

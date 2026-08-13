# Figma Fidelity Audit

Use this task when a Flutter Page or component must preserve an approved Figma
screen, its state variants, exported assets, shell ownership, routes, and
regression coverage.

Before translating Figma MCP output into Flutter, read
`figma_flutter_design_to_code.md`. The MCP's generic design-to-code skill
remains responsible for context acquisition; the adapter defines how its
Web-oriented reference output is interpreted for Flutter.

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
   that materially changes bounds. Flutter has no `text-box-trim` equivalent:
   never shrink a `Text` parent to the observed trimmed glyph height. Preserve
   at least the declared line-box height, then adjust the remaining gap or
   position so the next opaque sibling stays at the Figma-derived offset; this
   prevents it from concealing descenders such as `g`, `j`, `p`, `q`, and `y`.
   Add a focused assertion for both the full line box and that sibling offset.
   Confirm that every required font is available to Flutter before treating the
   implementation as approved. A system-font fallback is a known visual
   deviation: obtain explicit design approval and declare the contract excluded
   until that exception becomes an authoritative compatibility decision.
6. For runtime or formatted text, distinguish the observed Figma sample bounds
   from the layout behavior required by real values. Inspect resizing and
   anchors, available space, siblings, the realistic value domain,
   localization, and text scaling. Decide from that evidence whether Flutter
   should constrain width, grow within safe bounds, wrap or reflow, or use
   clipping or ellipsis; no strategy is the universal default. Add a focused
   test with representative and boundary values that verifies the selected
   behavior from rendered geometry and overflow state. A `Text.data` assertion
   proves the input string, not that the intended content was painted. Do not
   add Figma contract fields solely to persist this implementation choice.
7. Add focused tests for the real navigation entry, owned states, overlays, and
   configured viewport. Capture the implemented screen at that viewport and
   compare it with the authoritative Figma screenshot. Check spacing,
   clipping, typography, shell continuity, and each icon's placement box and
   visual glyph bounds. For trimmed text, assert its full Flutter line-box
   height and the next opaque sibling's offset in addition to the screenshot;
   Ahem or fallback-font goldens cannot prove that descenders are visible.
   Widget-existence, route, asset-hash, and container-size assertions alone are
   not visual-fidelity evidence.

## SVG Runtime Asset Pipeline

Run this pipeline for every Figma-exported SVG before approving its runtime
use. It is intentionally narrower than a general SVG optimizer: it never
rewrites paths, transforms, clipping, masks, the `viewBox`, dimensions, or
aspect-ratio behavior.

1. Preserve the raw Figma export and scan it without modification:

   ```bash
   uv run --script <skill-root>/scripts/figma_svg_pipeline.py \
     --project-root <project-root> scan <raw-export.svg> [...]
   ```

   Review every reported dimension, aspect-ratio, overflow, transform, clip,
   mask, filter, and pattern finding against the Figma leaf node and a rendered
   screenshot. These findings are not safe auto-fixes.
2. If the only blocking runtime incompatibility is a `fill` or `stroke` CSS
   variable with an explicit hexadecimal fallback, generate a separate runtime
   asset and a transformation receipt:

   ```bash
   uv run --script <skill-root>/scripts/figma_svg_pipeline.py \
     --project-root <project-root> normalize \
     --output-dir <runtime-asset-directory> \
     --receipt .agents/skills-config/fr-mvvm-contract/<screen>-figma-svg-normalization.json \
     <raw-export.svg> [...]
   ```

   Never use the same path for the raw export and runtime output. Normalization
   refuses unresolved variables, unsupported content, and source overwrite.
3. The receipt schema is
   `fr-mvvm-contract.figma-svg-normalization.v1`. It records
   `source_export_sha256`, `runtime_asset_path`, `runtime_asset_sha256`, and the
   exact normalization applied. Keep the existing asset lock schema unchanged:
   its `path` and `sha256` must identify the runtime asset bytes, while the
   receipt preserves the original export identity and transformation evidence.
4. Verify the receipt after copying, formatting, or replacing assets:

   ```bash
   uv run --script <skill-root>/scripts/figma_svg_pipeline.py \
     --project-root <project-root> verify \
     --receipt .agents/skills-config/fr-mvvm-contract/<screen>-figma-svg-normalization.json
   ```

   The aggregate Figma audit automatically discovers these receipts, requires
   every runtime SVG to be present in an approved screen's asset lock, and
   rejects runtime or receipt hash drift. A valid receipt proves byte
   traceability only; geometry warnings and visual comparison still gate
   approval.

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
assets are rendered by Flutter asset widgets, verifies any discovered SVG
normalization receipts against runtime assets and locks, and requires the
declared test and viewport. Use `--asset-lock` for a focused hash-only lock
check.

The lock schema is `fr-mvvm-contract.figma-assets-lock.v1`. It accepts only
`schema` and `assets`; every asset contains `name`, `path`, `source_export`,
and `sha256`. The audit is a deterministic structural gate; it complements,
but does not replace, contract validation, analyzer checks, focused Flutter
tests, and visual comparison against Figma. Report the structural result and
visual-approval result separately; never describe a passing structural audit
as proof that icon geometry or typography matches. When a contract is excluded,
report `structural audit passed` and `visual status excluded` rather than an
unqualified `pass`.

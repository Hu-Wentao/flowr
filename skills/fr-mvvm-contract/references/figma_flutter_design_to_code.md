# Figma MCP to Flutter Adapter

Use this reference whenever a Flutter implementation reads design context
through the Figma MCP. It specializes the generic Web-oriented
`figma-design-to-code` workflow for Flutter without attempting to bypass the
MCP tool's mandatory prerequisite.

## Responsibility Boundary

1. Load `figma-design-to-code` when required and call `get_design_context`
   before implementation. Use it to acquire node structure, reference code,
   screenshots, annotations, tokens, and exported asset URLs.
2. Treat returned React, Tailwind, `<img>`, CSS sizing, and absolute-positioning
   code as evidence about the design, not as Flutter implementation rules.
3. From the point where Figma evidence is translated into Dart, Flutter
   widgets, typography, assets, tests, and approval status, follow this
   reference and `audit_figma_fidelity.md`.
4. Never claim that this reference replaces or disables a prerequisite imposed
   by the Figma MCP. It replaces only the generic Web-to-code interpretation
   after context acquisition.

## Flutter Conflict Rules

Apply these rules when generic Figma guidance and Flutter fidelity disagree:

- Do not apply a blanket “leaf image fills its fixed-size container” rule.
  Inspect the outer slot or hit area and the inner glyph as separate nodes.
  Give each its own Figma-derived dimensions and center the glyph in the slot.
  Let the leaf fill the slot only when the inspected leaf bounds and slot bounds
  are actually identical.
- Do not translate `<img>` sizing directly into `SvgPicture.asset` sizing.
  Account for the SVG `viewBox`, intrinsic blank bounds, clipping, transforms,
  and `preserveAspectRatio` before choosing the Flutter leaf size.
- Do not substitute a project icon merely because its semantic name matches.
  Require a visual glyph match or use the exact exported asset.
- Do not translate CSS typography values without verifying the runtime Flutter
  font. Confirm family, file availability, weight mapping, size, line height,
  letter spacing, and text bounds. A fallback font is an unresolved visual
  deviation.
- Do not treat React/Tailwind layout structure as proof of Figma ownership,
  navigation-shell ownership, or Flutter widget boundaries. Resolve those from
  the project contract and established Flutter architecture.

The project-specific Flutter rules above are the applicable interpretation of
the generic skill's own requirement to adapt its reference output to the target
framework.

## Required Sequence

1. Resolve `audit_figma_fidelity` and read the resolved project profile.
2. Load the mandatory Figma acquisition skill and call `get_design_context` on
   the primary Frame. Query smaller leaf nodes when the initial context
   collapses an icon, text node, component instance, or state variant.
3. Use metadata and screenshots only for orientation and validation after
   design context has been acquired; never use them as a silent substitute for
   a failed context call.
4. Inventory every icon's slot bounds, leaf bounds, exported asset identity,
   and runtime widget size. Record exact runtime asset bytes in the screen's
   asset lock.
5. Run `figma_svg_pipeline.py scan` for exported SVGs. Use its narrow
   normalization only for supported CSS color fallbacks, then lock the runtime
   bytes and retain the source-to-runtime receipt.
6. Verify actual Flutter fonts before implementing typography. Keep the Figma
   fidelity contract excluded while a required font is unavailable.
7. Capture the implemented screen at the contract viewport and compare it with
   the authoritative Figma screenshot. Structural checks and asset hashes do
   not replace this visual gate.

## Stop Conditions

Keep the contract excluded and report the unresolved evidence when:

- the relevant Figma leaf node cannot be inspected;
- exported asset bytes cannot be retained or verified;
- slot and glyph bounds cannot be distinguished;
- an SVG geometry warning has not been visually reviewed;
- the required runtime font is unavailable; or
- implementation and Figma screenshots have not been compared.

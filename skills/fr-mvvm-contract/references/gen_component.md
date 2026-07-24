# Generic Component Contract Workflow

`gen_component` creates an independently importable feature component library.
Use `draft_contract.py --component-only`; do not create a page adapter.
Default to `--mode bff-json`; use explicit `--mode api --api '<METHOD> <path>'`
only for a concrete backend API.

Choose its directory by reuse scope:

- Use `lib/components/<component-name>/` when multiple routes reuse it.
- Keep a route-owned component under `lib/app/<route-segment>/`.
- Treat a cross-route component as self-contained. Keep every
  module-specific file in `lib/components/<component-name>/`; do not place or
  leave module-specific files in `lib/core/`.
- Reuse plain route-owned Widgets from
  `lib/app/<route-segment>/widgets/` and cross-route Widgets from
  `lib/widgets/`. Do not turn them into components unless they own independent
state, API, Event, or ViewModel responsibilities.
- Preserve established equivalent roots in existing projects unless an
  approved adaptation moves them.

Read `api-contract-semantics.md` before defining UI API DTO fields. Internally
classify each UI API as query or command without asking the user to choose a
type. Let AI organize only the applicable `Behavior` fields, trace each UI API
request field, and reference the SDK-adapter class as `[Type]` in the required
`BFF Service` declaration. Do not author backend APIs or flow.

The component shell owns imports and `.c/.v/.vm` parts. The contract defines
Figma/API facts, state ownership, cross-route `Capabilities` and `Public Views`
when applicable, widget tree, Event and VM
references, `XxxModel` state, BFF/service assets, and ordinary `XxxView` input
fields. It never declares `XxxArgs`, `XxxConfig`, `XxxPageArgs`, or references
typed Page/GoRouter types. `XxxView` owns
its Provider and startup Event. Interaction is Event-driven; do not add Intent
or callback protocols.

When multiple Figma nodes are supplied, first complete
`figma-screen-audit.md`, account for every URL exactly once, and present the
logical owner/state/reference/exclusion map before choosing components.

After drafting the component and before contract review, record the exact
authoritative Figma Frame title and node-specific URL in `.c.dart`. Do not
write contract paths, plugin data, cards, annotations, or other implementation
metadata back to Figma. A missing node-specific URL is a blocking contract
error.

Before contract review, run `discover_ui_reuse.py` and replace the generated
`Widget Tree` TODO. Use the Figma, matching component/Widget catalogs, and component goal to identify user
inputs, actions, primary content, important states, and structural business
components. Preserve only the hierarchy needed to understand composition;
remove state wrappers, implementation bodies, layout glue, decoration, and
component-internal details. Prefer 4–8 key Widgets, fold more than 12 into
business regions, use `× N` for repeated items, and label conditional states
briefly. Do not substitute a natural-language UI summary for Widget references.

Replace the pending UI API method/path, remove the unused query or command
fields from `Behavior`, complete its values and request provenance, then define
UI API DTO fields.
Pending markers are not valid approved input. The draft is a
review state and is not expected to pass the analyzer before its declared
derived parts exist.

After approval, run `validate_contract.py --component-file ... --phase
contract`, then `read_contract.py --component-file`. Run
`generate_from_contract.py --component-file ... --write-stubs` only after that
gate. It preflights Theme and BFF work without mutation, then commits the
prepared file set with rollback protection. It must generate the
component-owned `xxx.bff.md` in BFF-JSON mode. The draft itself contains the
required `fr_acdd` page/root-DTO/JSON declarations, detailed UI-facing
`BFF-API:`, but no backend-call placeholders; backend developers edit only the
protected backend section of the generated BFF artifact. The draft
must not emit a placeholder BFF artifact before approval.

The Python workflow generates or refreshes the frontend-owned BFF content while
preserving the backend-owned section byte-for-byte. Implement the independent
`xxx.srv.dart` as a `lib/api/gen` SDK adapter; generation never creates or
overwrites it.
Implement service integration in `.vm.dart`, then implement `.v.dart`.
Format handwritten files, run build_runner, and require
`validate_contract.py --component-file ... --phase final` plus the repository
analyzer. The generator may refresh only its own unfinished stubs and must
never replace an implemented derived file.

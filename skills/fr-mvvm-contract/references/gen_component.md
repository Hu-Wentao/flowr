# Generic Component Contract Workflow

`gen_component` creates an independently importable feature component library.
Use `draft_contract.py --component-only`; do not create a page adapter.
Default to `--mode bff-json`; use explicit `--mode api --api '<METHOD> <path>'`
only for a concrete backend API.

Choose its directory by reuse scope:

- Use `lib/components/<component-name>/` when multiple routes reuse it.
- Keep a route-owned component under `lib/app/<route-segment>/`.
- Reuse plain route-owned Widgets from
  `lib/app/<route-segment>/widgets/` and cross-route Widgets from
  `lib/widgets/`. Do not turn them into components unless they own independent
state, API, Event, or ViewModel responsibilities.
- Preserve established equivalent roots in existing projects unless an
  approved adaptation moves them.

Read `api-contract-semantics.md` before defining DTO fields. Internally classify
each API as query or command without asking the user to choose a type. Let AI
organize only the applicable `Behavior` fields, trace each request field, and
reference the generated Dart class as `[Type]` in the required `BFF Service`
declaration.

The component shell owns imports and `.c/.v/.vm` parts. The contract defines
Figma/API facts, state ownership, reused components, widget tree, Event and VM
references, `XxxModel` state, BFF/service assets, and ordinary `XxxView` input
fields. It never declares `XxxArgs`, `XxxConfig`, `XxxPageArgs`, or references
typed Page/GoRouter types. `XxxView` owns
its Provider and startup Event. Interaction is Event-driven; do not add Intent
or callback protocols.

When multiple Figma nodes are supplied, first complete
`figma-screen-audit.md`, account for every URL exactly once, and present the
logical owner/state/reference/exclusion map before choosing components.

After drafting the component and before contract review, bind its primary
Frame and every declared `Figma States` Frame to the complete project-relative
`.c.dart` path set. Never bind reference or excluded nodes. Follow
`figma-node-binding.md`: prepare the payload with
`prepare_figma_binding.py`, write its shared plugin data and compact yellow
`.c.dart` card above the concrete target with Figma MCP `use_figma`. Put only
the project-relative path in the card with no label or prefix, and verify data,
placement, and screenshot in a second `use_figma` call. `Figma:` must continue
to identify the concrete page Frame; after the primary write, record its
returned `visibleCardId` in `Figma Contract Card:`, rerun preparation, and use
the refreshed verification payload. Route pages must be
prepared one at a time. For component move, split, or merge, supply the complete
resulting contract set. A missing node-specific URL or failed readback is a
blocking contract error.

Before contract review, replace the generated `Widget Tree` TODO. Use the
Figma, existing component/Widget catalogs, and component goal to identify user
inputs, actions, primary content, important states, and structural business
components. Preserve only the hierarchy needed to understand composition;
remove state wrappers, implementation bodies, layout glue, decoration, and
component-internal details. Prefer 4–8 key Widgets, fold more than 12 into
business regions, use `× N` for repeated items, and label conditional states
briefly. Do not substitute a natural-language UI summary for Widget references.

Replace the pending method/path, remove the unused query or command fields from
`Behavior`, complete its values and request provenance, then define DTO fields.
Pending markers are not valid approved input. The draft is a
review state and is not expected to pass the analyzer before its declared
derived parts exist.

After approval, run `validate_contract.py --component-file ... --phase
contract`, then `read_contract.py --component-file`. Run
`generate_from_contract.py --component-file ... --write-stubs` only after that
gate. It preflights Theme and BFF work without mutation, then commits the
prepared file set with rollback protection. It must generate the
component-owned `xxx.bff.md` in BFF-JSON mode. The draft itself contains the
required `fr_acdd` page/root-DTO/JSON declarations and detailed `BFF-API:`, but
must not emit a placeholder BFF artifact before approval.

The Python workflow immediately reads
the generated `xxx.bff.md` and creates the independent Retrofit `xxx.srv.dart`
containing `Type` only when absent. Preserve any existing `.srv.dart` as
developer-owned project code; run build_runner to generate `xxx.srv.g.dart`.
Implement service integration in `.vm.dart`, then implement `.v.dart`.
Format handwritten files, run build_runner, and require
`validate_contract.py --component-file ... --phase final` plus the repository
analyzer. The generator may refresh only its own unfinished stubs and must
never replace an implemented derived file.

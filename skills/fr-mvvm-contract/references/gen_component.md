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

Read `api-contract-semantics.md` before defining DTO fields. Classify each API
as data or business, complete only the applicable semantic section, trace each
request field, and either omit `BFF Service` for contract-only delivery or
reference the generated Dart class as `[Type]` for runtime integration.

The component shell owns imports and `.c/.v/.vm` parts. The contract defines
Figma/API facts, state ownership, reused components, widget tree, Event and VM
references, `XxxModel` state, BFF/service assets, and ordinary `XxxView` input
fields. It never declares `XxxArgs`, `XxxConfig`, or references `XxxPageArgs`. `XxxView` owns
its Provider and startup Event. Interaction is Event-driven; do not add Intent
or callback protocols.

After drafting the component and before contract review, bind its concrete
Figma node to the complete project-relative `.c.dart` path set. Follow
`figma-node-binding.md`: prepare the payload with
`prepare_figma_binding.py`, write it with Figma MCP `use_figma`, and verify it
in a second `use_figma` call. For move, split, or merge, supply the complete
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

Replace the pending API type/method/path, remove the unused Data/Business
section, complete the applicable semantics and request provenance, then define
DTO fields. Pending markers are not valid approved input. The draft is a
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

When `BFF Service: [Type]` is declared, the Python workflow immediately reads
the generated `xxx.bff.md` and creates the independent Retrofit `xxx.srv.dart`
containing `Type` only when absent. Preserve any existing `.srv.dart` as
developer-owned project code; run build_runner to generate `xxx.srv.g.dart`.
Implement service integration in `.vm.dart`, then
implement `.v.dart`. When `BFF Service` is omitted, deliver only the contract
and do not claim runtime delivery.
Format handwritten files, run build_runner, and require
`validate_contract.py --component-file ... --phase final` plus the repository
analyzer. The generator may refresh only its own unfinished stubs and must
never replace an implemented derived file.

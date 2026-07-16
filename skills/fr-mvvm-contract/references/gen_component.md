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

The component shell owns imports and `.c/.v/.vm` parts. The contract defines
Figma/API facts, state ownership, reused components, widget tree, Event and VM
references, models, BFF/service assets, and optional component-owned `XxxArgs`
or `XxxConfig`. It never declares or references `XxxPageArgs`. `XxxView` owns
its Provider and startup Event. Interaction is Event-driven; do not add Intent
or callback protocols.

Use `read_contract.py --component-file` before editing derived implementation.
After approval, `generate_from_contract.py --component-file ...` must generate
the component-owned `xxx.bff.md` in BFF-JSON mode. The draft itself contains
the required `fr_acdd` page/root-DTO/JSON declarations and detailed
`BFF-API:`, but must not emit a placeholder BFF artifact before approval.

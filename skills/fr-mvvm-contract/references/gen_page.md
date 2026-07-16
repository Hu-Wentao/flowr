# Generic Page Contract Workflow

`gen_page` creates a component contract plus one optional independent route
adapter. It never creates a JSON spec.

1. Read Figma, component catalogs, nearby feature code, and API context.
2. Reuse cross-route components from `lib/components/<component-name>/`; keep
   the route-owned primary component under `lib/app/<route-segment>/`.
3. Decide the primary `XxxView`, component-owned `XxxPageArgs`, models, Events,
   ViewModel, BFF boundary, and route entry.
4. Draft `xxx.dart`, `xxx.c.dart`, and `xxx.page.dart` with
   `draft_contract.py`; stop for review.
5. After approval, run `read_contract.py --page-file` and create derived
   `.v.dart` / `.vm.dart` implementation from that output.

The page file imports its sibling component library, declares one
`/// Component: [XxxView]` marker, converts route arguments to `XxxPageArgs`,
and returns `XxxView`. It contains no Provider, VM, models, DTOs, BFF, or UI.

The primary View may compose multiple other components. `XxxView` owns its
`FrProvider` and uses `FrBlocViewModel<XxxEvent, XxxModel>`.

# Generic Page Contract Workflow

`gen_page` creates a component contract plus one optional independent route
adapter. It never creates a JSON spec.

1. Read Figma, component and Widget catalogs, nearby feature code, and API
   context.
2. Reuse cross-route components from `lib/components/<component-name>/`; keep
   the route-owned primary component under `lib/app/<route-segment>/`.
3. Reuse route-owned plain Widgets from
   `lib/app/<route-segment>/widgets/` and cross-route plain Widgets from
   `lib/widgets/`.
4. Decide the primary `XxxView`, route-owned `XxxPageArgs`, component-owned
   `XxxArgs` or `XxxConfig`, models, Events, ViewModel, BFF boundary, and route
   entry.
5. Draft `xxx.dart`, `xxx.c.dart`, and `xxx.page.dart` with
   `draft_contract.py`; stop for review. Default to `--mode bff-json`. The
   draft includes the `fr_acdd` page/DTO declarations and a complete
   method/path/request/response `BFF-API:` shape, but does not create
   `xxx.bff.md` before the business fields are completed and approved.
6. After approval, run `read_contract.py --page-file` and create derived
   `.v.dart` / `.vm.dart` implementation from that output. BFF-JSON mode must
   also generate `xxx.bff.md` beside `xxx.dart`; explicit API mode does not.

The page file imports its sibling component library, declares one route-owned
`XxxPageArgs` and one `/// Component: [XxxView]` marker, converts the page args
to ordinary View parameters or component-owned `XxxArgs` / `XxxConfig`, and
returns `XxxView`. It contains no Provider, VM, models, DTOs, BFF, or UI.

The primary View may compose multiple other components. `XxxView` owns its
`FrProvider` and uses `FrBlocViewModel<XxxEvent, XxxModel>`.

`draft_contract.py` uses `@FrState`, which enables `toJson`. The shell must
therefore declare both `part 'xxx.freezed.dart';` and `part 'xxx.g.dart';`, and
the owning package must directly declare `json_annotation` as a runtime
dependency and `json_serializable` as a dev dependency. Never install
`json_annotation` with `--dev`. Generate both files with build_runner. If
`_$XxxToJson` or `_$XxxFromJson` is missing, check the dependencies and part
declaration; never implement that function in `.c.dart`, `.v.dart`, `.vm.dart`,
or `.srv.dart`.

Use `--mode api --api '<METHOD> <path>'` only when a concrete backend API is
known. Legacy `--api BFF-JSON` remains a deprecated compatibility spelling.

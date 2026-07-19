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
4. Decide the primary `XxxView`, route-owned `XxxPageArgs`, ordinary View input
   fields, `XxxModel` state, Events, ViewModel, BFF boundary, and route entry.
   Read `api-contract-semantics.md`. Classify each API as data or business,
   define the applicable semantic section, trace request fields, and choose
   whether to omit `BFF Service` for contract-only delivery or declare its
   runtime ownership before writing DTOs.
5. Draft `xxx.dart`, `xxx.c.dart`, and `xxx.page.dart` with
   `draft_contract.py`; stop for review. Default to `--mode bff-json`. The
   draft includes `fr_acdd` page/DTO declarations plus deliberately invalid
   API/semantic placeholders. It does not invent `/bootstrap` or create
   `xxx.bff.md` before the API meaning is completed and approved.
6. Bind the concrete Figma node to the complete generated project-relative
   `.c.dart` path set before review. Follow `figma-node-binding.md`: run
   `prepare_figma_binding.py`, write the emitted shared plugin data with Figma
   MCP `use_figma`, and verify persisted state in a second call. Stop if the
   node-specific URL, write, or readback gate fails.
7. Replace the generated `Widget Tree` TODO before review. Use the Figma,
   existing component/Widget catalogs, and page goal to identify user inputs,
   actions, primary content, important states, and structural business
   components. Keep their necessary hierarchy, then remove state wrappers,
   implementation bodies, layout glue, decoration, and component-internal
   details. Prefer 4–8 key Widgets and fold views with more than 12 into
   business regions. Do not submit a natural-language UI summary in place of
   Widget references.
8. Remove the unused `Data:` or `Business:` draft section, complete the
   applicable section and request-field provenance, replace the pending
   method/path/service values, then define DTO fields. Synchronize the
   adapter's route-owned `XxxPageArgs` conversion with the final ordinary
   `XxxView` fields. The draft is a review state and is not expected to pass
   the analyzer while its declared derived parts do not exist.
9. After approval, run `validate_contract.py --page-file ... --phase contract`,
   then `read_contract.py --page-file`. Contract validation rejects draft
   placeholders but does not require generated Freezed/JSON files.
10. Run `generate_from_contract.py --page-file ... --write-stubs`. It preflights
   Theme and BFF work before committing a rollback-protected derived file set.
   BFF-JSON mode generates `xxx.bff.md`; when `BFF Service: [Type]` is
   declared, the same transaction reads that artifact and creates the
   independent Retrofit `xxx.srv.dart` only when absent. Existing Service code
   is never overwritten. Explicit API mode does not generate a BFF artifact.
11. Run build_runner to generate `xxx.srv.g.dart` for the generated service.
    Implement service
    integration in `.vm.dart`, then `.v.dart`. When `BFF Service` is omitted,
    deliver only the contract and do not claim runtime delivery.
    Format the handwritten files, run build_runner, and require
    `validate_contract.py --page-file ... --phase final` plus the repository
    analyzer before registering the route.

The page file imports its sibling component library, declares one route-owned
`XxxPageArgs` and one `/// Component: [XxxView]` marker, expands the page args
into ordinary View fields, and
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

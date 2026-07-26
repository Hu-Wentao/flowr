# Generic Page Contract Workflow

`gen_page` creates a component contract plus one optional independent route
adapter. It never creates a JSON spec.

1. Run `discover_ui_reuse.py`, then read Figma, matching component and Widget
   catalogs, nearby feature code, and API context. Record whether each shared
   need reuses a public entry, extends its owner, or creates a new owner. For
   multiple supplied nodes, complete `figma-screen-audit.md`,
   account for every URL exactly once, and present the logical page/state map
   before choosing routes or contracts.
2. Reuse or extend cross-route components from
   `lib/components/<component-name>/`; keep the route-owned primary component
   under `lib/app/<feature>/<component-name>/`. A feature directory may group
   related modules, but every Page/Component module must own a separate
   basename-matching leaf directory. Never draft different module shells or
   `*.c.dart` contracts into the same directory.
3. Reuse or extend route-owned plain Widgets from
   `lib/app/<route-segment>/widgets/` and cross-route plain Widgets from
   `lib/widgets/`. Extend the owning module when it already owns the required
   capability; do not recreate its UI in the Page.
4. Decide the primary `XxxView`, `XxxPage` path/query/`$extra` fields, which
   route fields initialize the page ViewModel, any ordinary View input fields,
   `XxxModel` state, Events, ViewModel, BFF boundary, and route entry.
   Read `api-contract-semantics.md`. Internally classify each UI API as query or
   command without asking the user to choose a type. Let AI organize the
   applicable `Behavior` fields, trace UI API request fields, resolve backend
   UI request provenance, and declare the SDK-adapter class in `BFF Service`
   before writing DTOs. Do not author backend APIs or flow.
5. Draft `xxx.dart`, `xxx.c.dart`, and `xxx.page.dart` with
   `draft_contract.py`; stop for review. Default to `--mode bff-json`. The
   draft includes `fr_acdd` page/DTO declarations plus deliberately invalid
   API/semantic placeholders. It does not invent `/bootstrap` or create
   `xxx.bff.md` before the API meaning is completed and approved.
6. Record the exact authoritative Figma Frame title and node-specific URL in
   the generated `.c.dart` contract. Do not write contract paths, plugin data,
   cards, annotations, or other implementation metadata back to Figma.
7. Replace the generated `Widget Tree` TODO before review. Use the Figma,
   existing component/Widget catalogs, and page goal to identify user inputs,
   actions, primary content, important states, and structural business
   components. Keep their necessary hierarchy, then remove state wrappers,
   implementation bodies, layout glue, decoration, and component-internal
   details. Prefer 4–8 key Widgets and fold views with more than 12 into
   business regions. Do not submit a natural-language UI summary in place of
   Widget references.
8. Remove the unused query or command fields from `Behavior`, complete its
   values and request-field provenance, replace the pending UI method/path,
   backend OpenAPI/call-flow, and service values, then define UI API DTO fields. Synchronize the
   typed Page route-field consumption with the final ViewModel factory and
   ordinary `XxxView` fields.
   The draft is a review state and is not expected to pass
   the analyzer while its declared derived parts do not exist.
9. After approval, run `validate_contract.py --page-file ... --phase contract`,
   then `read_contract.py --page-file`. Contract validation rejects draft
   placeholders but does not require generated Freezed/JSON files.
10. Run `generate_from_contract.py --page-file ... --write-stubs`. It preflights
   Theme and BFF work before committing a rollback-protected derived file set.
   BFF-JSON mode generates or refreshes `xxx.bff.md` while preserving its
   backend-owned section byte-for-byte. It never creates or overwrites
   `xxx.srv.dart`. Explicit API mode does not generate a BFF artifact.
11. Implement `xxx.srv.dart` as a `lib/api/gen` SDK adapter, then implement
    service integration in `.vm.dart` and `.v.dart`.
    Format the handwritten files, run build_runner, and require
    `validate_contract.py --page-file ... --phase final` plus the repository
    analyzer before registering the route.

The page file imports its sibling component library, declares one
`XxxPage extends GoRouteData with $XxxPage`, creates the page-scoped
`FrProvider`, dispatches the startup Event, consumes route fields in the
ViewModel factory and/or ordinary View fields, and builds `XxxView` below that
scope. Route and primary View facts are read directly from `@TypedGoRoute` and
`build`, so the file contains no duplicate Route or Component doc markers. It
also contains no Widget adapter, `XxxPageArgs`, models, DTOs, BFF, or UI.

The primary View may compose multiple other components. `XxxView` consumes the
page-owned `XxxViewModel` and does not create a second Provider. This makes the
same page VM available to every descendant in the page subtree.

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

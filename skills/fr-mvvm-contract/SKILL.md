---
name: fr-mvvm-contract
description: Create or adapt ACDD Flutter projects across Android, iOS, macOS, Web, Windows, and Linux; create, validate, or evolve FlowR component contracts, typed Pages, cross-page modules, and persistent navigation shells; audit project-configured Figma screen fidelity; generate, query, collect, package, or project-configure synchronization of BFF contracts; and evaluate optional Flutter command-line packaging or dependency-download optimizations when explicitly requested. Use for new acdd_scaffold projects, existing-project adaptation, contract-first FlowR page or component work, typed route or bottom-navigation-shell refactors, Figma fidelity repair, BFF API inventory or delivery archives, and explicit Flutter build or packaging optimization requests.
---

# FR MVVM Contract

Run every bundled Python entrypoint with `uv run --script <path>`. Add or
update its PEP 723 dependencies with `uv add --script <path> <dependency>`;
never invoke a bundled script with `python`, `python3`, or `uv run python`.

## Mode Selection

- For a new project or `acdd_scaffold`, read
  `references/acdd_scaffold.md` and use `scripts/acdd_scaffold.py`. Do not run
  the project profile resolver before the target project exists.
- For an existing Flutter project that must adopt the standard scaffold
  structure, run:

```bash
uv run --script <skill-root>/scripts/resolve.py --task adapt_project
```

  Follow the resolved inventory, mapping, approval, migration, and validation
  workflow. Treat this skill's `assets/acdd_scaffold/` templates and
  `references/acdd_scaffold.md` boundaries as the standard. Never run
  `acdd_scaffold.py --apply` against the existing project.
- For contract work in an existing project, run:

```bash
uv run --script <skill-root>/scripts/resolve.py --task <gen_page|gen_component|extract_shared_ui|validate|validate_routes|validate_navigation_shell|audit_figma_fidelity|refresh|package_bff|generate_openapi>
```

  Read the resolved instructions once per `instructions_id`.
- For backend OpenAPI-to-Retrofit generation, run the resolver with task
  `generate_openapi`, read `references/generate_openapi.md`, and use
  `scripts/openapi_to_retrofit.py`. Project-specific generic request and
  response wrappers belong in `.agents/skills-config/fr-mvvm-contract/config.yaml`;
  never infer or hard-code their non-generic fields in the reusable skill.
- For a screen whose implementation must be audited or repaired against Figma,
  resolve `audit_figma_fidelity`, read its resolved project profile, and run
  the declared audit command before and after changes. Discover screen
  participation from each primary `.c.dart` contract's `Figma Fidelity:`
  disposition; never maintain a second page registry. Keep the viewport,
  asset-lock path, and regression-test owner in `.c.dart`. Keep only exact
  export identities, repository paths, and hashes in the referenced asset
  lock under `.agents/skills-config/fr-mvvm-contract/`; never hard-code one
  product screen in this reusable skill. Before implementing or approving the
  screen, read `references/figma_flutter_design_to_code.md` to constrain the
  mandatory Figma MCP acquisition skill to evidence collection, then follow
  `references/audit_figma_fidelity.md`, run its SVG scan and safe normalization
  pipeline for exported SVG assets, and preserve icon placement-box versus
  visual-glyph dimensions and exact typography. The SVG pipeline never
  auto-repairs geometry, and a structural audit pass is not visual approval.
- Before editing any Figma-bound Page or component, read
  `references/figma_release_management.md` and run
  `scripts/resolve_figma_release.py` for its `.c.dart`. When project config
  declares releases, treat `active_release` as explicit authority; never infer
  the latest release by sorting names. A `stale` result requires lightweight
  structure discovery in the active file and touched-contract migration before
  implementation. Migrate automatically only when route identity, business
  responsibility, navigation context, primary Frame, and state Frames identify
  one unambiguous successor. Block on missing, split, merged, or ambiguous
  successors. Honor only a reasoned `Figma Release Override`; never create one
  automatically to silence drift.
- For two or more destinations that share a persistent bottom navigation,
  resolve `validate_navigation_shell`, read
  `references/navigation-shells.md`, and run the declared validator before
  changing Pages or routes. Classify the shared shell before auditing each
  destination as a standalone screen.
- Do not propose command-line packaging or dependency-download optimizations
  during ordinary project creation, adaptation, validation, or repair. Only
  when the user explicitly requests build or packaging optimization, read
  `references/optional-build-packaging-optimizations.md`, present the relevant
  options, and obtain the authorization required by the target repository
  before applying them.

## Source-First Layout

Choose ownership and directory by reuse scope:

- Use feature directories only for grouping. Put every Page/Component module
  in its own basename-matching leaf directory; never place different module
  shells or `*.c.dart` contracts in the same directory.
- Put a route-owned component under
  `lib/app/<feature>/<component-name>/` beside its optional page adapter.
- Put a component reused by multiple routes under
  `lib/components/<component-name>/`. Do not duplicate it under each route.
- Keep every implementation artifact of a cross-route component in its own
  `lib/components/<component-name>/` directory. Do not place or leave
  module-specific files in `lib/core/`.
- Keep a Widget used only inside one component private in that component's
  `.v.dart`.
- Put a plain Widget reused inside one route under
  `lib/app/<route-segment>/widgets/`.
- Put a plain Widget reused by multiple routes under `lib/widgets/`.
- Do not give a plain presentation Widget a contract, Provider, Event, or
  ViewModel. Promote it to a component when it encapsulates a reusable business
  capability, app/page state integration, independent state, API, Event, or
  ViewModel responsibility.
- In an existing project with an established equivalent root, preserve that
  root unless the explicit `adapt_project` workflow approves a move. Preserving
  a root never permits several modules to share one leaf directory.

## Shared UI Discovery And Extension

Before modifying a Page or route-owned component, discover reusable UI in this
order:

1. Search `lib/components/` for a component whose `Capabilities:` matches the
   requested capability.
2. Search `lib/widgets/` for a shared Widget module whose `Capabilities:`
   matches the requested capability.
3. Reuse an existing public View or public Widget when it satisfies the
   requirement.
4. When an existing module owns the capability but has no suitable public
   entry, add a semantic public View or Widget in that same module and update
   its public list.
5. Create a new component only when no component owns the required stateful or
   business capability. Create a Widget module only for a cross-page pure
   presentation need.

Run `scripts/discover_ui_reuse.py --project-root <project-root> --capability
"<requested capability>"` before this decision. Treat its output as a catalog,
not an automatic ownership decision: resolve close semantic matches from the
module contract before creating a new module.

## Extract Shared UI

Use `extract_shared_ui` when an existing route-owned View contains a UI entry
that must be reused by another route. Resolve this task, read
`references/extract_shared_ui.md`, and run `extract_shared_ui.py` in dry-run
mode before changing Dart sources. The tool produces a reviewable ownership
and file-migration manifest; `--apply` is permitted only after the manifest is
approved.

Classify by ownership, not by similar appearance:

- A presentation entry with inputs and callbacks only is a shared Widget under
  `lib/widgets/`; it has no contract, Provider, Event, or ViewModel.
- An entry with independent state, API, Event, or ViewModel is a feature
  component under `lib/components/<name>/` and follows the complete
  `gen_component` contract workflow. Do not mechanically move it with the
  Widget extractor.
- Similar widgets with different visual or interaction contracts stay
  separate until an approved design decision defines a common public API.

After extraction, add `Capabilities:` and `Public Widgets:` to the shared
Widget provider, update consumers' `Widget Tree:` entries, rerun reuse
discovery, and validate formatting, tests, and analysis.

`Capabilities:` and public API lists are owned by the provider module:

- A component contract (`lib/components/<name>/<name>.c.dart`) declares
  `Capabilities:` and `Public Views:`.
- A shared Widget module public entry under `lib/widgets/` declares
  `Capabilities:` and `Public Widgets:`.
- Every item in a public list uses a bracket reference and must be accessible
  from that module's public entry.

Consumer Page contracts do not declare `Components:` or `Shared Widgets:`.
Their `Widget Tree:` records the key public Views and Widgets actually composed
by the Page. A Page owns placement and composition; the provider module owns
the reusable UI and its interaction.
- Group tightly related Pages into a cross-page module under one feature
  directory, but keep every Page/Component module in a separate child leaf
  directory. The feature's basename-matching module export must document
  `Pages:` and `Page Data Flow:`. Read `references/validate_routes.md` before
  creating or refactoring that boundary.

## Persistent Navigation Shell Ownership

Before treating several Figma Frames or route roots as complete Pages, determine
whether they are destinations of one persistent navigation shell. Read
`references/navigation-shells.md` whenever two or more destinations share a
bottom bar.

- One shell owns the outer Scaffold, persistent top-region host, and one bottom
  navigation instance.
- Branch Page adapters retain route inputs and page-scoped Providers; branch
  Views contain content only.
- The bottom-navigation Widget accepts selection state and callbacks. It never
  imports branch Page adapters or performs navigation.
- Use `StatefulShellRoute.indexedStack` by default for transition-free branch
  switching with retained independent branch state.
- A zero-duration Page transition or `NoTransitionPage` is not a persistent
  shell repair.
- Root fullscreen routes and overlays cover the shell through the root
  navigator/overlay; a branch ViewModel does not hide or recreate shell chrome.

A reusable feature component is one Dart library:

```text
order_content/
  order_content.dart
  order_content.c.dart
  order_content.v.dart
  order_content.vm.dart        # only for page- or component-owned state
  order_content.srv.dart       # SDK adapter over lib/api/gen
  order_content.bff.md         # required in BFF-JSON mode
  order_content.freezed.dart   # generated by Freezed
  order_content.g.dart         # generated by json_serializable
```

`order_content.dart` owns all imports and part declarations. Its `.c.dart`,
`.v.dart`, and optional `.vm.dart` files use `part of 'order_content.dart';`
and never declare imports. Write every contract section in `.c.dart` with
consecutive `///` documentation comments; do not use `/* ... */` contract
blocks.

Treat `.c.dart` as the source contract, not the View implementation file. Put
its contract comment before `part of`, followed only by stable contract types
such as Models, Events, DTOs, and business enums when they exist. Put every
public and private Widget/View declaration, constructor, `build`, `FrView`, and
visual composition in `.v.dart`. New drafts follow this layout; the reader may
still recognize one legacy View declared in `.c.dart` for migration.

A page is that component plus an optional, independent typed route adapter:

```text
order_content.page.dart
```

The adapter imports `order_content.dart`, extends `GoRouteData`, owns the
page-scoped `FrProvider`, and builds `OrderContentView` below it. It is never a
Widget or a `part` of the component. Deleting the adapter removes the
page-owned lifecycle; app-owned and stateless components remain independently
usable by another page, sheet, tab, or dialog.

## Naming And Ownership

- `XxxPage` lives in `xxx.page.dart`, extends `GoRouteData` with the generated
  `$XxxPage` mixin, owns route inputs as constructor fields, and expands them
  into the page ViewModel factory and/or ordinary `XxxView` fields. It owns the
  page-scoped Provider and dispatches a startup Event only when the contract
  declares `Startup Event: [XxxStarted]`. It is not a Widget.
- Public `*View` entries live in `.v.dart` and are listed authoritatively under
  `Public Views:` in `.c.dart`. A component may expose multiple semantic Views.
  Each consumes its upstream page/app state or ordinary inputs and does not
  create a Provider by default.
- `XxxViewModel extends FrBlocViewModel<XxxEvent, XxxModel>` lives in
  `.vm.dart` only when this module owns page- or component-scoped state; all
  external writes use `add(event)`.
- Component fields, models, DTOs, Events, BFF/service declarations, and the
  component contract belong to the component library.
- Name component state `XxxModel`, BFF request and response boundaries
  `XxxBffReq` and `XxxBffRsp`, and BFF-only nested data `XxxDto`. A project
  request-data-envelope profile may explicitly allow a root `XxxRequestDto`
  in place of `XxxBffReq`.
- A component Service imports the concrete SDK from `lib/api/gen` and calls it
  directly. Permit a semantic `typedef` for an SDK request type when the
  ViewModel constructs that request. Keep response signatures in their original
  generated SDK form by default. Every alias must preserve the exact SDK type,
  fields, generics, and serialization shape.
- Do not generate Intent or callback output protocols. Component interactions
  use the Bloc Event hierarchy. Follow the project's established navigation
  mechanism from Event handlers.
- Put a Provider at the state owner's lifecycle and at the lowest common
  ancestor of all consumers:
  - `app-owned [AppViewModel]`: the root `AppProviders` owns it; the component
    consumes it directly and declares no local VM, Event, Model, or Provider.
  - `page-owned [XxxViewModel]`: `xxx.page.dart` creates it and dispatches the
    optional declared Startup Event; every Widget in that page subtree can
    consume it.
  - `none`: the component uses inputs/callbacks or Widget-local ephemeral
    state and declares no VM, Event, Model, or Provider.
  - `component-owned [XxxViewModel]`: explicit opt-in only for an independently
    embeddable compound component that owns a distinct lifecycle and has
    multiple descendants sharing its state.
- Cross-route shared components must not bind to a route-specific Page
  ViewModel. Consume app-owned state when the state is genuinely global;
  otherwise accept ordinary inputs/callbacks.

## Page Route Inputs And Component Inputs

- Do not declare `XxxPageArgs`. `XxxPage` is the single typed route input
  model; declare path, query, and `$extra` inputs as its constructor fields.
- The component library (`xxx.dart` and its parts) must never reference its own
  sibling `XxxPage`, generated route mixin, `GoRouterState`, or import its own
  `xxx.page.dart`. It may import another target route's `.page.dart` to use its
  generated Page helper or target-owned PageExtra for typed navigation.
- `XxxPage.build` consumes every route field in its ViewModel factory and/or
  ordinary named fields on `XxxView`.
- Do not declare component input wrappers named `XxxArgs` or `XxxConfig`.
- Pass only the route fields needed by `XxxViewModel` from the Page's Provider
  factory. Do not pass the Page route object into the component library.
- Use a route-owned `XxxPageExtra` only when several non-URL values must travel
  together through `$extra`. Declare it directly in the target `xxx.page.dart`,
  never in an independent model file. Treat it only as a route transport model,
  not domain data or ViewModel state. The target Page must expand it into
  ordinary View fields. Declare it with `@FrAcddFreezedJSON`, a redirecting
  `const factory`, and `fromJson`; add the page `.freezed.dart` part and retain
  its shared generated `.page.g.dart` part. Configure one application-owned
  `GoRouter.extraCodec` with tagged encode/decode cases for every PageExtra.
  Preserve the approved PageExtra field contract during migration; serialization
  requirements do not authorize changing field names, values, ownership, or
  lifecycle. Read `references/typed-routing.md` for the required shape.

| Type | File | Consumers |
|---|---|---|
| `OrderContentPage.orderId` | `order_content.page.dart` | Path input and route system |
| `OrderContentPage.entryPoint` | `order_content.page.dart` | Query input and route system |
| `OrderContentView.orderId` | `order_content.v.dart` | View only, when rendering needs it |
| `OrderContentView.entryPoint` | `order_content.v.dart` | View only, when rendering needs it |

Use this standard conversion shape:

```dart
@TypedGoRoute<OrderContentPage>(path: '/orders/:orderId')
class OrderContentPage extends GoRouteData with $OrderContentPage {
  const OrderContentPage({required this.orderId, required this.entryPoint});

  final String orderId;
  final String entryPoint;

  @override
  Widget build(BuildContext context, GoRouterState state) => FrProvider(
        (context) => OrderContentViewModel(
          orderId: orderId,
          entryPoint: entryPoint,
        ),
        onCreated: (context, vm) => vm.add(const OrderContentStarted()),
        child: const OrderContentView(),
      );
}
```

Page fields describe how the route enters and initialize page-owned state.
Ordinary View fields are reserved for values the View itself must render
without reading that state. Keep route types out of the component library.

## Page Contract

`xxx.page.dart` declares one route-to-Provider-to-view adapter:

```dart
@TypedGoRoute<OrderContentPage>(path: '/orders/:orderId')
class OrderContentPage extends GoRouteData with $OrderContentPage {
  /* route fields -> page ViewModel and/or View fields */
}
```

The route path is read from `@TypedGoRoute`, and the primary View is inferred
from `XxxPage.build`; do not duplicate either fact in documentation comments.
The primary View may compose any number of public/shared components and
Widgets recorded in its `Widget Tree:`; it does not limit a page to one
component. A page file may
declare additional typed Page variants for distinct URLs only when every
variant builds the same primary View; keep the basename-matching
`XxxPage` as the primary entry.

## Typed Routing

- New scaffolds use `go_router_builder` by default. Keep it and `build_runner`
  in `dev_dependencies`; every independent `xxx.page.dart` generates its own
  `$appRoutes`, and the root `app_router.dart` spreads those prefixed lists.
- Before adding or changing a route, read `references/typed-routing.md`.
- For a cross-page module or PageExtra migration, resolve `validate_routes`,
  read `references/validate_routes.md`, and run its module validator.
- For persistent bottom-navigation destinations, resolve
  `validate_navigation_shell`; branch switching uses the shell's `goBranch`
  API and is not Page-to-Page typed navigation.
- Make `XxxPage` the `GoRouteData`; do not create a separate `XxxRoute` or
  `XxxPageArgs`. Its `build` creates the page scope and constructs the primary
  `XxxView` below it.
- Navigate with generated route helpers when the destination is known in app
  code. Keep raw URI navigation only at explicit external/dynamic URI
  boundaries. `validate_routes` rejects fixed `context.go`/`push`/`replace`
  calls and `AppRoutes.xxx` indirection when the URI matches a typed Page;
  document exceptional compatibility boundaries with the required reasoned
  marker from `references/validate_routes.md`.

## Contract-First Workflow

1. Inspect Figma, run shared UI discovery, inspect the matching component and
   Widget module catalogs, nearby usage, and API context. Record one outcome:
   reuse an existing public entry; extend its owning module because no entry
   fits; or create a module because no module owns the capability. When the
   request supplies multiple Figma nodes or a Figma container node, first read
   `references/figma-screen-audit.md` and account for every supplied URL as a
   primary Frame, same-owner state, visual reference, or explicit exclusion.
   Inspect a container's structure before requesting any full design context;
   select concrete Frames from that structure rather than reading the
   container as though it were a page.
   Present the resulting logical page/state ownership map before drafting.
   When primary Frames share a bottom navigation, also present their shell
   membership and classify shell roots, branch children, root fullscreen
   routes, and overlays before selecting Page or Scaffold ownership;
   never infer route or contract count from link count or visual similarity.
   Page drafts default to `BFF-JSON` when no concrete API is supplied.
   Shared component drafts default to `local` with `State Ownership: none`.
   Read
   `references/api-contract-semantics.md`; draw the cross-component data and
   business flow before defining DTOs.
2. For `gen_page`, draft `xxx.page.dart`, `xxx.dart`, `xxx.c.dart`, and the
   reviewable public-View stub in `xxx.v.dart`:

```bash
uv run --script <skill-root>/scripts/draft_contract.py \
  --name order_content --dir lib/app/order_content \
  --figma-url <url> --figma-frame <exact-frame-title> --mode bff-json --route <route> \
  --theme <none|material|app-shared|component>
```

   For `app-shared` or `component`, also pass `--theme-type <ThemeType>`.
   Repeat `--extra-field name:DartType` when the Page needs multiple `$extra`
   values. The draft emits the required
   `@FrAcddFreezedJSON` PageExtra, generated parts, typed `$extra`, and
   PageExtra-to-ViewModel expansion. Register every emitted type in the
   application route-extra codec before final validation.

   Use `lib/app/<route-segment>/` for a route-owned component and
   `lib/components/<component-name>/ --component-only` for a component reused
   across routes. `--component-only` defaults to `--mode local --state-owner
   none`, so it emits no VM, Model, Event, Provider, Freezed, JSON, or BFF
   assets. Use `--state-owner app --state-type <AppViewModel>` when it consumes
   an existing root-provided VM. Use `--state-owner component` only after
   explicitly proving an independent component lifecycle; component-owned
   API/BFF modes require that flag. Use an existing project's established
   equivalent roots when they differ, unless an approved adaptation moves
   them.
3. Bind the primary Figma Frame and every declared `Figma States` Frame back
   to the generated Dart files before contract review. Never bind `Figma
   References` or `Figma Excluded`. Record the exact primary Frame title and
   complete node-specific URL in `Figma.Node`; record each `Figma States`
   target as only its `node-id`, resolved against that primary design file.
   Never repeat the design URL in `Figma States`. For an approved screen, add
   exactly one `Figma Fidelity:` section in this fixed shape:

```dart
/// Figma Fidelity:
/// - Viewport: 360 x 780
/// - Asset Lock: .agents/skills-config/fr-mvvm-contract/order-figma-assets.lock.json
/// - Regression Test: orderFigmaFidelity renders approved states
```

   Use `Asset Lock: none` only when the authoritative Frame has no exported
   assets. Do not put the Figma file/node, viewport, routes, copy, source
   assertions, or test names in the lock. Do not write contract metadata,
   shared plugin data, or visible cards into Figma.
   Use the one-line `Figma Fidelity: excluded | <reason>` form instead when
   the current implementation is explicitly outside the approved gate.
   Prepare page contracts and target Frames one at a time; a page contract must
   target its exact Figma Frame, never a Section containing several pages.
   Execute the
   emitted `verifyCode` in a second `use_figma` call and inspect its screenshot.
   Do not continue if the primary URL lacks `node-id`, a page target is a
   non-Frame,
   either representation is missing or stale, the card is not above its page,
   a path is not visibly rendered, or the independent readback differs.
4. Internally classify each UI-facing BFF API as `query` or `command`; do not ask the user to
   choose a type or write an API-type field. Let AI organize one `Behavior:`
   section. For a query, define UI Data, Source, Loading/Refresh, and
   Empty/Error. For a command, define Effect, Success, Failure with App
   recovery, and Navigation. Trace every UI API request field to its source and
   purpose. Do not author `SDK Calls`, `SDK Call Flow`, backend method/path
   annotations, or backend orchestration in `.c.dart`. Backend developers own
   those facts and edit only the protected backend section of `xxx.bff.md`.
   The skill may define and refresh the frontend UI data API, UI DTOs, state,
   behavior, structure, and integration mapping. It must preserve the complete
   backend section byte-for-byte. Set `BFF Service` to the Dart SDK-adapter
   service class, such
   as `[OrderContentService]`; every BFF-JSON contract requires runtime
   integration. If
   any semantic answer is unknown, stop for user input; never invent
   `/bootstrap`, `nextRoute`, proof, result, or error placeholders.

   Write descriptive contract values in the resolved `Contract Description
   Language`. This applies to Behavior entries, Request Field Sources
   purpose prose, and Notes. Keep stable labels, code identifiers, types,
   methods, paths, enum literals, and authoritative source expressions
   unchanged.

   Keep the remaining approval contract minimal: Figma, API/BFF, state ownership,
   reusable UI in the Widget Tree, theme, Event and ViewModel
   references, models, and concise notes. Page Support contains only route and
   primary View facts.
   Define `Widget Tree` as a concise hierarchy of key Widgets that lets a
   reviewer understand the View from `.c.dart` alone. Include a Widget when it
   is directly interactive, carries primary information, expresses an
   important state, determines the functional structure, or is a shared
   component developers must recognize. Prefer 4–8 key Widgets and keep even
   complex Views to at most 12; fold larger trees into business-level regions,
   use `× N` for repeated items, and mark conditional states briefly.

   When `Public Views:` lists more than one entry, write one `Widget Tree`
   bullet per public View in the same order. Do not add a discriminator enum
   merely to force semantically different entries through one generic View.

   Preserve only necessary hierarchy. Omit formulaic `_XxxViewBody` nodes,
   `FrProvider`, `FrConsumer`, `Builder`, layout glue such as `Padding`,
   `SizedBox`, `Spacer`, `Align`, `Expanded`, `Flexible`, and `SafeArea`, pure
   decoration such as `Divider` and `DecoratedBox`, and component-internal
   labels/icons/spacing already covered by the parent component. Omit `Row`,
   `Column`, `Stack`, and `Container` unless one is essential to disambiguate
   business structure. A semantic private Widget such as `[_HomeHeader]` may
   remain.

   Do not replace key Widget references with prose such as `confirmation form`.
   Do not draw a UI diagram or reproduce the complete runtime Widget tree.
   The provider module's public list is the dependency/reuse inventory; the
   concise `Widget Tree` records the entries actually composed here. Replace the generated TODO with an informative,
   concise tree before contract review and approval.
   Remove the unused query or command fields from `Behavior`, replace every
   pending marker, then define DTO fields and synchronize typed `XxxPage`
   route fields to the final ordinary `XxxView` fields. The draft shell deliberately names not-yet-generated
   parts, so this review state is not a compilation or analyzer gate.
5. Present the UI API method/path and Req/Rsp/Error, AI-organized behavior,
   field provenance, and SDK-adapter service class. Do not present, propose, or
   edit backend APIs or flow; backend developers maintain them in `xxx.bff.md`.
6. Validate the approved source contract before deriving files. This phase
   rejects semantic/API placeholders, mixed or incomplete query/command
   behavior, untraceable request fields, UI-only command responses, invalid
   typed Page route-field conversion, incomplete Theme declarations, and missing direct
   dependencies, but does not require Freezed/JSON output yet:

```bash
uv run --script <skill-root>/scripts/validate_contract.py \
  --page-file path/to/xxx.page.dart --phase contract
```

7. For all non-contract work, read the contract through scripts rather than
   manually deriving decisions from raw Dart:

```bash
uv run --script <skill-root>/scripts/read_contract.py \
  --page-file path/to/xxx.page.dart
uv run --script <skill-root>/scripts/read_contract.py \
  --component-file path/to/xxx.dart
```

8. Prepare derived parts only from the approved reader output. The generator
   preflights the complete contract, Theme target, dependencies, and BFF
   extractor before committing any file. It prepares Theme changes, the BFF
   artifact, then `.vm.dart` and `.v.dart` stubs as one rollback-protected file
   set. An extractor or Theme failure must leave every prior file unchanged:

```bash
uv run --script <skill-root>/scripts/generate_from_contract.py \
  --page-file path/to/xxx.page.dart --write-stubs
```

Every BFF-JSON contract with runtime backend calls declares
`BFF Service: [Type]`. Use one Service per component. The Service imports the
required concrete SDK files from `lib/api/gen`, constructs configured generic
wrappers internally, and exposes semantic methods to its ViewModel. Do not
generate a frontend Retrofit client from the UI data API.

A project may require every `XxxBffRsp` to model a complete gateway response such as
`{state, code, message, data}`. In that case the original business response is
the value of its `data` field, not a replacement for the outer envelope.

Generated `*.bff.md` files begin with compact `bff-md-meta/v8` YAML Front
Matter containing schema, `@FrAcddPage` namespace/version, the authoritative
UI design source, a namespaced mdq v2 API-record contract, and no derivable
contract-file path. They separate inline UI
API DTOs from OpenAPI-owned backend operations, backend call flow, frontend UI
data, integration mapping, and a generated `API Query Records` verification
projection. Render UI State exclusively as a JSON5 code
block: every field has consecutive Model, Dart type, and `Authority: Frontend`
comments. Do not use Markdown tables for UI State. Read
`references/bff-dual-authority.md` before changing artifact structure,
ownership, generation, parsing, or validation.

Render BFF artifacts in this fixed order: title, `后端业务流程与业务逻辑 API`, and
`前端 UI 数据接口`. The backend domain contains only OpenAPI document references,
the business API annotations and business flow written by backend developers.
Each business API annotation retains only method/path, parameter names and
types, and response DTO type. It never expands DTO fields. Backend developers
alone create and edit this entire domain. AI may create only UI-facing paths
and `XxxBffReq`/`XxxBffRsp` DTOs from approved Figma/UI requirements.

The generator never creates or overwrites `xxx.srv.dart`. Implement it from the
backend-owned BFF flow with concrete `lib/api/gen` clients, then import it from
the component shell. A request type constructed by the ViewModel may receive a
semantic `typedef`; response signatures remain the original generated SDK type
unless the response itself must be stored or passed as a declared type. The
Service uses the application-provided `Dio` and does not add interceptors or
own a base URL. Implement `.vm.dart` before `.v.dart`.
`--replace-derived-stubs` may
refresh only files that still contain its generated-stub marker; deprecated
`--force` has the same restricted behavior.

9. Format handwritten Dart, run build_runner (including typed routes), refresh
   the BFF verification projection after Service/ViewModel integration, then
   require final validation
   and the repository analyzer:

```bash
fvm dart format path/to/component/files
fvm dart run build_runner build
uv run --script <skill-root>/scripts/generate_bff.py \
  --component-file path/to/xxx.dart
uv run --script <skill-root>/scripts/validate_contract.py \
  --page-file path/to/xxx.page.dart --phase final
fvm flutter analyze
```

Do not create or persist a JSON spec file. Do not register the route until the
component passes final validation and analysis.

## BFF Delivery Package

After all component BFF artifacts are generated and current, resolve
`package_bff` and run its `package` command. The generic command collects every
project `*.bff.md` into `build/bff-contracts.zip` while preserving relative
paths. OpenAPI documents remain independently owned references and are never
included in the BFF package. Read `references/package_bff.md` for exclusions
and project configuration.

Allow a project profile to override `package` or declare an optional `sync`
command. Treat `sync` as a separate external mutation: show its destination
and side effects and obtain explicit authorization before copying, committing,
or pushing to another repository. An explicit request to sync, publish, or
update the configured shared repository is that authorization, including its
required push to the configured ref; never request a second push confirmation.
Once authorization is explicit, always run the resolved `sync` command after
validation and packaging, even when every local `*.bff.md` is current and Git
reports no BFF changes. Local freshness does not prove destination parity; let
the configured sync command compare the destination and decide whether a commit
is necessary. Resolver execution never authorizes or runs configured commands.

Use these delivery outcomes exactly when the configured destination is a shared
authority repository:

- `packaged`: the delivery archive exists only in the source repository.
- `published`: the configured remote ref has been read back and its commit is
  exactly the destination checkout commit produced or selected by `sync`.

Only `published` satisfies a request to sync, publish, deliver, or update the
shared authority repository. A local file, local checkout, or local commit is
never evidence that the repository was updated. If publication authorization
is absent, report the current non-published state and request that authorization;
do not claim completion. If authorization is present, do not stop after commit:
push and verify the exact remote ref and commit. A successful command without
that remote evidence is not a delivery outcome, so report the task as incomplete.
Project profiles may define which user phrases grant publication authorization;
follow that definition without asking again, but never infer broader mutations.
If unrelated commits would be included in the push, stop and report that scope
conflict instead of publishing them under the sync authorization.

## Theme Contracts

- Use exactly `Theme: none`, `Theme: material`,
  `Theme: app-shared [ThemeType]`, or `Theme: component [ThemeType]`.
- Do not declare a separate `Theme Ownership` section. `app-shared` and
  `component` select `fr_mvvm_theme` ownership directly from `Theme`.
- Treat any other Theme text as legacy. The reader may expose it with a
  migration warning, but validation and derived generation must stop until the
  declaration is migrated.
- When the project directly depends on `fr_mvvm_theme` and the approved
  contract uses `app-shared` or `component`, load the `flowr-usage` skill. Read
  `references/fr-mvvm-theme-install.md` when package or root extension
  injection is missing; otherwise read `references/fr-mvvm-theme.md`.
- Generate one app-shared Theme type under `lib/core`, register it as a named
  `AppThemeModel` field, and keep that `FrPageTheme` object as a top-level
  `toJson()` value. Reuse the same type for every contract that names it.
- Generate a component-owned Theme as `xxx.thm.dart` and add it to the
  component shell.
- Read custom Theme values with `context.ofThm<ThemeType>()`. Never replace
  an approved `FrPageTheme` with `abstract final class XxxColors`.
- For `material`, read shared semantic colors from
  `Theme.of(context).colorScheme`; do not generate a page color table or a
  `FrPageTheme`.

## Validation

- Run `validate_navigation_shell` whenever a Page is a declared persistent
  shell destination. A valid result requires one shell owner, passive bottom
  navigation, content-only branch Views, stateful indexed-stack routing, and
  focused runtime coverage. A final-state-only `pumpAndSettle()` assertion does
  not prove transition-free switching.
- Use `--phase contract` before `generate_from_contract.py`. Use `--phase
  final` only after `.srv/.vm/.v` implementation and build_runner. Omitting
  `--phase` retains the legacy source-validation behavior for compatibility;
  it is not the final completion gate.
- Every Page/Component module must own its leaf directory. Validation rejects
  any sibling module shell or `*.c.dart` contract with a different basename.
- Every UI-facing BFF API declares one `Behavior:` section whose fields let the parser infer
  internal `query` or `command` kind. The contract exposes no API-type field.
  Every BFF request field declares one authoritative source and UI API purpose.
  Backend developers record each business API in the protected BFF Markdown
  section as `- [id] METHOD /path | Parameters: name Type[, ...] | Response:
  Type`, then reference every id from `### 业务流程`. The skill validates these
  annotations against OpenAPI and `lib/api/gen` but never edits them.
  Read `references/api-contract-semantics.md` for syntax.
- A command response must contain a non-UI result referenced by `Success`.
  UI/navigation fields cannot be the only command response, and
  every failure maps to App recovery/display.
- Every BFF-JSON contract with backend calls declares `BFF Service: [Type]`,
  pointing to the single component SDK-adapter class in `xxx.srv.dart`.
  The Service must import at least one concrete SDK file from `lib/api/gen` and
  must not be `@RestApi`. Validation also requires ViewModel
  injection, async request/response handling, failure state,
  submitting/loading recovery, and success-before-navigation part of final
  validation. Contract-only BFF delivery is not supported.
- A component must not import or reference its sibling `.page.dart` adapter or
  sibling PageExtra. A source component may depend on another target Page
  adapter for typed navigation.
- `Public Views:` is the authoritative inventory for new and migrated modules;
  every listed class must be public and declared by the component library, and
  every exposed public `*View` must be listed. Page adapters still select one
  primary View from this inventory.
- `Widget Tree:` must exist and contain one root per public View in declared
  order, with at least one key Widget after each root. It must contain no TODO,
  formulaic `_XxxViewBody`, state/implementation wrapper, or deterministic
  layout/decorative noise, and no more than 12 non-root Widget references.
- `app-shared` and `component` must name a Theme type. The type must extend
  `FrPageTheme<ThemeType>`; app-shared types must be registered in
  `AppThemeModel`, retained as objects by `toJson()`, and injected from the root
  `ThemeData(extensions: theme.data.extensions)` path.
- `.v.dart` must not statically reference `XxxColors` for an `app-shared` or
  `component` Theme contract. `material` contracts must use
  `Theme.of(context).colorScheme`.
- `.c.dart` must not declare a type whose name ends in `PageArgs`, `Args`, or
  `Config` for component input wrapping.
- `.c.dart` contract sections must use consecutive `///` documentation
  comments before `part of`; block-comment contracts are invalid. Public and
  private View/Widget declarations belong in `.v.dart`.
- Every primary `Figma:` contract must declare exactly one `Figma Fidelity:`
  disposition. Aggregate discovery rejects missing/invalid dispositions,
  unsafe or reused asset-lock paths, duplicate audited Figma bindings, unused
  or unrendered locked assets, and a missing declared regression test or
  viewport. `Figma Fidelity: excluded |
  <reason>` is an explicit unapproved state, not evidence of visual
  completion.
- When project config declares `figma.releases`, aggregate discovery also
  resolves every concrete contract file key. `gradual` enforcement reports
  unexcepted archived bindings as stale migration work; `strict` rejects them.
  Unknown and candidate releases, malformed overrides, and mixed-file
  declarations always fail. A pinned archived release requires
  `Figma Release Override` with a matching release and non-empty reason.
- Component sources must not reference their own `XxxPage`, `GoRouterState`,
  generated sibling route mixin, or sibling `.page.dart`; cross-route target
  Page/PageExtra references are allowed.
- Component navigation to an internally known typed Page must use
  `XxxPage(...).go/push/replace(context)`. Fixed raw URI calls and
  `AppRoutes.xxx` are invalid substitutes except at a reasoned compatibility
  boundary defined by `validate_routes`.
- Every `XxxPageExtra` must use the `@FrAcddFreezedJSON` Freezed shape,
  generated JSON hooks, and the application route-extra codec. Validation
  requires explicit encoder and decoder coverage for every transported
  PageExtra; `toJson()` without typed `fromJson` restoration is invalid.
- `.page.dart` declares `XxxPage extends GoRouteData with $XxxPage`, contains
  no `XxxPageArgs`, and consumes every route field in the page ViewModel
  factory and/or ordinary View fields.
- `State Ownership: page-owned [XxxViewModel]` requires every typed Page
  variant to create `FrProvider`; when `Startup Event: [XxxStarted]` is
  declared, every variant dispatches it in `.page.dart`. The component View
  must not create another Provider.
- `State Ownership: app-owned [AppViewModel]` and `none` reject local Provider,
  VM part, Events, and Models. `component-owned [XxxViewModel]` requires a
  View-owned Provider and is an explicit exception.
- `read_contract.py --component-file` must work after removing `.page.dart`.
- A page adapter must import its sibling component library. Every typed Page
  variant must declare a string-literal `@TypedGoRoute` path and build the same
  public `XxxView` below its page scope; Route and Component doc markers are
  redundant and must not be generated.
- `xxx.bff.md` and `xxx.srv.dart` are component assets, not
  page assets. `xxx.srv.dart` is an independent SDK-adapter library imported by
  the component shell; it is not a Dart `part` of the component.
  `xxx.bff.md` is mandatory in BFF-JSON mode and omitted only in explicit API
  mode. It begins with compact `bff-md-meta/v8` YAML Front Matter followed by
  its BFF contract title, then separates the backend logic, UI API Contract,
  UI Contract, Integration Mapping, and mdq-backed API Query Records. Read `namespace` and
  `contract_version` from `@FrAcddPage(version: ...)`; the annotation field is
  exactly `version`, never `contractVersion`, and the artifact schema version
  is not the contract version.
  UI State is one JSON5 code block, not a Markdown table, with Model, Dart
  type, and Frontend-authority comments on every field.
- `API Query Records` is the one flat GFM matrix intentionally retained for
  collection queries. It must expose backend, UI, runtime-only, and API-less
  dispositions with explicit contract and integration statuses. Runtime-only
  rows report missing backend authority without modifying the backend-owned
  section. `generate_bff.py --check` rejects stale rows after Service or
  ViewModel changes.
- BFF-JSON contracts import `fr_acdd`, declare exactly one
  `@FrAcddPage(mode: FrAcddMode.bff)`, at least one root `@FrAcddDto`, and use
  `@FrAcddFreezedJSON` plus `fromJson` for every BFF DTO. Every referenced
  `XxxBffReq` (or explicitly profiled `XxxRequestDto`) also explicitly declares
  `Map<String, dynamic> toJson();` for deterministic UI DTO serialization. `BFF-API:`
  names the UI-facing HTTP method, path, request DTO, and `XxxBffRsp`; DTOs used
  only inside that UI API boundary use `XxxDto`. Backend operations never add
  Dart DTOs to this section. Backend method/path/type annotations and flow live
  only in the backend-owned BFF Markdown section. A Service consumes the
  referenced concrete SDK API directly; it must not add an aggregate SDK client
  or a synthetic backend boundary.
- Generate or check BFF delivery with
  `generate_bff.py --component-file path/to/xxx.dart [--check]`. Treat
  extractor preflight or dependency incompatibility as a hard failure. This
  command refreshes only frontend-owned BFF content and preserves the backend
  section. `--check` confirms the referenced SDK-adapter class without
  comparing `.srv.dart` with a generated template.
- Final validation requires every declared Dart part to exist, rejects the
  generated `.v` and applicable `.vm` stub marker, and requires
  `.freezed.dart` plus `.g.dart` whenever `@FrState` / `@FrStateJson` enables
  JSON generation.
- Use `@FrState` / `@FrStateJson` Freezed models; keep model/view helpers and
  Event handlers in `.vm.dart`.
- Both `@FrState` and `@FrStateJson` require JSON code generation because both
  presets enable `toJson`. Declare `part 'xxx.g.dart';` beside
  `part 'xxx.freezed.dart';`. In the package that owns the model, add
  `json_annotation` as a direct runtime dependency and `json_serializable` as
  a direct dev dependency. Never add `json_annotation` with `--dev`.
- Generated `_$XxxToJson` / `_$XxxFromJson` functions may exist only in the
  generated `.g.dart`. Never define them in `.c.dart`, `.v.dart`, `.vm.dart`,
  or `.srv.dart`.
- When a generated JSON function is missing, check the owning package's
  `json_annotation` / `json_serializable` dependencies and the shell's
  `.g.dart` part, then run
  `fvm dart run build_runner build`. Never repair
  generation by writing the function in a VM or another source part.
- Component SDK-adapter services use the application-owned `Dio` through the
  generated clients in `lib/api/gen`. The application root registers shared
  interceptors once; component services never mutate that instance or own its
  base URL.
- Format changed Dart files, run build_runner when generated parts change, and
  run the repository analyzer command.

## Compatibility

- `acdd_scaffold` supports Android, iOS, macOS, Web, Windows, and Linux while
  retaining Android+iOS as the default. It applies macOS deployment, storage,
  entitlement, and Debug signing configuration only when macOS is selected.
- macOS Debug uses an embedded development-only encryption key and separate
  unsandboxed entitlement so local startup does not require Keychain, an Apple
  Team, or a personal certificate. Profile and Release remain sandboxed and use
  Keychain Sharing; configure project-owned identity and signing before
  distribution. Never use Debug storage for real sensitive data.
- Existing-project adaptation preserves the project's current platform targets,
  organization identifiers, routes, business behavior, and platform-native
  configuration unless the user explicitly approves changing them.
- Adaptation is structural, not a destructive regeneration: merge required
  scaffold responsibilities into existing code and do not overwrite the
  project with `acdd_scaffold.py`.
- Existing projects keep their current page roots; only new scaffolded projects
  default route-owned components to `lib/app/<route-segment>/` and cross-route
  components to `lib/components/<component-name>/`. Route-owned shared Widgets
  default to `lib/app/<route-segment>/widgets/`; cross-route shared Widgets
  default to `lib/widgets/`. When the explicit `adapt_project` task is
  requested, move code toward those roots only through an approved
  current-to-target mapping.
- Figma is read-only for contract tracking. Every primary contract records the
  exact Frame title and complete node-specific URL in `.c.dart`; each `Figma
  States` entry records only its `node-id`. No `flowr` shared
  plugin data, cards, annotations, or equivalent contract metadata is written
  into Figma.
- Existing full-URL `Figma States` entries remain readable for compatibility;
  every new or modified state declaration uses only `node-id`. No compatibility
  configuration is required.
- Figma release configuration is optional. Projects without it retain
  contract-only binding behavior. Projects that enable it keep only global
  immutable release names, file keys, statuses, the explicit active release,
  and enforcement mode in `skills-config`; the concrete primary URL and state
  node IDs remain solely in `.c.dart`.
- The contract workflow replaces the old JSON-first `new_page.py --spec-file`
  and single `xxx_page.dart` layout. No compatibility mode is provided.
- Strict contract/final validation rejects legacy API contracts without a
  complete query or command `Behavior`, BFF request provenance, or the required
  generated BFF Service class. `BFF Runtime`, `BFF Service: none`, and omitted
  BFF Service declarations are obsolete. Drafts no longer contain a usable
  default method/path.
- `Backend Calls`, `Backend Call Flow`, `SDK Calls`, and `SDK Call Flow` are
  rejected in frontend `.c.dart` contracts. Backend developers maintain the
  protected `后端业务流程与业务逻辑 API` section in `xxx.bff.md`.
- Local OpenAPI references resolve from the project root when no profile is
  configured. Projects may configure another contained checkout root, but BFF
  packages and synchronization never include local OpenAPI documents; publish
  those documents through their independent authority.
- Free-text Theme declarations are legacy schema. They remain readable only to
  produce an explicit migration warning; refresh, generation, and strict
  validation require one of the structured Theme forms above. Existing
  `none` and `material` declarations keep their behavior.

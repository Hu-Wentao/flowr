# FR MVVM Contract Refactor Plan

## Purpose

Refactor `fr-mvvm-contract` from a JSON-first page generator into a generic,
contract-first component skill. Project behavior remains tracked in
`.agents/skills-config/fr-mvvm-contract/`; the reusable skill must not absorb
HSG-specific branches.

## Accepted Architecture

The primary unit is a component contract, not a page contract:

```text
order_content/
  order_content.dart
  order_content.c.dart
  order_content.thm.dart       # optional component theme implementation
  order_content.v.dart
  order_content.vm.dart
  order_content.srv.dart
  order_content.bff.md
  order_content.page.dart      # optional Page Support
```

`order_content.dart` plus its parts are one independently importable component
library. `order_content.page.dart` is a separate Dart library that imports it.
Deleting `.page.dart` removes only route access and its router registration;
the component library must remain analyzable and reusable.

`XxxPage` is the route adapter. `XxxView` is the component entry. `XxxView`
creates its own `FrProvider`; `XxxViewModel` owns `FrBlocViewModel<XxxEvent,
XxxModel>` behavior. Every embedding therefore owns an independent feature VM
lifecycle. Do not give pure presentation components a VM merely for symmetry.

## Ownership

Page Support contains route entry, route-owned `XxxPageArgs`, conversion to
ordinary View parameters or component-owned `XxxArgs` / `XxxConfig`, and the explicit
`/// Component: [XxxView]` marker. A page may use many components; this marker
only identifies the direct root View.

The Component Contract contains Figma facts, API/BFF boundary, state ownership,
component choices, widget tree, theme, model/DTO declarations, Event and VM
references, and BFF/service ownership. `xxx.srv.dart` and `xxx.bff.md` are
component assets.

There are no Intent or callback output contracts. Interaction is modeled with
Bloc Events. The component VM may use the repository's established navigation
mechanism from Event handlers; Page Support does not listen for or translate
component events.

## Theme Ownership

Theme ownership follows the library that statically references the Theme type.
Shared design-system tokens remain in app/shared theme. A component-private
typed theme that is read by `XxxView` or `.v.dart` belongs to the component
library, never to Page Support.

New components default to `/// Theme: none` and use shared Theme. Generate the
optional `xxx.thm.dart` only when the component has stable private tokens,
remote-configurable visual styles, or dedicated images, shadows, or state
colors. `xxx.thm.dart` is a part of `xxx.dart`; the shell owns its imports and
generated `.g.dart` declaration when serialization is required.

The global page-theme registry may register a component theme, but imports only
the component shell `xxx.dart`, never `xxx.page.dart`. Page Support may inject
an already-defined component theme around `XxxView`, but it must not define a
Theme type that `XxxView` or other component code reads. This preserves the
component library's ability to compile and be reused after `.page.dart` is
deleted.

Existing pages are not forced to migrate. The new generator policy requires a
Theme decision, not a component-private Theme implementation.

Page Support must not define Theme types. A future route-shell Theme exception
requires an explicit architecture decision and must remain inaccessible from
`xxx.dart` and its parts.

## Approval Flow

Default `gen_page` input is Figma. Existing API/OpenAPI input is a compatibility
input only; otherwise use BFF analysis. The AI inspects Figma, available shared
components, widget boundaries, models, state, Events, and route entry before
drafting the contract source pair. User review happens before derived UI/VM
implementation. No JSON spec is written or committed.

All non-contract work must use `read_contract.py` output as its decision
source. The reader supports page aggregation and standalone component mode.

## Runtime Scripts

- `resolve.py`: resolve generic and project-profile instructions only.
- `draft_contract.py`: draft shell, component contract, and optional adapter.
- `contract_core.py` / `contract_parser.py`: parse stable Dart contract facts.
- `read_contract.py`: print stable AI-readable page or component summaries.
- `generate_from_contract.py`: prepare derived part targets from approved
  source, never from a hidden JSON spec.

Use a lightweight structured parser first. Add a Dart analyzer AST bridge only
when the stable contract surface can no longer be parsed safely by the current
tokenizer and conventions.

## Project Profiles

`config.yaml` indexes base references and optional project profile references.
HSG rules remain in `skills-config`, including Chinese prose, Figma gate,
theme rules, `fr_acdd` DTO extraction, BFF JSON5 review artifacts, and HTML
contract document delegation. The profile must adapt to generic component
inputs rather than add HSG branches to generic scripts.

## Migration

1. Keep `hsg-page-contract` and `hsg-component-contract` removed.
2. Replace old single `xxx_page.dart` output with component library plus
   optional `.page.dart` adapter.
3. Move BFF artifact/service naming from page ownership to component ownership.
4. Replace JSON generator tests with draft/read/generate source-pair tests.
5. Update BFF extraction, contract HTML docs, validation, and scanners to find
   `xxx.c.dart` through its shell or `.page.dart` entry.
6. Migrate existing pages only when they are touched; no runtime compatibility
   switch is required.

## Validation

- Resolver profile fallback and deterministic `instructions_id`.
- Page parser verifies sibling import and exactly one primary View marker.
- Page validation rejects passing `XxxPageArgs` directly to `XxxView`.
- Component parser rejects imports in parts, component-owned `XxxPageArgs`,
  and references to `.page.dart`.
- Removing `.page.dart` leaves `read_contract.py --component-file` working.
- A non-page host can render `XxxView` with ordinary parameters or
  component-owned `XxxArgs` / `XxxConfig`.
- BFF, build_runner, analyzer, and project profile tests run after generation.

## Breaking Changes

- `new_page.py --spec-file` is no longer the supported workflow.
- A page is no longer one `xxx_page.dart` contract library.
- JSON spec files are not durable artifacts.
- `.page.dart` has no Provider, VM, DTO, BFF, or component UI ownership.
- `read_contract.py` reports route-owned `page_args` separately from
  `component_input`; consumers of the former component-level `page_args` field
  must migrate.

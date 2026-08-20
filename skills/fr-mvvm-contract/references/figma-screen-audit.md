# Figma Screen Responsibility Audit

Use this audit whenever a request supplies more than one Figma node. Complete
it before choosing directories, routes, Views, contracts, state ownership, or
BFF boundaries.

## Required evidence

Before calling Figma `get_design_context`, inspect lightweight structure
metadata for every supplied node. Record each supplied URL exactly once in an
evidence table:

1. If the supplied node is a concrete `FRAME`, call `get_design_context` on
   that Frame.
2. If it is a `SECTION`, page, or another container, list only its direct
   `FRAME` children first. Do not call `get_design_context` on the container.
   Select the relevant child Frames with the user or from the delivery scope,
   then call `get_design_context` only on those child Frames.
3. Prefer Figma `get_metadata` for the structure pass. If it times out or is
   unavailable for a large node, use a read-only `use_figma` call to return
   just the container type/name and each direct Frame's ID, name, and size.
   Do not retrieve screenshots, assets, generated code, or descendant details
   during this fallback.

Treat the container URL as a scope-discovery record, not a page-design
reference. Its direct Frame URLs are the candidates for classification and
implementation.

## Find a page by visible title

Treat the visible page title as the primary discovery key. Designers usually
name a Frame after its page, but an untouched or stale Frame name can be
unrelated to the screen it contains. For a requested page such as `Settings`:

1. Search visible Figma text for the exact or localized page title before
   searching Frame names.
2. For each matching text node, identify its nearest owning screen Frame and
   collect that Frame's node ID and current name.
3. Use the Frame name only to rank candidates. Never reject an otherwise valid
   screen because its Frame name differs from the page title.
4. Confirm the candidate from its visible hierarchy, navigation context,
   distinctive controls/content, dimensions, and rendered image when needed.
   A repeated title in navigation, a menu item, or an embedded card is not by
   itself proof of page ownership.
5. When no visible title exists by design, use route/product identity and
   distinguishing screen content, then record the page title as `none`.

After confirmation, preserve one association among the immutable `node-id`,
the current Frame name, and the visible page title. The node ID anchors later
reads; the Frame name preserves design-file context; the page title preserves
semantic page identity. If the Frame is later renamed, update only the Frame
name after confirming the same node and visible title.

| Node | Frame name | Page title | Distinguishing evidence | Classification | Logical owner | Navigation context |
|---|---|---|---|---|---|---|
| `1:2` | `Input Mobile` | `Settings` | settings title, account controls, and branch navigation | primary | `SettingsView` | `standalone` |

Classify every node as exactly one of:

- **primary**: the authoritative default Frame for one logical page or
  independently state-owning component;
- **state**: an authoritative full-frame state of the same route, ViewModel,
  state ownership, and backend contract as its primary;
- **reference**: a component, instance, asset, or contextual visual reference
  that is not itself implemented as an independent state owner;
- **excluded**: explicitly outside the requested delivery scope.

Do not use visual similarity or Frame count alone. Compare route/back-stack
identity, entry and exit behavior, state lifecycle, business responsibility,
API/BFF effect, overlays, content hierarchy, and interaction transitions.

Treat keyboard-open, focused, loading, validation, success, failure, resend,
and picker-open variants as states when the same ViewModel can transition
between them without a new navigation identity. Treat a dialog or bottom sheet
as an overlay state unless it has an independently addressable lifecycle.
Treat a component/instance node as a reference unless it owns independent
state or is explicitly requested as a reusable component contract.

Create a separate route/View/contract only when the node has an independent
navigation identity, state/API ownership, lifecycle, or reuse responsibility.
If evidence conflicts or remains ambiguous, stop and ask the user before
drafting contracts.

## Persistent Navigation Context

After the primary/state/reference classification, classify every primary Frame
on a second navigation axis:

- `standalone`: owns its complete route surface outside a persistent shell;
- `shell:<id>/branch-root`: one primary destination of the named shell;
- `shell:<id>/branch-child`: a detail/flow route inside one branch stack;
- `shell:<id>/root-fullscreen`: intentionally covers or replaces the shell;
- `shell:<id>/root-overlay`: a dialog or sheet that covers persistent chrome.

When two or more primary Frames use the same bottom destinations, order, and
switch semantics, inspect Figma component identity plus product/router evidence
before assigning ownership. If they are one shell, interpret each complete
Frame as `shell state + branch content`. Do not generate one outer Scaffold and
bottom navigation per Frame.

Read `navigation-shells.md`, resolve `validate_navigation_shell`, and record the
project-specific membership in the resolved profile before implementing or
repairing those Frames.

## Contract declarations

Record the exact current Frame name, visible page title, and complete
node-specific URL in `Figma:`. Declare a same-owner state with a stable name,
only its `node-id`, and evidence; resolve that ID against the primary design
file. Keep complete
URLs for references and exclusions because they are independently supplied
evidence:

```dart
/// Figma:
/// - Frame: Registration / Input Code Success
/// - Page Title: Enter verification code
/// - Node: https://www.figma.com/design/fileKey/File?node-id=1-2
/// Figma States:
/// - editing | 1-3 | focused input with keyboard
/// - invalid | 1-4 | server validation error
/// Figma References:
/// - topNav | https://www.figma.com/design/fileKey/File?node-id=1-5 | shared navigation visual reference only
/// Figma Excluded:
/// - dashboard | https://www.figma.com/design/fileKey/File?node-id=1-6 | outside this feature scope
```

Names must be unique identifiers. Every `Figma States` node belongs to the
same Figma file named by `Figma.Node`; all URL declarations must target that
file, and one node may appear in only one category. Do not repeat the primary
design URL in `Figma States`.

## Contract recording

Record the authoritative primary Frame name, visible page title, and
node-specific URL in the `.c.dart` contract. Existing two-line `Frame`/`Node`
contracts remain readable, but add `Page Title` whenever that contract is
created or otherwise modified. Also record one page-level audit disposition:

```dart
/// Figma Fidelity:
/// - Viewport: 360 x 780
/// - Asset Lock: .agents/skills-config/fr-mvvm-contract/order-figma-assets.lock.json
/// - Regression Test: orderFigmaFidelity renders approved states
```

Use `Asset Lock: none` only when no exported assets belong to the Frame. The
lock contains only export identity, repository path, and SHA-256; `.c.dart`
alone owns the node, viewport, and test assignment. Use `excluded | <reason>`
only when the current implementation is explicitly outside the approved
fidelity gate. This exclusion is page-level audit status; it is distinct from
`Figma Excluded`, which classifies individual supplied nodes. `Figma States`,
`Figma References`, and `Figma Excluded` remain contract ownership
declarations only; do not write plugin data, cards, or other contract metadata
into Figma.

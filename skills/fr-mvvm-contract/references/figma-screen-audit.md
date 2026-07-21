# Figma Screen Responsibility Audit

Use this audit whenever a request supplies more than one Figma node. Complete
it before choosing directories, routes, Views, contracts, state ownership, or
BFF boundaries.

## Required evidence

Call Figma `get_design_context` on every supplied node. When a root is too
large, inspect the relevant children. Record each supplied URL exactly once in
an evidence table:

| Node | Figma type/name | Distinguishing evidence | Classification | Logical owner |
|---|---|---|---|---|
| `1:2` | `FRAME / Input Mobile` | focused field and keyboard | state | `MobileEntryView.editing` |

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

## Contract declarations

Keep the primary URL in `Figma:`. Declare every other supplied node under one
ownership section using a stable name, node-specific URL, and evidence:

```dart
/// Figma: https://www.figma.com/design/fileKey/File?node-id=1-2
/// Figma States:
/// - editing | https://www.figma.com/design/fileKey/File?node-id=1-3 | focused input with keyboard
/// - invalid | https://www.figma.com/design/fileKey/File?node-id=1-4 | server validation error
/// Figma References:
/// - topNav | https://www.figma.com/design/fileKey/File?node-id=1-5 | shared navigation visual reference only
/// Figma Excluded:
/// - dashboard | https://www.figma.com/design/fileKey/File?node-id=1-6 | outside this feature scope
```

Names must be unique identifiers. All declarations must target the same Figma
file, and one node may appear in only one category.

## Binding consequences

Bind the contract to its primary Frame and every `Figma States` Frame. Each
authoritative Frame receives the same visible `.c.dart` yellow card and shared
plugin-data binding. Run the write and independent verification for each node.

Never bind or create a yellow card on `Figma References` or `Figma Excluded`
nodes. References may guide visual implementation but do not prove route,
state, API, or BFF ownership.

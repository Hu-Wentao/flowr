# Figma Node Contract Binding

Bind every generated page or component contract back to its primary Figma
Frame and every authoritative Frame declared under `Figma States` in two
synchronized forms:

1. Store the complete set of project-relative `.c.dart` paths as one versioned
   shared-plugin-data value for tools.
2. For every primary/state route Frame, create or update one compact yellow
   card immediately above that concrete Figma Frame for people. Show the authoritative `.c.dart`
   contract path as the entire text. Do not prepend `Contract` or any other
   label. Never aggregate several pages into one Section-level card.

Writing only shared plugin data is incomplete because users cannot see it on
the canvas.

Prepare validated inputs from the project root:

```bash
uv run python <skill-root>/scripts/prepare_figma_binding.py \
  --project-root . \
  --contract-file lib/app/order_content/order_content.c.dart \
  --contract-file lib/app/order_header/order_header.c.dart
```

The default target is the contract's primary `Figma:` Frame. Prepare every
additional authoritative state separately:

```bash
uv run python <skill-root>/scripts/prepare_figma_binding.py \
  --project-root . \
  --contract-file lib/app/order_content/order_content.c.dart \
  --target-node-id 12:35
```

The target must be the primary node or a node declared under `Figma States`.
The command rejects nodes declared under `Figma References` or `Figma
Excluded`; those nodes never receive shared data or a visible card.

The command rejects missing files, paths outside the project root, non-contract
files, malformed/duplicate ownership declarations, contracts that do not share
the selected Figma node, multiple route pages in one invocation, and any Figma
URL without a concrete `node-id`. It reads authorized targets from `.c.dart` so
a second input cannot redirect paths to an undeclared node. It emits the
authoritative `fileKey`, normalized `nodeId`, sorted `contractPaths`, detected
`pagePaths`, `figmaRole`, `visiblePathLines`, `visibleCardName`, `bindingValue`,
`writeCode`, and `verifyCode`.

Load `figma-use` before the following MCP calls. Call `use_figma` once with the
emitted `fileKey` and `writeCode`, using `skillNames: "figma-use"`. The code
writes shared plugin data, requires a route page target to be a concrete Figma
Frame, creates or updates one idempotently named compact yellow card in the
nearest Section/Page canvas, places it directly above the Frame, resolves
collisions upward, and returns a screenshot plus every created, removed, or
mutated node ID.

Then call `use_figma` a second time with the same `fileKey` and the emitted
`verifyCode`. Do not merge the calls: the second invocation independently
checks the persisted shared data, every visible contract path, and that the card
bottom remains above the target Frame top, then returns another screenshot.
Inspect that screenshot before continuing. A `verified: true` result without
the expected above-page card and screenshot is not a completed binding.

The binding schema is:

```text
namespace: flowr
key: contract_binding
value: {"version":1,"contracts":["lib/.../a.c.dart","lib/.../b.c.dart"]}
```

Always supply the complete desired contract set. Moving a contract means
writing only its new path; splitting means supplying every resulting contract;
merging means supplying only the merged contract. The script sorts and
deduplicates paths, and every write replaces the single `contract_binding`
value atomically. Never read-modify-append the current Figma value.

Writing the same binding is idempotent: replace the complete shared value and
update the deterministic visible card instead of creating duplicates. Prepare
each route page and each primary/state Frame separately so every authoritative
Frame owns its own card. Do not create
alternate keys, rename the target node, append paths to its description, or use
private plugin data. Treat a shared-data failure, non-Frame page target, missing
or below-page card, missing visible path, or failed screenshot/readback as an
incomplete module binding; do not proceed to contract review. This schema has
no legacy compatibility behavior.

Code Connect may be added separately when the target is a published Figma
component and the organization supports it. It is not the contract-path source
of truth because route frames and ordinary module nodes are not necessarily
published components.

# Figma Node Contract Binding

Bind every generated page or component contract back to its concrete Figma
node. Store the complete set of project-relative `.c.dart` paths as one
versioned shared-plugin-data value so frames, sections, components, and other
ordinary nodes use the same mechanism.

Prepare validated inputs from the project root:

```bash
uv run python <skill-root>/scripts/prepare_figma_binding.py \
  --project-root . \
  --contract-file lib/app/order_content/order_content.c.dart \
  --contract-file lib/app/order_header/order_header.c.dart
```

The command rejects missing files, paths outside the project root, non-contract
files, contracts that target different Figma nodes, and a contract's `Figma:`
URL when it lacks a concrete `node-id`. It reads URLs from `.c.dart` so a
second input cannot redirect paths to a different node. It emits the
authoritative `fileKey`, normalized `nodeId`, sorted `contractPaths`,
`bindingValue`, `writeCode`, and `verifyCode`.

Load `figma-use` before the following MCP calls. Call `use_figma` once with the
emitted `fileKey` and `writeCode`, using `skillNames: "figma-use"`. Then call it
a second time with the same `fileKey` and the emitted `verifyCode`. Do not merge
the calls: the second invocation is the persisted-state readback gate.

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

Writing the same binding is idempotent. Do not create alternate keys, rename
the node, append paths to its description, or use private plugin data. Treat a
write or readback failure as an incomplete module binding; do not proceed to
contract review. This schema has no legacy compatibility behavior.

Code Connect may be added separately when the target is a published Figma
component and the organization supports it. It is not the contract-path source
of truth because route frames and ordinary module nodes are not necessarily
published components.

# Figma Node Contract Binding

Bind every generated page or component contract back to its concrete Figma
node. Store the project-relative `.c.dart` path as shared plugin data so frames,
sections, components, and other ordinary nodes use the same mechanism.

Prepare validated inputs from the project root:

```bash
uv run python <skill-root>/scripts/prepare_figma_binding.py \
  --project-root . \
  --contract-file lib/app/order_content/order_content.c.dart
```

The command rejects missing files, paths outside the project root, non-contract
files, and the contract's `Figma:` URL when it lacks a concrete `node-id`. It
reads that URL from `.c.dart` so a second input cannot redirect the path to a
different node. It emits the authoritative `fileKey`, normalized `nodeId`,
`contractPath`, `writeCode`, and `verifyCode`.

Load `figma-use` before the following MCP calls. Call `use_figma` once with the
emitted `fileKey` and `writeCode`, using `skillNames: "figma-use"`. Then call it
a second time with the same `fileKey` and the emitted `verifyCode`. Do not merge
the calls: the second invocation is the persisted-state readback gate.

The binding schema is:

```text
namespace: flowr
key: contract_path
value: lib/.../xxx.c.dart
```

Writing the same binding is idempotent. Rebinding a node replaces only this
key. Do not rename the node, append the path to its description, or use private
plugin data. Treat a write or readback failure as an incomplete module binding;
do not proceed to contract review.

Code Connect may be added separately when the target is a published Figma
component and the organization supports it. It is not the contract-path source
of truth because route frames and ordinary module nodes are not necessarily
published components.

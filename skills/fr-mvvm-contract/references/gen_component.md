# Generic Component Contract Workflow

`gen_component` creates an independently importable feature component library.
Use `draft_contract.py --component-only`; do not create a page adapter.

The component shell owns imports and `.c/.v/.vm` parts. The contract defines
Figma/API facts, state ownership, reused components, widget tree, Event and VM
references, models, BFF/service assets, and `XxxPageArgs`. `XxxView` owns its
Provider and startup Event. Interaction is Event-driven; do not add Intent or
callback protocols.

Use `read_contract.py --component-file` before editing derived implementation.

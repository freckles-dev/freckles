# The shape of the tree

Type: grilling
Status: open
Blocked by: 01

## Question

The brief names "the base tree-like structure" as the base design concept —
but the example nodes take *multiple* inputs (a transformer takes the pixi
bootstrap outcome *and* the name/version of what to install; a flux config
node takes the cluster outcome *and* a config directory), which is a DAG in
the general case. Pin down the shape exactly.

To resolve:

- What a node *is*: parent outcome(s) + the node's own configuration + a named
  transformer? Is one input distinguished as "the environment I run in" (a
  true tree spine) with other inputs as parameters, or are all inputs equal
  (plain DAG)?
- In what exact sense "tree" remains the base concept — a tree of
  environments, with cross-references allowed? Sharpen this into a statement
  the design doc can print.
- Node identity and addressing: is a node identified by the hash of (inputs +
  transformer + config)? What is the human-readable name, and where does it
  live?
- Whether the tree is written by the user as an explicit structure, or
  assembled from declarations (the vision doc assembled a DAG from frecklet
  stage declarations — does anything of that survive?).
- Express the full rosekube chain in the chosen shape:
  pixi bootstrap → opentofu tool → infra state (Talos host) → flux install →
  flux config dir → apps. Every edge labeled with what flows along it.

Run /grilling and /domain-modeling. Grill against vision.md §4 (stage graph
assembly).

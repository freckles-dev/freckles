# The shape of the tree

Type: grilling
Status: resolved
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

## Answer

Resolved 2026-08-20 over three grilling rounds; confirmed by Markus.
Assets: [ADR 0002](../../../docs/adr/0002-consumed-claims-are-identity.md),
[rosekube chain sketch](../assets/02-rosekube-chain.yaml), glossary terms in
[CONTEXT.md](../../../CONTEXT.md).

1. The base structure is a **DAG of named nodes** — "tree" is retired
   (Markus: "I misspoke when I said tree"). Typical configurations stay
   mostly chain-shaped, but no distinguished parent edge exists.
2. A **node** binds a stable, path-like human name (`infra/staging`) to an
   operation, its configuration, and input edges. Names are the stable
   identity across config edits — day-2 diffs speak names; derivation
   hashes and claim addresses are the versioned identity beneath.
3. **Available environment**: the merged claims of all transitive
   predecessors, keyed by kind — a *resolution-time* concept only, used for
   edge inference and compatibility checks.
4. **Effective inputs** (ADR 0002): only the claims matching the operation's
   declared consumed kinds enter the provenance record and cache key — and
   at *run time* the operation receives exactly those claims, never the
   whole environment. Availability is ergonomics; consumption is identity;
   the runner enforces it.
5. Ambiguity among consumed kinds is a **hard error** resolved by explicit
   selection (`use:`). Door deliberately left open for a future *explicit*
   multi-consume declaration (aggregators — "all claims of kind X"); silent
   winners are ruled out.
6. **Edges are hybrid**: explicit edges are always allowed and always win;
   inference wires unambiguous consumed kinds automatically; ambiguity
   errors loudly. Resolved edges land in provenance, so authoring mode
   never affects identity.
7. **Everything is a node.** Sources — imports of user values, directories,
   sops files — are pure operations whose claims reference CAS content;
   roots are simply nodes with zero inputs (bootstrap, sources). The
   bootstrap root is structurally unspecial.
8. Validated by expressing the full rosekube chain in this shape (asset
   above); every edge there is inferred, and a second cluster is the worked
   example of the ambiguity error.

Routed onward: the consumption *selector* mechanism (kind + field match,
e.g. `tool(opentofu)`) and runtime-visibility enforcement → The plugin
contract; the origin of operation content (tofu module, flux tree) → Where
curation lives; full-fidelity chain documents + a day-2 delta → The
rosekube chain on paper.

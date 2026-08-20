# Where curation lives

Type: grilling
Status: claimed
Blocked by: 02

## Question

The vision doc's central concept — the curated catalog of frecklets with
opinionated defaults and curation policies — does not appear in the new brief
at all. Per the charter, absence is not conflict: this ticket decides its
place.

To resolve:

- Does the catalog/frecklet concept survive into the node-tree model, and in
  what form? Candidate shapes: a library of parameterized node templates
  (subtrees) the user instantiates; layered configuration defaults; something
  else.
- If it survives: how catalog-supplied structure and user-supplied
  configuration combine into one tree, and how catalog layering (official +
  personal override) works in the new model.
- If deferred: is the design doc's model expressive enough that curation can
  be added later without reshaping it? Name the extension point explicitly,
  and move catalog design to the map's out-of-scope or a follow-up effort.
- Either way: rosekube-as-first-catalog was the vision doc's validation
  strategy — what validates the design doc instead (presumably The rosekube
  chain on paper)?

Routed here by The shape of the tree (resolved): in the chain sketch
(assets/02-rosekube-chain.yaml), `infra/staging` names a tofu **module**
(`talos-proxmox`) and `sources/flux-tree` renders catalog **content** —
where does that curated content come from and how is it pinned/addressed?
This is the concrete form of the curation question in the DAG model.

Also routed from The plugin contract (resolved): the **kind vocabulary**
and the **per-kind claim field conventions** (that `tool` claims carry
`tool`/`version`/`platform` — everything selectors and consumers rely on)
are curation policy — decide where they live and how they're governed.

Run /grilling and /domain-modeling. Grill against vision.md §2–3, §8, open
question 2.

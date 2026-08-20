# Where curation lives

Type: grilling
Status: open
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

Run /grilling and /domain-modeling. Grill against vision.md §2–3, §8, open
question 2.

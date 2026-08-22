# Where curation lives

Type: grilling
Status: resolved
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

## Answer

Resolved 2026-08-20 in one grilling round; all four points explicitly
adopted by Markus.

1. **Curation is deferred, with precise extension points.** The design doc
   specifies the core (explicit DAG) as complete and standalone, names
   exactly where curation plugs in (points 2–4 below), and carries a short
   *non-normative* "curation direction" section. **Full catalog design —
   layering semantics, the frecklet/template format, policy composition —
   is its own follow-up effort**, naturally paired with rosekube
   migration, and is now out of scope on this map. This completes the bet
   The shape of the tree made when it left curation as the
   generator-of-explicit-config extension point, and it follows the
   vision doc's own validation principle: template semantics get
   specified against a real catalog, not before one exists.
2. **Catalog content arrives as claims**: standard plugin `import-git` — a
   source-style pure operation producing `kind: file-tree` claims from a
   git repo at a configured ref, with the resolved commit in the claim.
   Content pinning is ordinary claim mechanics (the vision doc's
   "catalogs are git repos pinned via lockfile" survives as git-imported
   claims pinned via the resolution document). The standard plugin set
   grows by `import-git`.
3. **Conventions governance**: freckles core reserves and documents only
   the kinds its built-ins and standard plugins need (`bootstrap`, `tool`,
   `plugin`, `file-tree`, `config`, `secrets`; final list in the design
   doc). All domain kinds (`talos-cluster`, …) and per-kind field
   conventions live in a **conventions document that is itself catalog
   content** — imported, versioned, pinned, governed with the catalog.
   The core stays domain-agnostic.
4. **The sketch's endorsed direction**: **expansion** — templates
   ("frecklets") expand into ordinary explicit nodes at
   authoring/resolution time, so the resolution document always holds the
   expanded, inspectable, diffable DAG and the core never learns about
   templates. Dynamic DAGs (nodes producing nodes) are explicitly
   rejected as the complexity cliff. External generation (copier
   rendering a freckles config) is named as the zero-cost interim that
   works today.

Validation split: The rosekube chain on paper validates the design doc;
the first real catalog release validates the follow-up effort.

Run /grilling and /domain-modeling. Grill against vision.md §2–3, §8, open
question 2.

## Amendment (2026-08-22)

`import-git` moves **standard → built-in** (Markus, design-doc review):
it must be usable before any plugin can be acquired, so a configuration
can bootstrap from a bare git repository — one that may itself carry a
bootstrap binary. Consequence recorded in design.md §6: the git fetch
ships inside freckles itself (a host `git` dependency would defeat the
tier; pinned-commit fetch needs no full libgit2 — pure-Python
implementations cover it). Point 2 above and The plugin contract's
built-in list are amended accordingly.

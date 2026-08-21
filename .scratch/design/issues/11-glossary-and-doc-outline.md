# Glossary and doc outline

Type: grilling
Status: resolved
Blocked by: 05, 07, 08, 09, 10

## Question

The last decision before the design doc is written: settle the ubiquitous
language and the doc's structure.

To resolve:

- Names, finally: the brief itself flags "transformer" vs "tasks" — "we'll
  have to settle on how to call things". Fix the term for: the operation
  plugin, a node, an outcome, the environment a node provides, the store,
  the bootstrap root, the user's configuration. Prefer terms that survived
  the ticket discussions; retire vision-doc terms that didn't (stage?
  frecklet? artifact? journal?).
- One-line definitions for each term — the design doc's glossary section,
  agreed before writing.
- The design doc's outline: section order, what the worked example (The
  rosekube chain on paper) anchors, what is stated as superseding vision.md,
  and what the doc explicitly defers (pointers into the map's out-of-scope
  and remaining fog).

Naming inputs accumulated by later tickets:

- Secrets in the outcome model (09): *secret value* / *secret reference* /
  *credential* already in CONTEXT.md — confirm final wording.
- The rosekube chain on paper (10): node-path conventions (`render/` for
  non-roots — `sources/` misleads); *terminal node* (in CONTEXT.md); the
  kind-namespacing convention (flat = official vocabulary, non-core
  publishers advised to prefix) needs its design-doc wording.

Run /grilling and /domain-modeling — this ticket *is* the domain-model
consolidation. When it closes, the map's way is clear: write docs/design.md.

## Answer

Resolved 2026-08-21 in one grilling round; all seven points adopted by
Markus. Asset: the graduated glossary in [CONTEXT.md](../../../CONTEXT.md).

1. **The unit of work is the operation** — final. Nine tickets used it
   without reaching for the alternatives; transformer (implies pure), task
   (imperative, CI-collides), and stage (died with the pipeline) stay on
   the avoid list. Provisional marker dropped.
2. **The config collision resolved three ways**: *configuration* = the
   user's whole declaration only; *node config* = a node's operation
   parameters; the imported-values claim kind renames `config` →
   **`values`** (so `import-values` produces kind `values`, and
   `use: { values: sources/values/cluster }`). The ticket-10 prototype
   predates the rename and keeps `kind: config`; the design doc's recast
   applies it.
3. **Retired**: stage, pipeline, render/execute stages, artifact, journal,
   lockfile, frecklet (curation-effort vocabulary). Surviving vision
   terms: checkpoint, catalog (as the named deferral), sops/age as tech.
4. **No term for the bootstrap root** — kind `bootstrap`, the bootstrap-*
   plugins, and fetch-verify already name everything; "bootstrap node" is
   plain prose.
5. **CONTEXT.md graduates as the design doc's glossary** — single source;
   the doc's glossary section mirrors it rather than forking it.
6. **The doc outline**, adopted as proposed — docs/design.md in twelve
   sections: (1) Motivation & what this supersedes (consolidated
   supersession list; vision.md gets a banner pointing here), (2) The
   model at a glance (five-node mini-example), (3) Glossary, (4) Outcomes
   (ADR 0001), (5) The DAG (ADR 0002; granularity principle; terminal
   nodes; aggregator door named shut), (6) Operations and plugins
   (ADR 0004; wire document as illustrative asset), (7) Storage
   (ADR 0003), (8) Effects and day-2, (9) Secrets (ADR 0005), (10) The
   rosekube chain, worked (the prototype recast, referenced forward from
   4–9), (11) Bootstrap, (12) Deferred. Worked example lives whole as its
   own section rather than diced into the model sections.
7. **The Deferred section** contains exactly the map's out-of-scope plus
   remaining fog: curation/catalog design with its named extension
   points, multi-machine sharing (incl. team keys, provider auth, the
   IPFS backend's purpose), the formal spec set, and implementation.
   Nothing else is silently deferred.

The map's way is clear: nothing left to decide before writing
docs/design.md — the handoff named in the map's Notes.

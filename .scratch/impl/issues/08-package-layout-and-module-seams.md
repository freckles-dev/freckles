# Package layout and module seams

Type: grilling
Status: open
Blocked by: 02

## Question

The module map for v1 — run /codebase-design with /grilling and
/domain-modeling. Candidate seams:

- **store** — backends behind `put/get/has/cids` + refs + gc.
- **documents** — claims, envelopes, canonical encoding, CIDs.
- **resolver** — DAG assembly, edge inference, the resolution document.
- **runner** — workspace materialization, process protocol, the secrets
  boundary.
- **heal** — the topological walk, derivation index, checkpoint set.
- **plugins** — built-ins.
- **cli**.

Decide: public API vs internal; which seams the Walking skeleton must
instantiate; where the deep-module boundaries sit so tests bite the
interfaces, not the internals. Record as a short layout doc asset.

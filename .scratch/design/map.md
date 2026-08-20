# Wayfinder map: the freckles design

Label: wayfinder:map
Tracker: local-markdown (`.scratch/design/`, tickets under `issues/`)

## Destination

A single, exact design document — `docs/design.md` — for freckles' declarative
node-tree model: outcome-hashed operations, pluggable content-addressable
storage, userspace-first bootstrap chains. It supersedes
[the vision doc](../../docs/vision.md) wherever the new model diverges, and is
precise enough to seed the formal spec and a first implementation.

## Notes

- Domain: declarative infrastructure / reproducible devops (Nix-adjacent, but
  deliberately not Nix). Rosekube (`~/projects/self-hosted/rosekube`) is the
  narrowly-scoped prototype and reference chain — instructive, not gospel.
- Every HITL ticket runs the `/grilling` and `/domain-modeling` skills.
- Charter facts (user-confirmed 2026-08-20):
  - The destination is **one** exact design doc; the multi-document formal
    spec set is a later, separate effort.
  - The new brief (outcome hashing, tree base structure, pluggable CAS,
    bootstrap chain) **supersedes** the vision doc on conflict. Absence of a
    concept in the brief (e.g. catalogs) is *not* conflict — those stay open.
- Standing design values: elegance and limited complexity; the tree-like
  structure as the base design concept; root/sudo supported but rarely
  required (userspace-first); outputs describe the environment and its
  capabilities.
- Markus reacts best to concrete worked examples (the rosekube chain:
  pixi → opentofu → Talos infra → Flux → apps).
- Writing `docs/design.md` is the handoff once the map is complete — it is not
  itself a map ticket.

## Decisions so far

<!-- one line per closed ticket: gist + link -->

- [Bootstrap tool evaluation](issues/03-bootstrap-tool-evaluation.md) — mise
  covers all 8 devops tools via upstream binaries and is recommended default;
  pixi peer for solved stacks; bootstrap is swappable behind a common
  contract, rooted in a tiny fetch+verify primitive.
- [Content-addressable store survey](issues/04-content-addressable-store-survey.md)
  — CIDv1 + sha2-256 + spec-strict DAG-CBOR gives free IPFS address
  compatibility for documents (not file trees); minimal backend =
  put/get/has/cids + refs-as-GC-roots; sqlite comfortable as default.
- [What is an outcome?](issues/01-what-is-an-outcome.md) — a present-tense
  description of what now exists: hashed claim (extensional address,
  ADR 0001) + unhashed annotations in one uniform envelope; success-only;
  DAG-CBOR value model; mandatory kind; trust = act without re-checking the
  world; claims travel, annotations don't, realization bridges.

## Not yet specified

- Day-2 UX — diffing outcomes, selective re-run, guarding destructive changes.
- Multi-machine sharing — whether/how stores sync between machines; what the
  IPFS backend is actually *for* (publication? distribution? backup?).
- Rosekube migration path — how the existing Copier template and generated
  repos map onto the first freckles configuration; likely the next effort
  after the design doc.

## Out of scope

- Implementing freckles itself — this effort ends at the design doc.
- Executing a rosekube migration — only sketched enough to validate the design.
- The multi-document formal spec set (vision.md §13) — follows the design doc
  as its own effort.

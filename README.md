# freckles

Minimum-configuration, reproducible devops: freckles turns minimal
declarative configuration into running infrastructure and IT state
through a DAG of named, hashed, content-addressed operations.

The user owns one configuration — a git working copy holding a DAG of
named nodes plus the values and secret files beside it. Each node binds
a stable, path-like name to an operation; running a node produces an
outcome: a hashed, machine-independent claim describing what now
exists, plus machine-local annotations recording where it is realized.
Claims live in a per-user content-addressed store; effectful nodes only
ever run as explicit checkpoints. Day-2 is one loop: edit the
configuration, re-resolve, heal — stale pure nodes re-derive
automatically, and the checkpoint set is confirmed per node.

Status: **design complete, implementation charted** — nothing runs yet.
Implementation planning is underway as a wayfinder map under
`.scratch/impl/`.

## Documents

- [Design](docs/design.md) — the current model, precise enough to seed
  the formal specification and a first implementation. Read this first.
- [Vision](docs/vision.md) — motivation, curation philosophy, and the
  reproducibility stance; superseded by the design doc where the two
  diverge (design.md §1 lists the divergences).
- [CONTEXT.md](CONTEXT.md) — the canonical glossary.
- [ADRs](docs/adr/) — the five decisions that were genuine trade-offs.

## Lineage

freckles generalizes patterns proven in [rosekube](../rosekube/), a
Copier template that renders a single Talos/Kubernetes cluster
repository (OpenTofu + Talos + Flux + sops/age). Rosekube is planned to
become the first freckles catalog.

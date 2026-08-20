# freckles

A Python framework for minimum-configuration, reproducible devops.

freckles turns a small user configuration plus a curated catalog of
infrastructure units ("frecklets") into fully rendered, content-addressed
deployment artifacts, and executes them through explicit, journaled pipeline
stages.

Status: design phase. Nothing here runs yet.

## Documents

- [Vision](docs/vision.md) — the full description of what freckles is, its
  concepts, and how it works. Read this first.
- `docs/spec/` — the formal specification (not started; the vision doc ends
  with the roadmap for it).

## Lineage

freckles generalizes patterns proven in
[rosekube](../rosekube/), a Copier template that renders a single
Talos/Kubernetes cluster repository (OpenTofu + Talos + Flux + sops/age).
Rosekube is planned to become the first freckles catalog.

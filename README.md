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

Status: **v1 landing** — the loop (resolve → run → heal) runs end to
end through the real CLI: checkpoints, sops secrets at the boundary,
drift and verify, plugin acquisition through the DAG, and both
bootstrap routes behind the swappable contract.

## Install

The canonical install is the released binary: one pinned URL plus its
checksum is a complete install (no installer, no registry in between).
From the [latest release](https://github.com/freckles-dev/freckles/releases):

```sh
curl -LO https://github.com/freckles-dev/freckles/releases/download/<version>/freckles-<version>-linux-x86_64
curl -LO https://github.com/freckles-dev/freckles/releases/download/<version>/SHA256SUMS
sha256sum --check --ignore-missing SHA256SUMS
chmod +x freckles-<version>-linux-x86_64
```

Binaries ship for linux x86_64 and aarch64 and bundle the SSH transport
for `import-git`. Riding along:

- **PyPI**: `uv tool install freckles` (add `freckles[ssh]` for SSH
  remotes — optional there, unlike in the binary).
- **conda**: the [`freckles` channel](https://anaconda.org/freckles) on
  anaconda.org.

Each release also carries the standard-plugin payloads
(`bootstrap-mise-<version>`, `bootstrap-pixi-<version>`,
`mise-install-<version>`, `pixi-install-<version>`) in the same
`SHA256SUMS` — configurations acquire them through `fetch-verify` at
exactly such pinned URLs.

## Documents

- [Design](docs/design.md) — the current model, precise enough to seed
  the formal specification and a first implementation. Read this first.
- [Vision](docs/vision.md) — motivation, curation philosophy, and the
  reproducibility stance; superseded by the design doc where the two
  diverge (design.md §1 lists the divergences).
- [CONTEXT.md](CONTEXT.md) — the canonical glossary.
- [ADRs](docs/adr/) — the six decisions that were genuine trade-offs.

## Lineage

freckles generalizes patterns proven in [rosekube](../rosekube/), a
Copier template that renders a single Talos/Kubernetes cluster
repository (OpenTofu + Talos + Flux + sops/age). Rosekube is planned to
become the first freckles catalog.

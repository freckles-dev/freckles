# Bootstrap tool evaluation

Type: research
Status: open

## Question

The chain's root is a bootstrap tool that provisions everything else in
userspace. The brief suggests pixi + conda environments but is explicitly
open to suggestions. Evaluate the candidates against primary sources.

Candidates: pixi (conda-forge), mise, uv (for python-only roots), plain
pinned-binary downloads (what the vision doc's "tool store" assumed).

For each, establish from primary documentation:

- Userspace story: install and operation with zero root, on any Linux distro;
  self-contained bootstrap of the tool itself (single static binary? curl
  script? version-pinnable install?).
- Exact pinning: lockfile format, whether a given lockfile reproduces
  bit-identical environments, how the tool's *own* version is pinned.
- Coverage of the devops toolchain on the respective ecosystem: opentofu,
  talosctl, flux, sops, age, kubectl, helm, copier — which are available at
  current versions (conda-forge for pixi; mise registry/backends for mise;
  n/a for uv beyond python tools)?
- Programmatic invocation: driving the tool from Python (CLI stability, JSON
  output, exit codes), creating/using environments non-interactively.
- Reproducibility characteristics and caveats (post-link scripts, platform
  variance, network requirements at env-creation time).

Deliverable: a comparison with a recommendation for the default bootstrap
transformer, and whether the design should treat the bootstrap tool as
swappable (one transformer among several) or as a privileged root concept.

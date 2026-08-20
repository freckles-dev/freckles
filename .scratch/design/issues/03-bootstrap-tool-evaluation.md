# Bootstrap tool evaluation

Type: research
Status: resolved
Findings: branch `research/bootstrap-tools`, file `docs/research/bootstrap-tools.md` (resolved 2026-08-20; read via `git show research/bootstrap-tools:docs/research/bootstrap-tools.md`)

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

## Answer

Full findings: `docs/research/bootstrap-tools.md` on branch
`research/bootstrap-tools` (282 lines, all claims cited to primary sources,
verified 2026-08-20; unverifiable facts flagged in its final section).

- **Coverage of the devops 8 (opentofu, talosctl, flux, sops, age, kubectl,
  helm, copier):** mise covers all 8 — seven via its aqua backend (upstream
  official binaries, mandatory checksums, cosign/SLSA verification, current
  versions), copier via pipx. pixi/conda-forge also covers all 8, but as
  source-rebuilt packages with version skew (kubectl 1.34.3 vs upstream
  1.36.4). uv covers only Python tools (copier). Plain pinned downloads
  cover 7/8 (copier ships no binary; age ships no plain checksums).
- **Pinning:** pixi.lock is the strongest lockfile (full graph, sha256+md5,
  multi-platform, channel URLs); mise.lock records per-platform
  checksum+size+URL for aqua tools but version-only for pipx; uv.lock is
  universal with per-artifact sha256.
- **Bootstrap of the bootstrapper:** all three are single userspace binaries,
  installable to $HOME with their own version pinned at install time
  (PIXI_VERSION / MISE_VERSION / versioned uv URL); all drivable
  non-interactively with JSON output.
- **Recommendation (a):** mise as the default bootstrap transformer (aqua
  backend, explicit pins, locked mode); pixi as the peer transformer where a
  solved library/Python stack is needed; uv as the Python-slice engine.
- **Recommendation (b):** the bootstrap tool should be **swappable** — one
  transformer among several behind a common contract. The only privileged
  root concept is a tiny "fetch pinned URL + verify checksum" primitive,
  which installs whichever bootstrap transformer a chain declares.

The *decision* on the default (mise vs the brief's pixi suggestion) is made
by Markus when a design ticket consumes this — likely The plugin contract or
the design doc itself.

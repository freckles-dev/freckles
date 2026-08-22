# The v1 cut

Type: grilling
Status: resolved

## Question

design-v1 (the surface design.md names) is the **ceiling**; decide the
actual v1 release cut. Candidates to trim or keep:

- ipfs backend (design.md: freckles never requires IPFS) and the folder
  backend — one backend or three?
- `bootstrap-pixi` — first-class *contract peer* need not mean *ships in
  the first release*.
- Standard plugins `uv-python`, `copier`.
- Drift: the `verify` entrypoint and `freckles verify` in v1 or later.
- GC in v1 or later.
- Auto-confirm opt-in for automation.
- The detached secret variant (`store: false`).
- SDK sugar for plugin authors (conditional on the language outcome —
  name it conditionally if needed).

Hard constraint: the acceptance chain (map Notes) must remain
expressible by whatever survives — bootstrap-mise, mise-install,
import-values, import-sops, `command`, checkpoints, `prior:`, secrets
at the boundary, staleness/heal are untrimmable.

The cut becomes the v1 definition Milestones to v1 builds toward.

Run /grilling and /domain-modeling.

## Answer

Resolved 2026-08-22 over two grilling rounds; every point explicitly
adopted by Markus. The cut is *wider* than recommended — pixi, copier,
GC, and the SDK all stayed in.

**In v1:**

1. **Backends: sqlite (default) + folder.** The folder backend is the
   debugging window and keeps the backend seam honest with a second
   implementation. ipfs deferred to the multi-machine effort — IPFS
   *compatibility* is already guaranteed by golden CIDs without it.
2. **All six built-ins** (`import-values`, `import-file-tree`,
   `import-sops`, `import-git`, `fetch-verify`, `command`);
   import-file-tree and import-git land as a late milestone, not in the
   skeleton.
3. **Standard plugins: bootstrap-mise (default), bootstrap-pixi,
   mise-install, `pixi-install` (new), copier.** The peer bootstrap
   ships in v1, not just its contract. `pixi-install` is a design
   amendment this ticket exposed: bootstrap-pixi without an install
   analog delivers no tools (design.md §6 amended; recorded on The
   plugin contract). **uv-python deferred.**
4. **Secrets**: value-bearing sops claims, CAS-resident *and* the
   detached (`store: false`) variant. The reference-bearing shape is
   expressible in the normative schemas (it is "specified now" per the
   design) and the runner fails cleanly on it — the secretspec-backed
   resolver stays future by design; pulling it in would exceed the
   ceiling.
5. **Drift** (charter-bound: the acceptance chain exercises it):
   distrust mechanics plus a minimal `verify` entrypoint and
   `freckles verify`.
6. **GC** — post-skeleton milestone; a store whose day-2 loop mints
   GC-fodder should be able to shrink.
7. **Auto-confirm opt-in** — Testing strategy needs it for
   non-interactive acceptance runs.
8. **A public Python SDK, dogfooded from day one**: all five standard
   plugins are written against it, so it has five real users before any
   third party. The process protocol remains the *only* contract
   (ADR 0004 intact) — a plugin written without the SDK stays fully
   possible.

**Acceptance bar amended** (map Notes updated): the mechanics-complete
chain as charted, **plus copier provably installable through both
bootstrap routes** — bootstrap-mise → mise-install → tool(copier)
(pipx backend; version-only locking accepted for v1, per the Bootstrap
tool evaluation) and bootstrap-pixi → pixi-install → tool(copier)
(conda-forge, sha256-locked). The swappable-bootstrap contract is
thereby tested, not asserted.

**Deferred past v1**: ipfs backend, uv-python, the secretspec resolver
plugin. Consequence routed onward: v1's standard plugins must be
published at pinned URLs so fetch-verify can acquire them — lands in
Packaging and distribution / Milestones to v1.

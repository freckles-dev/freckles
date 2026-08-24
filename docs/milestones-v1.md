# Milestones to v1

Status: current (2026-08-24). The handoff from the
[implementation wayfinder map](../.scratch/impl/map.md) (ticket
"Milestones to v1") — the ordered build plan from the walking skeleton to
the v1 release. The ceiling is [design.md](design.md); the scope is The
v1 cut; the surface is the ratified CLI transcript; the doctrine comes
from Testing strategy. Building proceeds outside wayfinder: one GitHub
issue per milestone, claimed and closed there.

## Doctrine

- **/tdd drives every milestone** (red–green–refactor; the walking
  skeleton was the last test-along work).
- The **undivided test suite** stays green on `develop` at all times;
  each milestone lands independently.
- Seam-first tests with real collaborators; documents minted in tests go
  through the dual-encoder cross-check; golden fixtures are normative.
- The acceptance bar is **not** re-litigated here: the
  mechanics-complete synthetic chain — bootstrap → install →
  import-values/import-sops → pure render → effectful `command` —
  exercising checkpoints, `prior:`, secret resolution at the boundary,
  staleness/heal, drift, **plus copier installable through both
  bootstrap routes**.

## The milestones

| # | Issue | Milestone | Gist |
|---|-------|-----------|------|
| 1 | [#1](https://github.com/freckles-dev/freckles/issues/1) | The CLI on the skeleton | The ratified verbs, 0/1/2 exit codes, checkpoint prompt, `--yes`; retires the dev commands |
| 2 | [#2](https://github.com/freckles-dev/freckles/issues/2) | The secrets boundary | import-sops, age key, in-memory `resolved:`, purity gate, detached variant, canary test |
| 3 | [#3](https://github.com/freckles-dev/freckles/issues/3) | Persistence completion | Folder backend into the contract suite, gc + verb, audit log (JSON-lines, field list final) |
| 4 | [#4](https://github.com/freckles-dev/freckles/issues/4) | Drift | Distrust marks, `verify` entrypoint, `freckles verify` |
| 5 | [#5](https://github.com/freckles-dev/freckles/issues/5) | Plugin mechanics + SDK | Ingestion decision first (design amendment), plugin claims via the DAG, fetch-verify, `freckles.sdk` |
| 6 | [#6](https://github.com/freckles-dev/freckles/issues/6) | The mise route | bootstrap-mise, mise-install, tool claims → PATH, copier via pipx |
| 7 | [#7](https://github.com/freckles-dev/freckles/issues/7) | The pixi leg | bootstrap-pixi, pixi-install, copier via conda-forge — the swappable contract tested |
| 8 | [#8](https://github.com/freckles-dev/freckles/issues/8) | Late imports | import-file-tree, import-git (dulwich; SSH vendor decided here) |
| 9 | [#9](https://github.com/freckles-dev/freckles/issues/9) | Release | Onefile matrix + SHA256SUMS, plugins at pinned URLs, the acceptance workflow, first tag |

**Ordering logic**: the CLI first so every later milestone demos and
tests through the real surface; secrets second (the acceptance bar's
heart); 3 and 4 are small, independent, and parallelizable; 5 must
precede 6–7 (the standard plugins are written against the SDK, and
copier's file-trees need ingestion settled); 8 is genuinely late
(nothing depends on it); 9 is the exit.

## The acceptance gate

The acceptance bar becomes an executable **acceptance workflow**:
network-bound (downloads mise, pixi, copier), so it runs on **manual
dispatch and mandatorily on version tags** — never on every push. The
per-push suite stays fast and hermetic; this is an additional workflow,
not a marker split. The M9 release job requires it green.

## Named design acts inside milestones

- **M5 opens with the plugin-content-ingestion decision** (skeleton
  finding): spawned plugins have no channel to land produced blobs in
  the CAS. Amends design.md §6 and `conformance/wire.cddl`; leading
  candidate: runner-side ingestion of a declared workspace output
  directory, generalizing the `command` builtin's `out/` convention.
- **M3 finalizes the audit-record field list** (Stack and libraries left
  it open).
- **M8 decides the dulwich SSH vendor** (host `ssh` vs paramiko extra).

## Out of v1 (recorded, not silently dropped)

- **Plugin runtime limits** (timeouts, resource caps): no design
  semantics exist; post-v1 backlog.
- **Parallel node execution**: sequential v1 stands. Contingency
  trigger, verbatim from the map: revisit **if the acceptance chain
  drags**.
- Inherited deferrals stand: ipfs backend, uv-python, the secretspec
  resolver, multi-machine sharing, catalogs (their own efforts).

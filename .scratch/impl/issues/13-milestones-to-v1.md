# Milestones to v1

Type: grilling
Status: resolved
Blocked by: 04, 06, 09, 10, 12

## Question

The handoff — the map's terminal decision. Order the post-skeleton
build toward the acceptance bar: the mechanics-complete synthetic chain
running on The v1 cut's surface with the CLI surface v1.

Slice into milestones, each independently landable; candidates:

- The secrets boundary: `import-sops`, age key handling, the checkpoint
  prompt naming plaintext secrets.
- Real bootstrap: `bootstrap-mise` + `mise-install`; the pixi leg
  (`bootstrap-pixi` + `pixi-install`) and copier via both routes (the
  amended acceptance clause).
- Remaining built-ins (`import-file-tree`, `import-git`,
  `fetch-verify`).
- Additional backends, drift/verify, GC — per the cut.
- The CLI per its prototype; packaging/release per its decision.

Deliverable: the milestone plan as a committed doc — when this ticket
closes, the map is complete and building proceeds outside wayfinder,
with /tdd (or as Testing strategy decided) driving the milestones.

Run /grilling and /domain-modeling.

## Answer

Resolved 2026-08-24 in one grilling round; all six points ratified by
Markus. Deliverable: **[the milestone plan](../../../docs/milestones-v1.md)**,
committed, with one GitHub issue per milestone
([#1–#9](https://github.com/freckles-dev/freckles/issues)).

1. **The source-rerun amendment is ratified** — design.md §8 amended
   this session (source nodes are exempt from hit-means-current; the
   walk re-runs them unconditionally).
2. **Nine milestones, adopted as proposed**: CLI on the skeleton →
   secrets boundary → persistence completion (folder/gc/audit) → drift
   → plugin mechanics + SDK → the mise route → the pixi leg → late
   imports → release. Ordering: CLI first so everything after demos
   through the real surface; SDK before the plugins written against it;
   release is the exit.
3. **Plugin-content-ingestion is M5's first act** — a bounded design
   pass amending design.md §6 + wire.cddl, generalizing the `command`
   builtin's `out/` convention; the map does not stay open for it.
4. **The acceptance bar becomes a separate acceptance workflow** —
   manual dispatch + mandatory on version tags; the per-push suite
   stays hermetic; M9's release job requires it green.
5. **Plan at docs/milestones-v1.md, tracked as GitHub issues** — the
   post-map build keeps the claim/close discipline on the repo's own
   tracker, /tdd driving.
6. **All remaining fog dispatched**: plugin-author ergonomics and
   plugin content ingestion graduate into M5; plugin runtime limits and
   parallel execution are out of v1, recorded in the plan with the
   parallel-execution contingency trigger ("if the acceptance chain
   drags") verbatim.

**With this resolution the map is complete**: architecture locked, the
walking skeleton runs, and building proceeds outside wayfinder.

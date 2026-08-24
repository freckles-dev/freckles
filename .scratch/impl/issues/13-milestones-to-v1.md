# Milestones to v1

Type: grilling
Status: claimed (markus, 2026-08-24)
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

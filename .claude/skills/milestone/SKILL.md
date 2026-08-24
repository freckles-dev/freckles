---
name: milestone
description: Drive one freckles v1 milestone (GitHub issues #1–#9) from claim to close. Use when the user says to open, continue, or resume a milestone, or asks what is next on the road to v1.
---

# Driving a v1 milestone

The loop that landed M1 and M2. One GitHub issue per milestone; work lands
on `develop`; the undivided suite stays green throughout.

## Steps

1. **Claim.** `gh issue view <N>` for scope, then
   `gh issue edit <N> --add-assignee "@me"`. Done when the issue is assigned.

2. **Context.** Read, in order: the issue body; the milestone's row and the
   "Named design acts" section of `docs/milestones-v1.md` (some milestones
   *open* with a design decision — that decision comes before any code);
   `CONTEXT.md` (the canonical vocabulary — its retired terms never appear
   in code or tests); the `docs/design.md` sections and ADRs the issue
   names; `.scratch/impl/assets/10-testing-strategy.md`; the ratified asset
   for the surface if one exists (e.g. `06-cli-surface/transcript.md` —
   decisions binding, literal output illustrative). Done when you can state
   the milestone's binding constraints and its open decisions without
   reopening the documents.

3. **Seams.** Invoke the `tdd` skill. Before the first test, put to the
   user: the seams you will test at, and every genuinely unpinned
   mechanism (a library the stack ticket never named, new node-config
   surface, a wire-visible shape). Done when the user has ratified them.

4. **Slices.** Vertical tracer bullets: one red test at a ratified seam →
   the minimal green → commit. Tests use real collaborators (tmpdir sqlite
   store, real runner, CliRunner for the CLI) and stay hermetic — no host
   binaries. A slice that changes a store/wire document shape or a golden
   fixture invokes the `conformance` skill first. A test that only pins
   behavior an earlier slice already implemented is still worth keeping
   when it fixes a binding decision.

5. **Gates.** `just tests`, `just typecheck`, `just lint` — all clean.

6. **Land.** Push `develop`; close the issue with a summary naming what
   landed, the named cuts taken, and the test count. Done when the issue
   is closed and the push is confirmed.

## Tripwires

- A design amendment (the design is the ceiling — amendments may trim,
  never exceed) lands as a dated note in the amended `design.md` section,
  written in `CONTEXT.md` vocabulary; a new term goes into `CONTEXT.md`
  itself.
- Finished milestones read well as precedent: `git log` around the M1/M2
  ranges shows the slice granularity and commit wording that passed review.

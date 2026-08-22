# README refresh

Type: task
Status: resolved

## Question

README.md still speaks retired vocabulary ("frecklets", "journaled
pipeline stages") and points at `docs/spec/` (not started) but not at
design.md — found stale during the 2026-08-22 design review.

Refresh it: gist of the current model (DAG of named nodes, outcomes,
content-addressed store), design.md as the current reference with
vision.md for motivation, an honest status line (design complete,
implementation charted), lineage note kept. Done when the README uses
only CONTEXT.md vocabulary.

## Answer

Resolved 2026-08-22. README rewritten from design.md §1–2:

- Model gist in CONTEXT.md vocabulary only — DAG of named nodes,
  operation, outcome = claim + annotations, store, checkpoints, the
  day-2 loop with the checkpoint set.
- Document index now leads with design.md; vision.md kept for
  motivation, marked superseded-on-divergence; CONTEXT.md and the ADRs
  listed. The dangling `docs/spec/` pointer removed (the spec set is a
  deferred separate effort).
- Status line: design complete, implementation charted (pointer to the
  `.scratch/impl/` map).
- One deliberate extra: the "A Python framework" claim was **dropped**,
  not restated — the implementation language is an open decision
  (Implementation language ticket), and the README should not prejudge
  it.
- Lineage section kept unchanged.

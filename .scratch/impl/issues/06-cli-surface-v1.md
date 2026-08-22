# CLI surface v1

Type: prototype
Status: resolved

## Question

Design the v1 CLI as a **mock terminal transcript** to react to (Markus
reacts best to concrete artifacts):

- Verbs: resolve, status, heal/run, the checkpoint confirmation flow,
  verify, gc, store inspection — which exist in v1 and what they print.
- How the checkpoint set is presented (day2.md's prompt — node,
  superseded claim, plaintext secret names, privilege — is the starting
  point).
- Name-first output everywhere (day-2 speaks names, never bare CIDs).
- The ambiguity hard error and its `use:` suggestion.
- Exit codes and non-interactive/auto-confirm behavior for automation.

Asset: the transcript file. React HITL; the agreed surface feeds
Milestones to v1 and (post-map) the CLI build.

Run /grilling and /domain-modeling alongside /prototype.

## Answer

Resolved 2026-08-22. Prototype at
[assets/06-cli-surface/](../assets/06-cli-surface/) (nine-scene mock
transcript over the skeleton chain); **all eight reaction points
ratified as embodied** by Markus:

1. **R1 — `heal` is the verb**: no install/apply/up; day-1 is day-2
   from zero.
2. **R2 — `status` heals stale pure nodes while walking** (safe by
   design; the only way to name the checkpoint set exactly);
   `--frozen` for look-don't-touch.
3. **R3 — checkpoint prompt** = day2.md's format: node, plugin, effect,
   superseded claim, plaintext secret names, `prior` availability,
   privilege line when present.
4. **R4 — name-first output**, CIDs abbreviated behind names; full
   documents via `show` / `store cat`.
5. **R5 — ambiguity hard error prints a ready-to-paste `use:` fix.**
6. **R6 — exit codes**: 0 success/current · 1 error · 2 not-current;
   `status --check` is the silent CI question.
7. **R7 — inspection is exactly `show <node>` (redacted human view) and
   `store cat <cid>` (raw DAG-JSON)**; the folder backend is the deeper
   browse story.
8. **R8 — verb inventory final for v1**: `heal`, `status`, `verify`,
   `show`, `store cat`, `gc`, plus `resolve` as plumbing. Nothing
   missing surfaced.

The transcript is the agreed surface for the post-skeleton CLI build;
Milestones to v1 consumes it.

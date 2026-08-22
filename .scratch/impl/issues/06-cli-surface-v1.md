# CLI surface v1

Type: prototype
Status: claimed (markus, 2026-08-22)

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

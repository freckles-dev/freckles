# PROTOTYPE — CLI surface v1 (wayfinder ticket 06)

One artifact: [transcript.md](transcript.md) — the proposed v1 CLI as a
mock terminal session over the walking-skeleton chain. React to the
scenes; verdicts land in the ticket's Answer.

## Decisions embodied — react to these

- **R1 — `heal` is *the* verb.** No `install`/`apply`/`up`: day-1 is
  day-2 from zero (everything stale, heal it), so one verb covers first
  deployment and every change after. Scene 1. Alternatives: `apply`
  (terraform muscle memory, but stage-era flavor), `up`, `run`.
- **R2 — `status` heals stale pure nodes while walking.** Pure
  re-derivation is side-effect-free by design, and it's the only way to
  name the exact checkpoint set (downstream derivations need upstream
  claims). `--frozen` for look-don't-touch. Scene 3. Alternative: a
  read-only status that can only name the first stale frontier and says
  "downstream undetermined".
- **R3 — the checkpoint prompt** = day2.md's format: node, plugin,
  effect, superseded claim, plaintext secret names, `prior`
  availability, privilege line when `requires_privilege` (not shown —
  no privileged node in the chain). Scenes 1/3/5.
- **R4 — name-first output**: CIDs abbreviated to `bafyre…xxx`
  everywhere a name leads; full CIDs via `show` / `store cat`.
- **R5 — the ambiguity error prints a ready-to-paste `use:` fix.**
  Scene 4.
- **R6 — exit-code contract**: 0 success/current · 1 error · 2 not
  current; `status --check` is the silent CI question. Scene 9 + table.
- **R7 — inspection is exactly two commands**: `show <node>` (human
  view, secret-marked annotations redacted) and `store cat <cid>` (raw
  DAG-JSON of any store document). No further store browsing in v1 —
  the folder backend is the browse story.
- **R8 — verb inventory is exactly**: `heal`, `status`, `verify`,
  `show`, `store cat`, `gc` (+ `resolve` as a plumbing alias for
  re-resolve-only). Anything missing you'd reach for weekly?

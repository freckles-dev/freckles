# The v1 cut

Type: grilling
Status: claimed (markus, 2026-08-22)

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

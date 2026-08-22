# Package layout and module seams

Type: grilling
Status: resolved
Blocked by: 02

## Question

The module map for v1 — run /codebase-design with /grilling and
/domain-modeling. Candidate seams:

- **store** — backends behind `put/get/has/cids` + refs + gc.
- **documents** — claims, envelopes, canonical encoding, CIDs.
- **resolver** — DAG assembly, edge inference, the resolution document.
- **runner** — workspace materialization, process protocol, the secrets
  boundary.
- **heal** — the topological walk, derivation index, checkpoint set.
- **plugins** — built-ins.
- **cli**.

Decide: public API vs internal; which seams the Walking skeleton must
instantiate; where the deep-module boundaries sit so tests bite the
interfaces, not the internals. Record as a short layout doc asset.

## Answer

Resolved 2026-08-22 in one grilling round; all five points adopted as
proposed. Asset: [the layout doc](../assets/08-package-layout.md).

1. **The §7 in/out line is a package boundary**: `store` (immutable
   CAS + refs) vs **`state`** (annotations index, derivation index,
   distrust marks, audit log) — nothing mutable can masquerade as
   content-addressed.
2. **Built-ins run in-process** behind the same Request/Outcome
   document interface as spawned plugins — the seam is the document
   types, not the process. Two runner adapters (in-process, process) =
   a real seam. `command`'s wrapped invocation stays a fully-enforced
   subprocess; the standard plugins exercise the true process path.
3. **Standard plugins live in this repo** (`plugins/`, standalone
   SDK-consuming scripts, built as separate artifacts by CI) — the
   artifact boundary enforces the separation; a second repo waits for a
   third-party plugin ecosystem.
4. **Public surface v1 = CLI + `freckles.sdk`**; core modules declared
   internal/unstable so seams can move as the skeleton teaches.
5. **Module names final**: documents, store, state, resolver, runner,
   heal, builtins, sdk, cli — names are glossary terms; `heal` matches
   the verb.

The skeleton instantiates both runner adapters (in-process built-ins
plus one spawned fake plugin speaking DAG-JSON), keeping the map
destination's "process-protocol runner" honest.

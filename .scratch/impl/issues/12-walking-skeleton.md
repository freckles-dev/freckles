# Walking skeleton

Type: task
Status: resolved
Blocked by: 05, 07, 08, 11

## Question

The map's carried execution (charter Q5, taken as proposed): the
thinnest end-to-end slice proving the decisions compose.

Build: resolve a 3–4 node chain (`import-values` → pure `command`
render → effectful `command`) → run it → claims, provenance, and the
resolution document land in a **sqlite CAS with real CIDv1 addressing**
(golden-CID checked) → edit config → re-resolve → the heal walk
computes the **checkpoint set** → confirm the checkpoint → the plugin
receives `prior:`.

**In**: CAS+CIDs, resolution document, derivation index,
process-protocol runner with minimal-but-real physical visibility
enforcement (isolated workspace, scrubbed env), purity split, staleness
walk, checkpoint confirm.
**Out** (post-map build): secrets, bootstrap-mise/mise-install, folder
and ipfs backends, drift/verify, GC, CLI polish — raw dev commands are
fine.

Done when the loop runs under the test suite *and* by hand; record a
transcript as an asset. React HITL: any friction feeds back into the
affected decision tickets before Milestones to v1 closes the map.

## Answer

Resolved 2026-08-24, skeleton commit `efae717` on `develop`. Both
done-conditions met: the loop runs under the test suite
(`tests/e2e/test_skeleton_chain.py` — 59 tests green overall) and by
hand ([transcript asset](../assets/12-skeleton-transcript.md), via the
committed `examples/skeleton/` chain and hidden `freckles dev`
commands).

**What runs**: resolve (edge inference, ambiguity/`use:`/cycle hard
errors, config snapshot as tree doc, ref `cfg/<name>/current`) → heal
(topological walk, derivation-index lookup, pure auto-heal, checkpoint
set with injected `confirm`, unconfirmed checkpoints hiding their
downstream, `prior:` on confirmed re-runs) → sqlite CAS with real
CIDv1 addressing (the walk mints the exact golden
`derivation-values-apps` document — E2E and the golden suite meet on
one CID). Runner: both adapters — in-process built-ins
(`import-values`, `command`; the wrapped invocation is a real
subprocess) and spawned fake plugins speaking DAG-JSON on stdio —
with isolated workspaces, scrubbed env (asserted by an env-echo
fake), input materialization, and the misbehavior battery. All
Testing-strategy machinery is live: golden triple assertions,
dual-encoder cross-check on test-minted documents, backend contract
suite, run-twice determinism checks. The Packaging `selftest` exists
and the guardrail smoke calls it.

**Frictions fed back** (react HITL — for ratification before
Milestones to v1 closes the map):

1. **The source-rerun rule** (design.md §8 gap, found by the E2E
   test): a source node's derivation is content-free (`{file, key}`,
   zero inputs), so a derivation-index hit would keep it current
   forever — the day-2 story ("the apps values claim re-derives
   automatically") only works if **the heal walk re-runs source nodes
   every walk**, letting extensional addressing stop the ripple when
   the import is unchanged. Implemented (Builtin.source flag);
   proposed §8 amendment: one sentence stating the rule.
2. **pyyaml** added to the pinned stack (configuration loading —
   Stack and libraries never named a YAML library); addendum recorded
   on that ticket, conda recipe mirrored.
3. **Plugin content ingestion** (new fog): built-ins ingest produced
   files into the CAS as trusted core, but the wire protocol has no
   channel for a *spawned* plugin to get blobs into the store — the
   moment a standard plugin produces a file-tree (copier), the
   ingestion protocol must be designed. Added to Not yet specified.

Deliberately rough, as chartered: dev commands instead of the ratified
CLI, no secrets, no bootstraps, sqlite backend only, no gc/drift, PATH
baseline `/usr/bin:/bin` until tool claims exist.

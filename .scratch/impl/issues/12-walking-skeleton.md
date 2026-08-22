# Walking skeleton

Type: task
Status: open
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

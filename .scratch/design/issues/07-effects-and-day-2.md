# Effects and day-2

Type: grilling
Status: open
Blocked by: 01, 02

## Question

Some nodes change the world (tofu apply creates a VM; flux bootstrap mutates
a cluster). Their outcomes are trusted, hashed descriptions of what now
exists. Decide the semantics of effects and change over time.

To resolve:

Routed here by What is an outcome? (resolved): trust semantics are decided —
act without re-checking; pure unconditional, effectful until explicitly
contradicted; caching is a provenance-keyed lookup (derivation → outcome).
This ticket owns the mechanics on top of that.

- Re-run semantics: when a node's inputs change, what happens to the node and
  its old outcome? Re-run in place (tofu-style converge)? New outcome
  superseding the old? What marks downstream nodes stale?
- Realization mechanics (from 01's consumption rule): claims travel through
  the store, annotations don't. Realizing a trusted-but-unrealized claim on
  this machine — for pure claims, re-derive via provenance-keyed cache miss;
  what for effectful claims (which cannot be re-derived)? What does the
  derivation index look like, and when may a cached outcome be reused as
  current without re-running?
- Confirmation: the vision doc made every effectful stage an explicit
  user-confirmed checkpoint — does that survive unchanged in the tree model?
- Idempotency expectations on effectful plugins: is "re-running with
  identical inputs is a no-op" a contract requirement?
- Teardown: outcomes describe creation — what describes destruction? Is
  removal a first-class operation (node deleted ⇒ world converges), or
  manual/out of scope for the design doc?
- Drift: a trusted outcome claims a host exists; the host dies. Restate the
  vision doc's stance (drift detection belongs to the underlying tools) in
  outcome terms — when is an outcome's trust revoked, and by what?
- The journal: with effectful outcomes as first-class hashed values in the
  store, is a separate append-only journal still needed, or does the store's
  history subsume it? (This resolves fog: "the journal's fate".)
- Root/sudo: the rare target-side privilege needs — declared on the node,
  confirmed explicitly, never silent. Confirm the vision doc's rule carries
  over.

Run /grilling and /domain-modeling. Grill against vision.md §4 (execute
stages), §9 (journal), open questions 5, 7.

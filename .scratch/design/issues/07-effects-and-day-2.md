# Effects and day-2

Type: grilling
Status: resolved
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
- History retention (routed from Storage and addressing, resolved): refs
  point only at *current* claims and the *current* resolution document, and
  unreferenced blocks are GC-collectable after grace. So: are there history
  chains (`cfg/<config>/nodes/<node>/history`, old resolution documents),
  and is that retained history the journal's successor — or is the audit
  log alone enough?

## Answer

Resolved 2026-08-20 in one grilling round; all seven points explicitly
adopted by Markus. Assets: glossary updates in
[CONTEXT.md](../../../CONTEXT.md), `prior:` added to the
[wire-protocol asset](../assets/06-wire-protocol.yaml).

1. **The day-2 loop**: edit config → re-resolve (new resolution document,
   pure, cheap) → **stale set** = nodes whose current claim was not
   produced by their new derivation (derivation-index lookup) → present by
   node name → heal: pure nodes re-derive automatically, effectful nodes
   are checkpoints → refs advance, superseded claims become GC-fodder.
   "Is the deployment current?" = "is the stale set empty?".
2. **`prior:`**: the request document gains the node's previous outcome
   (claim + annotations) — present only when one exists and only for
   effectful plugins; pure plugins never see it. Idempotency contract:
   re-run with identical effective inputs and prior must be
   side-effect-safe and should be a no-op. Convergence with the world is
   the tool's business; freckles delivers continuity.
3. **Checkpoints**: effectful nodes never run implicitly — per-node
   explicit confirmation, with deliberate opt-in auto-confirm for
   automation. The prompt names the node, the claim being superseded, and
   privilege needs via a new manifest flag `requires_privilege`. Never a
   silent sudo.
4. **Teardown, v1**: node removal orphans its effectful claim; freckles
   *reports* orphans, cleanup is the operator's job with the underlying
   tools. A future optional `destroy` manifest entrypoint is named as the
   extension point, deliberately unspecified.
5. **Drift**: optional `verify` manifest entrypoint; `freckles verify` is
   explicit, never polled. Contradiction marks the claim **distrusted** in
   the local annotations index (claims stay immutable) — which makes the
   node stale through the one existing staleness mechanism; re-running
   heals.
6. **The journal's successor is the audit log**: append-only, records every
   run with derivation and claim CIDs, so "what was deployed when" stays
   textually answerable even after blocks are GC'd. No history refs in v1;
   bounded history refs (last N resolution documents) named as a cheap
   later option.
7. **Claims-only consumption**: consuming any claim requires only the
   claim — a node's annotations are private to the machine that runs that
   node. Consequence stated honestly: re-running an effectful node is
   bound to the machine holding its annotations; moving that seat means
   moving tool state, out of scope alongside multi-machine sync.

Manifest grew two optional fields here: `requires_privilege`, `verify`
(plus `destroy` as a named-future entry).
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

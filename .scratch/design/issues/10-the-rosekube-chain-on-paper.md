# The rosekube chain on paper

Type: prototype
Status: resolved
Blocked by: 02, 06

## Question

Raise the fidelity: write the full rosekube chain as concrete documents in
the settled schema — the worked example that anchors the design doc, and the
test that the decided model actually expresses the motivating case.

The chain: bootstrap (tool name, version, parameters) → opentofu tool
install → infrastructure outcome (Proxmox VM + Talos host) → flux install on
the cluster → flux config directory → an app or two (e.g. paperless-ngx with
CloudNativePG, Tailscale ingress).

Starting point: the low-fidelity sketch confirmed in The shape of the tree
(assets/02-rosekube-chain.yaml) — this ticket raises it to full fidelity
(complete claim/annotation/provenance documents in the settled schema) and
adds the day-2 delta.

Produce, as real files (linked from this ticket, living under
`.scratch/design/prototype/`):

- each node's configuration document,
- each node's outcome document (plausible, hand-written),
- the tree/DAG wiring between them, in the decided addressing scheme,
- at least one day-2 delta sketched: a changed input and which
  outcomes/hashes it invalidates,
- (added by Secrets in the outcome model, 09) at least one flow-A secret in
  the chain — the Proxmox API token as a value-bearing secret value consumed
  by the tofu-apply node — plus a credential-bearing outcome (the
  kubeconfig as a secret-marked annotation) in the settled shapes.

React to it with Markus (HITL): where the schema feels clumsy, verbose, or
ambiguous, feed corrections back into the affected decisions before the
design doc is written.

Asset: [the prototype](../prototype/README.md) — full chain (13 nodes),
resolution document, per-node outcome + provenance docs, two day-2 deltas;
seven reaction points (R1–R7) in its README, all reacted to below.

## Answer

Resolved 2026-08-21. Prototype built at full fidelity, then reacted to by
Markus point by point (R1–R7). One glossary term added to
[CONTEXT.md](../../../CONTEXT.md); naming inputs routed to Glossary and doc
outline.

1. **The decided model expresses the motivating case.** No schema change
   was needed: uniform envelopes, credentials as secret-marked annotations
   (the kubeconfig never nears a claim), both secret flows in one chain,
   the detached secret needing no special claim shape, `prior:` making the
   rotation re-run converge — and in delta B the extensional payoff:
   rotating the Proxmox token re-runs `tofu apply`, which returns the same
   cluster claim, so staleness stops at the consuming node. ADR 0001's
   residual-doubt case landed on the right side.
2. **The granularity principle** (R1+R2, adopted as a stated design-doc
   principle, not folklore): *import at the granularity of independent
   change.* Consumed claims are identity (ADR 0002), so import granularity
   sets the blast radius of every change: the sketch's single `secrets`
   and `config` nodes over-tainted (any secret rotation would re-run
   `tofu apply`; enabling an app would stale infra). The chain now imports
   one secret value per node and splits cluster values from app values —
   which is exactly what preserves vision §10's "only push is stale".
3. **The aggregator door is named, strongly, and stays shut** (R3): the
   first concrete knock is `render/flux-tree` needing cluster values in
   addition to app values — two claims of kind `config`, inexpressible
   under one-claim-per-consumed-kind. The design doc names this example
   verbatim; opening the door remains future work.
4. **`use:` verbosity accepted** (R4): six explicit selections across the
   chain is the cost of ambiguity-as-hard-error, and Markus sees no way
   around it. No change.
5. **Terminal nodes are a property, not a smell** (R5, Markus's reframe of
   "dangling"): a node no other node consumes is a legitimate sink whose
   realization is the point — `tools/talosctl` exists *so that* the
   operator can use it manually. No warning; glossary term added.
6. **`render/flux-tree` rename stands** (R6): non-roots don't belong under
   `sources/`; recorded as naming input for Glossary and doc outline.
7. **Kind namespacing convention** (R7): flat kind names are reserved for
   official vocabulary — the core kinds plus officially published
   catalogs; non-core publishers are *advised* to namespace-prefix their
   kinds (e.g. `acme/thing`). A curation-governance convention, never
   syntax enforcement (consistent with Where curation lives). Wording
   lands in the design doc via Glossary and doc outline.

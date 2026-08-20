# The rosekube chain on paper

Type: prototype
Status: open
Blocked by: 02, 06

## Question

Raise the fidelity: write the full rosekube chain as concrete documents in
the settled schema — the worked example that anchors the design doc, and the
test that the decided model actually expresses the motivating case.

The chain: pixi bootstrap (tool name, version, parameters) → opentofu tool
install → infrastructure outcome (Proxmox VM + Talos host) → flux install on
the cluster → flux config directory → an app or two (e.g. paperless-ngx with
CloudNativePG, Tailscale ingress).

Produce, as real files (linked from this ticket, living under
`.scratch/design/prototype/`):

- each node's configuration document,
- each node's outcome document (plausible, hand-written),
- the tree/DAG wiring between them, in the decided addressing scheme,
- at least one day-2 delta sketched: a changed input and which
  outcomes/hashes it invalidates.

React to it with Markus (HITL): where the schema feels clumsy, verbose, or
ambiguous, feed corrections back into the affected decisions before the
design doc is written.

# PROTOTYPE — the rosekube chain on paper (wayfinder ticket 10)

**Throwaway.** Hand-written documents in the schema the map has settled
(tickets 01–09); nothing executes them. The question they answer: *does the
decided model actually express the motivating case, and where does it feel
clumsy?* React; corrections feed back into the affected decisions.

## Reading order

1. [config/freckles.yaml](config/freckles.yaml) — the user's DAG
   ([cluster.yaml](config/cluster.yaml),
   [secrets.sops.yaml](config/secrets.sops.yaml) beside it)
2. [resolution.yaml](resolution.yaml) — the resolution document (wiring,
   pinned plugins), plus refs and derivation index after the first run
3. [outcomes/](outcomes/) — per node: claim, annotations, provenance
   (bootstrap-and-tools, sources, infra-staging, flux-tree, flux-bootstrap,
   push-config)
4. [day2.md](day2.md) — two deltas: enable karakeep; rotate the Proxmox token

CID convention: placeholders (`bafy_CLAIM_INFRA_V1`) for readability; real
addresses are opaque base32 CIDv1. Real store docs are spec-strict DAG-CBOR;
YAML here is for reading. Claim/provenance are separate store documents even
where a file groups them; annotations live only in the local index.

## What writing it surfaced — react to these

> Reacted 2026-08-21 — verdicts on all seven points live in
> [the ticket's Answer](../issues/10-the-rosekube-chain-on-paper.md).

- **R1 — secret granularity.** The sketch's single `sources/secrets` node
  would make *any* secret rotation stale *every* secret consumer (rotating
  Tailscale OAuth would re-run `tofu apply`). Since consumed claims are
  identity (ADR 0002), granularity is load-bearing: the prototype uses one
  `import-sops` node per value. Cost: three source nodes where the sketch
  had one.
- **R2 — config granularity, same disease.** One `cluster.yaml` claim would
  put `infra/staging` in the stale set when an app is enabled — breaking
  vision §10's "only push is stale" promise. Split into `values/cluster` +
  `values/apps`. Question behind R1+R2: should the design doc state a
  *principle* (import at the granularity of independent change), or does
  this stay authoring folklore?
- **R3 — same-kind multi-consume is one step away.** The moment
  `render/flux-tree` needs cluster values *too* (say, the cluster name in a
  dashboard title), it consumes two `config` claims — which the one-claim-
  per-consumed-kind contract cannot express. The aggregator door (The shape
  of the tree) gets its first concrete knock. Fine to leave future, but the
  design doc should name this exact example.
- **R4 — `use:` frequency.** Six explicit `use:` lines across the chain,
  because `config` and `secret` each have multiple providers. The hybrid
  rule works exactly as designed (ambiguity → hard error → explicit pick) —
  but is this the authoring feel you want for the common case?
- **R5 — `tools/talosctl` dangles.** No node consumes it (true in the
  sketch too). Under ADR 0002 it costs nothing downstream — but is a
  no-consumer node a smell freckles should warn about, a feature (operator
  convenience tools), or should `infra/staging` consume it for health
  checks?
- **R6 — renamed `sources/flux-tree` → `render/flux-tree`.** It consumes
  inputs, so it is not a root; the sketch's name was misleading. Naming
  input for the glossary ticket.
- **R7 — kind vocabulary in play.** Core kinds used: `bootstrap`, `tool`,
  `config`, `secret`, `file-tree` (+ `plugin`). Catalog kinds:
  `talos-cluster`, `gitops`, `gitops-synced`. The split reads clean here;
  final naming belongs to Glossary and doc outline.

## Where the settled decisions carried without friction

Uniform envelopes for pure and effectful nodes; credentials as secret-marked
annotations (the kubeconfig never nears a claim, ADR 0005); both secret
flows in one chain (flow A: proxmox token + age key resolved at the
boundary; flow B: tailscale ciphertext embedded in the rendered tree); the
detached secret (`store: false`) needing no special claim shape; prior:
making the rotation re-run converge; and the extensional-addressing payoff
in delta B — the staleness ripple stopping exactly at the node that
consumed the rotated secret.

# Normative wire schemas

Type: prototype
Status: resolved

## Question

The wire asset (`.scratch/design/assets/06-wire-protocol.yaml`) is
illustrative — field names explicitly non-normative, and it predates the
`config` → `values` kind rename. Harden it into the normative v1
schemas (language-agnostic: these documents are DAG-CBOR regardless of
implementation language):

- **Request document**: inputs as claim+annotation pairs, runner-injected
  `resolved:` secrets, workspace (dir, constructed PATH), `prior:`
  (effectful only), node config.
- **Outcome document**: the claim+annotations envelope, `schema` field
  semantics, secret-marked annotations; **structured error** shape.
- **Resolution document**: config snapshot CID, resolved post-inference
  edges, plugin+version per node, consumed-claim wiring.
- **The derivation's canonical bytes**: exactly what enters the
  derivation hash (plugin claim CID or freckles version for built-ins,
  canonicalized node config, input claim CIDs; node names excluded) and
  how it is serialized and addressed.

Produce schema files as assets (format is part of the ticket: CDDL,
JSON Schema, or annotated golden examples) plus at least one golden
example each of a claim and a derivation **with computed CIDs**. React
with Markus (HITL); friction feeds back into the affected design
decisions.

Run /grilling and /domain-modeling alongside /prototype.

## Answer

Resolved 2026-08-22. Prototype built at
[conformance/](../../../conformance/) (originally
`assets/05-wire-schemas/`, relocated by Repo scaffolding) — `store.cddl`,
`wire.cddl`, and skeleton-chain golden fixtures with real computed
CIDv1 addresses (`uv run make_golden.py` regenerates deterministically).
Reacted point by point; all seven verdicts by Markus. The schemas are
**normative for v1** as of this resolution.

1. **R1 — the wire is DAG-JSON, the store is DAG-CBOR** (as embodied):
   same IPLD data model, lossless both ways, shell-scriptable with jq;
   nothing on the wire is ever hashed as-is.
2. **R2 — the derivation is a standalone store document and its CID
   *is* the derivation hash**; the provenance record is pure links
   `{derivation, outcome}` — identical derivations dedup structurally.
3. **R3 — flat claim envelope**: `schema` + `kind` reserved at top
   level, payload fields flat beside them.
4. **R4 — explicit `shape` discriminator** (`value` / `reference`) on
   secret claims — the open-set contract gets a place to grow.
5. **R5 — the resolution document speaks names**: nodes keyed by name,
   edges consumed-kind → provider-node-name, claim CIDs deliberately
   absent (refs and the derivation index own that mapping).
6. **R6 — request `inputs` keyed by consumed kind** (map), mirroring
   the derivation's keying; widens to list-valued form only if the
   aggregator door opens.
7. **R7 — design gap found and closed**: the node-supplied rule extends
   to **`effect`** for `command` — one built-in cannot be
   manifest-statically pure *and* effectful, and the purity gate needs
   effect at resolution. design.md §6 amended (recorded on The plugin
   contract, amendment item 4); consequence applied here: the
   resolution document's `resolved-node` records `effect` beside
   `produces`, fixtures regenerated.

The golden fixtures seed Testing strategy's golden-CID suite;
relocating schemas/fixtures into the real source tree belongs to Repo
scaffolding / Package layout and module seams.

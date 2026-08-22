# PROTOTYPE — normative wire schemas (wayfinder ticket 05)

Draft-normative schemas for every document freckles v1 hashes or speaks,
plus golden fixtures with **real computed CIDs**. React; on resolution
these become the normative v1 schemas and the fixtures seed Testing
strategy's golden-CID suite.

## Reading order

1. [store.cddl](store.cddl) — everything DAG-CBOR-hashed: claim envelope,
   secret shapes, tree document, **derivation** (the canonical bytes),
   provenance record, resolution document.
2. [wire.cddl](wire.cddl) — the runner ↔ plugin stdio protocol: request,
   outcome, structured error.
3. [golden/](golden/) — `make_golden.py` (re-run: `uv run make_golden.py`)
   generates the skeleton-chain documents; `CIDS.txt` is the address
   manifest. Every CID is real CIDv1/sha2-256 over spec-strict DAG-CBOR
   (hashberg `dag-cbor` — length-first key order verified).

## Decisions embodied — react to these

- **R1 — the wire is DAG-JSON, the store is DAG-CBOR.** Same IPLD data
  model, lossless both ways (links `{"/": "bafy…"}`, bytes
  `{"/": {"bytes": …}}`), but a shell-script plugin or test fake can speak
  it with jq. Raw CBOR on stdio was rejected as shell-hostile; ad-hoc
  JSON as lossy. Nothing on the wire is ever hashed as-is.
- **R2 — the derivation is a standalone store document and its CID *is*
  the derivation hash.** Provenance shrinks to pure links
  `{derivation, outcome}`; identical derivations dedup structurally.
  Alternative (folded into provenance, hash a sub-map) rejected as two
  serializations of one thing.
- **R3 — claim envelope: `schema` + `kind` reserved at top level, payload
  fields flat beside them** (matches the design prototype's documents).
  Alternative: a nested `payload` map — cleaner reservation story, noisier
  documents.
- **R4 — secret claims carry an explicit `shape` discriminator**
  (`value` / `reference`) rather than inferring shape from field
  presence — the "set explicitly open" contract gets a place to grow.
- **R5 — the resolution document speaks names, not claims**: nodes keyed
  by name, edges as consumed-kind → provider-node-name, `produces`
  recorded per node (the resolution-time-fixed kind). Claim CIDs are
  deliberately absent — resolution precedes running; refs and the
  derivation index own that mapping.
- **R6 — request `inputs` is a map keyed by consumed kind**, mirroring
  the derivation's keying (the illustrative asset had a list). One claim
  per kind holds until the aggregator door opens; the map widens to a
  list-valued form then.
- **R7 — writing the fixtures exposed a design gap**: `command` wrapping
  an effectful script needs node-supplied **`effect`**, exactly as the
  adapter amendment gave it node-supplied `kind` — `effect` is
  manifest-static in the design, and one `command` built-in cannot be
  both pure and effectful. Embodied here as `effect` in the command
  node's config; alternatives: two built-ins (`command` /
  `command-effectful`), or extending the node-supplied rule (my lean —
  same argument as kind: resolution-time-fixed, hashed via node config,
  and the purity gate needs it at resolution). Needs a design-side
  amendment either way.

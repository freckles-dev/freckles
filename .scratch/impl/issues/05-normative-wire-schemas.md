# Normative wire schemas

Type: prototype
Status: open

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

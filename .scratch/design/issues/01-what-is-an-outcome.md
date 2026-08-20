# What is an outcome?

Type: grilling
Status: resolved

## Question

The central new idea, and the map's first decision: what exactly does an
operation return?

The brief: every operation returns a dict-like structure describing its
*outcome* — which is then **trusted** and **hashed**. The output hash is not
necessarily a hash of actual bytes; it is the hash of the outcome description.
This diverges from the vision doc's model (byte-hashed file-tree artifacts for
render stages; execute stages journaled but their results not first-class
pipeline values), and per the charter, the brief supersedes on conflict.

To resolve:

- The outcome structure's shape: what fields are mandatory (identity of the
  operation? input hashes? capability descriptions?), what is free-form, and
  how it is canonicalized for hashing (key ordering, encoding).
- How outcomes relate to actual bytes. When a node *does* produce a file tree
  (copier render) or a binary (opentofu install), does its outcome reference a
  byte hash as one field, so byte-level content-addressing survives as a
  special case inside outcome hashing? Or are bytes never hashed at all?
- What "trusted" means precisely, and when trust breaks. A trusted outcome
  says "a Talos host exists at 10.0.50.50" — what invalidates that claim?
  (Full answer belongs to Effects and day-2, but the *trust semantics* are
  decided here.)
- Whether pure (render) and effectful (apply) operations return the same kind
  of value — the brief implies yes, which unifies what the vision doc split.
  Confirm, and name the consequences.
- The brief's closing framing: outputs "describe the environment and its
  capabilities" — is an outcome primarily a *record of what happened* or a
  *description of what is now available* (an environment downstream nodes can
  consume)? This choice shapes everything downstream.

Run /grilling and /domain-modeling. Grill against vision.md §4–5 (pipeline
model, reproducibility stance) — each superseded point should be named
explicitly in the answer.

## Answer

Resolved 2026-08-20 over three grilling rounds; confirmed by Markus.
Assets: [ADR 0001](../../../docs/adr/0001-extensional-outcome-addressing.md),
glossary terms in [CONTEXT.md](../../../CONTEXT.md).

1. An outcome is a **present-tense description of what now exists and can be
   consumed** — never a record of how it happened. "What happened" is the
   audit log, which downstream operations never read.
2. **One uniform envelope** for pure and effectful operations. Purity is a
   property the operation declares; payloads are operation-specific.
3. Envelope = **claim** (hashed) + **annotations** (unhashed). Claim:
   identity-defining, machine-independent assertions about the world.
   Annotations: non-identity realization facts (paths, timestamps, hosts).
   Named boundary case — world-true but arguably non-identity facts, i.e.
   credentials/volatile capability material (the kubeconfig question) —
   deferred to Secrets in the outcome model (09).
4. **Extensional addressing** (ADR 0001): the outcome's address is the hash
   of the claim alone. Provenance (plugin + version, config, input claim
   addresses) is a separate content-addressed record per derivation. Caching
   is a provenance-keyed lookup (derivation → outcome). Held with explicit
   residual doubt; revisit triggers named in the ADR.
5. Claims may **reference byte content by content hash**: portable content
   (rendered trees) lives in the CAS; live/local state (VMs, envs) is
   described, never byte-hashed.
6. **Trust** = freckles acts on an outcome without re-checking the world.
   Pure outcomes: unconditional (worst case re-derive). Effectful outcomes:
   trusted until explicitly contradicted. Verification is an explicit
   operation, never background polling.
7. **Success-only outcomes.** Failures exist solely in the audit log;
   nothing downstream can consume a failure.
8. Claim value model = **DAG-CBOR data model**: string-keyed maps, lists,
   strings, 64-bit ints, bools, null, CID references; no floats. Buys
   IPFS-identical addressing per the CAS survey (04). Annotations free-form.
9. **Consumption rule**: an operation receives the full envelopes of its
   inputs (claim + annotations). Claims travel through the store;
   annotations do not; a trusted-but-unrealized claim must be **realized**
   locally first. Realization mechanics → Effects and day-2 (07).
10. **`kind` is a mandatory claim field**; the kind vocabulary and how
    plugins declare accepted kinds → The plugin contract (06) / Where
    curation lives (08).
11. Hashed **`schema` version field** on the envelope; no address stability
    promised across envelope format versions.

Supersessions of vision.md made explicit: the artifact/journal output split
(§4) is replaced by the uniform outcome envelope; byte-hashed artifacts
remain only as CAS-referenced content inside claims; the journal's role
shrinks to the audit log plus provenance records (final form decided in 07).

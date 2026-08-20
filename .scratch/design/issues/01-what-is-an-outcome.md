# What is an outcome?

Type: grilling
Status: open

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

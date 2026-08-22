# freckles

freckles turns minimal declarative configuration into running infrastructure
and IT state through a DAG of named, hashed, content-addressed operations.
This glossary is canonical for design discussions and documents, and is the
design doc's glossary (naming review completed 2026-08-21, ticket "Glossary
and doc outline"). Retired vocabulary: stage, pipeline, render/execute
stages, artifact, journal, lockfile, frecklet (catalog-effort vocabulary).

## Language

**Operation**:
A pluggable unit of work that declares the claim kinds it consumes and
produces one outcome on success. Declares itself pure or effectful.
_Avoid_: transformer, task, stage

**Node**:
A named element of the DAG: a stable, path-like human name binding an
operation, its configuration, and input edges. Names are the stable
identity across config edits; hashes are the versioned identity beneath.

**Configuration**:
The user's whole declaration: the named-node DAG plus the values and secret
files beside it. A git working copy, never store content; the resolution
document snapshots it by CID. A node's `config` block — its operation
parameters — is "node config", never "the configuration".

**Values**:
The claim kind of imported user-supplied value documents (produced by
`import-values`), imported at the granularity of independent change.
_Avoid_: config (as a claim kind)

**Available environment**:
The merged claims of a node's transitive predecessors, keyed by kind. A
resolution-time concept for edge inference and checks; never visible to an
operation at run time.

**Effective inputs**:
The claims matching an operation's declared consumed kinds — the only
inputs entering the node's provenance record and cache key, and exactly
what the operation receives at run time. Pure operations receive claims
only; effectful operations also receive whatever annotations exist locally.

**Plugin**:
The content-addressed implementation an operation runs: a claim of kind
plugin whose content is a manifest (name, version, produced kind, consumed
selectors, effect, platforms, entrypoint) plus an executable payload.
Invoked as a process — request document on stdin, outcome or error on
stdout. A minimal built-in set ships with freckles itself.

**Source node**:
A root node whose pure operation imports external content (files,
directories, encrypted values) into the store; its claim references the
imported bytes.

**Terminal node**:
A node no other node consumes. Legitimate, never a warning: its realization
is the point (a tool on PATH for manual use) — a sink consumed by humans
rather than by the DAG.

**Outcome**:
The value a successful operation returns: a structured description of what
now exists and can be consumed — never a record of how it happened. One
uniform envelope for pure and effectful operations: a Claim plus Annotations.
Failures never mint outcomes.
_Avoid_: artifact, output, result

**Claim**:
The hashed part of an outcome: identity-defining, machine-independent
assertions about the world. The claim's content hash is the outcome's
address. May reference stored byte content by content hash. Carries a
mandatory kind.

**Annotation**:
The unhashed part of an outcome: non-identity realization facts (local
paths, timestamps, hosts) recording where and when the claim is realized on
this machine. Annotations do not travel with the claim and are private to
the machine that runs the node.

**Secret value**:
An encrypted input: a claim whose identity is its ciphertext, referenced by
content hash — CAS-resident by default, detachable to the working copy when
the ciphertext must not be published. Rotation changes the ciphertext and
ripples staleness to consumers.

**Secret reference**:
A claim asserting that a named secret must be resolvable at run time.
Identity is the logical name alone; which provider holds the value on this
machine is machine-local configuration recorded in annotations at
resolution. Rotation is invisible to staleness — handled by explicit
verify and distrust.

**Credential**:
Access material minted by an effectful operation (a kubeconfig, a generated
password). Never identity: lives in secret-marked annotations, private to
the machine; rotates without changing any claim.

**Realization**:
Making a trusted claim usable on the local machine, producing its
annotations. Pure claims realize by local re-derivation; effectful claims
need no realization to be consumed — their claim fields suffice, and only
re-running their own node is machine-bound.

**Stale**:
A node whose current claim was not produced by its current derivation —
because an input changed or the claim was distrusted. Healed by re-running:
automatically for pure nodes, via checkpoint for effectful ones.

**Checkpoint**:
An explicit, per-node confirmed run of an effectful node. Effectful nodes
never run implicitly; auto-confirmation is a deliberate opt-in.

**Checkpoint set**:
The stale effectful nodes of a resolved configuration — what remains
after pure staleness heals automatically, and the only thing day-2
surfaces for confirmation. Discovered incrementally: a stale effectful
node hides its downstream until its checkpoint runs. "Is the deployment
current?" means "is the checkpoint set empty?"

**Provenance record**:
A separate content-addressed record of one derivation: which operation
(plugin, version, configuration) consumed which input claims to produce which
output claim. Preserves the audit chain without entering the claim's address.
_Avoid_: journal entry

**Store**:
The content-addressed home of all immutable documents and blobs (claims,
provenance records, imported content, resolution documents), addressed by
CID, with pluggable backends. One store per user; refs are namespaced per
configuration.

**Ref**:
A mutable name → CID pointer in the store — the only mutable state, doubling
as a garbage-collection root.

**Resolution document**:
The content-addressed snapshot of one resolved run: config snapshot, nodes
with their resolved edges, operations and versions, and consumed-claim
wiring. The lockfile's successor.
_Avoid_: lockfile

**Derivation index**:
The prunable local cache mapping derivation hashes to claim CIDs. Not refs,
never a GC root, rebuildable.

**Trust**:
Acting on an outcome without re-checking the world. Pure outcomes are trusted
unconditionally (worst case: re-derived); effectful outcomes are trusted
until explicitly contradicted. Verification is an explicit operation, never
background polling.

**Audit log**:
The append-only record of what operations did (runs with their derivations
and claim CIDs, logs, exit codes, durations, failures). The journal's
successor: it answers "what was deployed when". Never consumed by
downstream operations.
_Avoid_: journal

# freckles

freckles turns minimal declarative configuration into running infrastructure
and IT state through a tree of hashed, content-addressed operations. This
glossary is canonical for design discussions and documents; final naming
review happens in the wayfinder ticket "Glossary and doc outline" — terms
marked *(provisional)* may be renamed there.

## Language

**Operation** *(provisional)*:
A pluggable unit of work that consumes outcomes and its own configuration and
produces one outcome on success. Declares itself pure or effectful.
_Avoid_: transformer, task (candidate names, undecided), stage

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
this machine. Annotations do not travel with the claim.

**Realization**:
Making a trusted claim usable on the local machine, producing its
annotations. Pure claims realize by local re-derivation; realization of
effectful claims is an open question.

**Provenance record**:
A separate content-addressed record of one derivation: which operation
(plugin, version, configuration) consumed which input claims to produce which
output claim. Preserves the audit chain without entering the claim's address.
_Avoid_: journal entry

**Trust**:
Acting on an outcome without re-checking the world. Pure outcomes are trusted
unconditionally (worst case: re-derived); effectful outcomes are trusted
until explicitly contradicted. Verification is an explicit operation, never
background polling.

**Audit log**:
The record of what operations did (logs, exit codes, durations, failures).
Never consumed by downstream operations.

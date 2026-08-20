# freckles — domain glossary

Canonical terms for design discussions and documents. Final naming review
happens in the wayfinder ticket "Glossary and doc outline"; terms marked
*provisional* may be renamed there.

- **Operation** *(provisional; may become "transformer" or "task")* — a
  pluggable unit of work that consumes outcomes and its own configuration and
  produces one outcome. Pure or effectful — a property the operation
  declares, never one inferred from its output.
- **Outcome** — the value an operation returns: a structured description of
  what now exists and can be consumed as a result of the operation — not a
  record of how it happened. Composed of a Claim and Annotations.
- **Claim** — the hashed part of an outcome: what is asserted to be true,
  stated machine-independently. May reference byte content in the store by
  its content hash.
- **Annotation** — the unhashed part of an outcome: machine- or
  time-incidental facts (local paths, timestamps, hosts) recording where and
  when the claim happens to be realized here.
- **Trust** — freckles acts on an outcome without re-checking the world.
  Pure outcomes are trusted unconditionally (worst case: re-derived);
  effectful outcomes are trusted until explicitly contradicted. Verification
  is an explicit operation, never background polling.
- **Audit log** — the secondary record of what operations did (logs, exit
  codes, durations). Never consumed by downstream operations.

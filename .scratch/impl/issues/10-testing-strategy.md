# Testing strategy

Type: grilling
Status: open
Blocked by: 07

## Question

Decide the testing approach before the skeleton exists:

- **Golden-CID fixtures**: claims/derivations with known CIDs, sourced
  from the design prototype's documents — the cross-implementation
  safety net and the stack's acceptance check.
- **Fake plugins**: the process protocol makes fakes trivial (a shell
  script speaking the wire schema) — how far do runner tests lean on
  them?
- **Backend contract tests**: one suite all store backends must pass.
- The determinism run-twice harness for pure plugins.
- Secrets-boundary assertions: how to test that plaintext never touches
  disk, store, provenance, or audit.
- Integration-vs-unit line; TDD stance (/tdd skill for the build?); CI
  matrix.

Record as a testing doc asset consumed by Repo scaffolding and Walking
skeleton.

Run /grilling and /domain-modeling.

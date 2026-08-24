# Testing strategy

Type: grilling
Status: resolved
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

## Answer

Resolved 2026-08-24 in two grilling rounds; all thirteen points
ratified by Markus. Asset: [the testing doc](../assets/10-testing-strategy.md)
— the normative record, consumed by Repo scaffolding and Walking
skeleton.

1. **/tdd drives the post-skeleton milestones; the skeleton is
   test-along** — red-first is not enforced while seams are declared
   unstable.
2. **Seam-first tests with real collaborators** (sqlite in tmpdir, real
   runner, fake plugins); no internal mocks — substitution points are
   the fake plugin and heal's `confirm` callback; unit tests only for
   pure logic; one E2E chain test doubles as the skeleton
   done-condition; no coverage gate.
3. **Top-level `conformance/`** holds CDDL + golden fixtures +
   `make_golden.py` as language-external contracts (data-only); three
   assertions per fixture: codec round-trip to the committed CID,
   libipld↔hashberg byte-identity, CI regenerate-and-diff.
4. **The dual-encoder cross-check extends beyond the goldens**: a
   helper cross-checks every document seam tests mint. Example-based
   only — no hypothesis; revisit trigger is a codec bug slipping the
   goldens.
5. **Fake plugins are stdlib-only Python subprocesses** speaking
   DAG-JSON on stdio; misbehavior battery covers garbage/error/exit
   handling, kind-vs-produces mismatch, env-scrub attestation,
   workspace isolation. Timeouts excluded — no design semantics; new
   fog patch.
6. **One parametrized store-backend contract suite** (sqlite now,
   folder joins later) including gc; `state` components get ordinary
   seam tests pinning DerivationIndex's prunable/rebuildable/never-a-
   GC-root properties.
7. **Determinism harness**: run-twice, byte-identical claim + CID, all
   pure built-ins and standard plugins; internal-only in v1 (sdk export
   stays in the plugin-ergonomics fog).
8. **Secrets boundary tested in two layers**: redaction unit tests plus
   the sentinel canary byte-scan over everything that persists, with a
   vacuity guard (the effectful fake attests it saw plaintext).
9. **CI**: linux-only until Packaging and distribution widens it;
   Python 3.12 through latest stable; `tests/` mirrors modules plus
   `tests/e2e/`; one undivided suite, no markers.

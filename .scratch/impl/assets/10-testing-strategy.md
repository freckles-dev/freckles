# freckles v1 — testing strategy

Wayfinder ticket 10, resolved 2026-08-24. Consumed by Repo scaffolding
and Walking skeleton. Vocabulary note: the terms coined here (seam
test, conformance directory, misbehavior battery, determinism harness,
canary test) are testing-process vocabulary and live in this doc —
CONTEXT.md is the design glossary and stays untouched.

## Stance

- **TDD**: the /tdd skill is the doctrine for every post-skeleton
  milestone. The walking skeleton itself is **test-along** — tests land
  with each slice, but red-first is not enforced while seams are still
  declared internal/unstable and allowed to move.
- **Seam-first**: the default test exercises one module through its
  public contract with **real collaborators** — sqlite store in a
  tmpdir, real runner, fake plugins. No mocks of internal modules; the
  designed substitution points are the fake plugin (behind the wire
  protocol) and heal's injected `confirm` callback. Unit tests are
  reserved for genuinely pure logic: codecs, edge inference, staleness
  computation.
- One **end-to-end chain test** (resolve → run → heal) doubles as the
  walking skeleton's done-condition.
- **No coverage gate** — the golden, contract, misbehavior, and E2E
  suites define done-ness.

## Conformance directory

Top-level **`conformance/`**: `store.cddl`, `wire.cddl`, the golden
fixtures (DAG-JSON + `CIDS.txt`), and `make_golden.py`. Data-only and
language-agnostic — these are the language-external contracts that keep
ADR 0006's port option alive, not pytest property. Repo scaffolding
relocates the ticket-05 assets here.

Three assertions over **every** golden fixture:

1. `documents` codecs round-trip the fixture and reproduce the
   committed CID.
2. libipld and the hashberg `dag-cbor`+`multiformats` pair produce
   byte-identical encodings (the Stack-and-libraries cross-check).
3. A CI job re-runs `make_golden.py` and diffs against the committed
   files — generator and committed truth cannot silently diverge.

## Dual-encoder cross-check beyond the goldens

A `documents` test helper encodes any document with both libipld and
the hashberg pair and asserts identical bytes + CID. Seam tests use it
wherever they mint documents, so the whole suite is a rolling
differential check on document shapes the goldens don't cover.

**Example-based only** — no hypothesis/property-based testing in v1.
Revisit trigger: a codec bug slipping past the goldens, not
speculation.

## Fake plugins

- **Stdlib-only Python scripts**, spawned as real subprocesses speaking
  DAG-JSON on stdio — honest foreign processes, no shortcuts. They are
  the primary vehicle for process-adapter runner tests; the standard
  plugins get their own tests as their milestones land. The skeleton's
  "one spawned fake plugin" is the first of these.
- **Misbehavior battery** (runner defensive posture): garbage on
  stdout; nonzero exit with a well-formed error document; nonzero exit
  with nothing; outcome claim `kind` contradicting the manifest's
  `produces`; an env-echo fake asserting the scrub scrubbed; a
  write-outside-workspace fake asserting isolation. **Out**: hanging
  plugins/timeouts — the design specifies no timeout semantics; fog,
  not a test-invented policy.

## Store backend contract suite

One pytest suite parametrized over backend factories — sqlite now, the
folder backend joins the parametrization when it lands (the layout
doc's two-adapter test). Covers `put/get/has/cids` semantics,
idempotent re-put, ref set/get/list, and **gc** (roots,
`extract_links` traversal, grace).

`state` components (AnnotationsIndex, DerivationIndex, AuditLog) get
ordinary seam tests, not one-implementation contract ceremony. The
DerivationIndex tests pin its design properties: prunable,
rebuildable, never a GC root.

## Determinism harness

An internal test helper: run a pure operation twice from the same
request document, assert byte-identical claim and identical CID.
Applied to every pure built-in, and to pure standard plugins as their
milestones land. **Not** exported through `freckles.sdk` in v1 — that
belongs to the plugin-author-ergonomics fog patch.

## Secrets-boundary assertions (ADR 0005)

Two layers, specified now, written with the secrets milestone under
/tdd:

1. Unit tests on the request-builder and the AnnotationsIndex
   redaction paths.
2. The **canary test**: run a chain whose secret value is a
   high-entropy sentinel, then byte-scan everything that persists —
   store sqlite file, state db, audit log, provenance documents, the
   post-run workspace — asserting the sentinel appears nowhere.
   Vacuity guard: the effectful fake plugin attests it received the
   plaintext on stdin, so the test cannot pass by the secret never
   flowing.

## Layout and CI

- `tests/` mirrors the module names (`tests/documents/`,
  `tests/store/`, `tests/runner/`, …) plus `tests/e2e/`. **One
  undivided suite** — no markers, no fast/slow split; a suite nobody
  learns to skip.
- CI matrix: **linux-only** until Packaging and distribution decides
  platforms (that ticket widens the matrix); Python **every minor from
  the 3.12 floor through latest stable** (2026-08: 3.12, 3.13, 3.14).
- Separate CI jobs beside the matrix: the golden regenerate-and-diff
  check, and the Nuitka standalone guardrail (ADR 0006 rider — decided
  elsewhere, listed for completeness).

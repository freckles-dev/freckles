# Wayfinder map: freckles v1 implementation

Label: wayfinder:map
Tracker: local-markdown (`.scratch/impl/`, tickets under `issues/`)

## Destination

freckles v1's architecture is locked and a walking skeleton runs:
resolve → run → heal on a thin chain through a real CIDv1 sqlite store
and process-protocol runner. Handoff: the Milestones-to-v1 plan, whose
acceptance bar is the mechanics-complete synthetic chain, with design-v1
as the ceiling.

## Notes

- Domain: implementing [the design](../../docs/design.md). CONTEXT.md is
  the canonical glossary; ADRs 0001–0005 are binding; the design
  prototype (`../design/prototype/`) is the reference-fixture source.
- Every HITL ticket runs the `/grilling` and `/domain-modeling` skills.
- Execution override: this map carries execution only as far as Repo
  scaffolding and Walking skeleton; everything past the skeleton hands
  off through Milestones to v1.
- Charter facts (Markus, 2026-08-22):
  - Destination shape: walking skeleton + locked architecture (not
    decision-only, not a full build on the map).
  - Acceptance bar for v1 (post-map): the **mechanics-complete synthetic
    chain** — bootstrap-mise → mise-install → import-values/import-sops
    → pure render → effectful `command` node — exercising checkpoints,
    `prior:`, secret resolution at the boundary, staleness/heal, drift.
    Amended by The v1 cut (2026-08-22): plus copier installable through
    **both** bootstrap routes (bootstrap-mise → mise-install and
    bootstrap-pixi → pixi-install) — the swappable-bootstrap contract
    tested, not asserted. Catalog-level plugins stay out; the real
    rosekube chain is the catalog effort's validation, not this one's.
  - Code lives in this repo, beside the docs.
  - design-v1 is the **ceiling**; The v1 cut may trim it, never exceed it.
  - Implementation language is a decision, not an inheritance — "Python
    framework" came from the vision doc and was never decided.
- The language decision landed on Python (ADR 0006): use
  [frkl-dev/python-project-template](https://github.com/frkl-dev/python-project-template)
  and its tooling (uv; hatch build/publish with git-tag versioning; CI
  for tests/lint/typecheck; wheel/sdist + conda; justfile).
- Commit rhythm: per-claim and per-resolve commits, as in the design
  effort. Since Repo scaffolding (2026-08-24): work lands on `develop`
  (the template's release flow; tags merge to `main`), repo
  `freckles-dev/freckles`, license AGPL-3.0-only.
- Research findings live on `research/*` branches
  (`research/bootstrap-tools` and `research/cas-survey` exist;
  `research/language-ecosystems` is added by this map).

## Decisions so far

<!-- one line per closed ticket: gist + link -->

- [README refresh](issues/03-readme-refresh.md) — README rewritten to
  the design model in CONTEXT.md vocabulary; design.md is the entry
  point; the "Python framework" claim dropped (the language is an open
  ticket).
- [Language ecosystem survey](issues/01-language-ecosystem-survey.md) —
  all three candidates CID-conformant (sorting verified in source);
  go-git's pinned-commit fetch and Go's sqlite blob gaps drop Go; survey
  recommends Rust, with Python+PyApp the velocity-priced second;
  decision → Implementation language.
- [Implementation language](issues/02-implementation-language.md) —
  **Python** ([ADR 0006](../../docs/adr/0006-python-for-v1.md)): no
  Rust mileage plus an iteration-first year; Go dropped; Nuitka
  standalone compile guardrail in CI from scaffolding onward; port kept
  optional via language-external contracts.
- [The v1 cut](issues/04-the-v1-cut.md) — wider than proposed: sqlite +
  folder backends (ipfs deferred), all six built-ins, both bootstraps
  with `pixi-install` added by design amendment, copier via both routes
  in the acceptance bar, GC and drift and detached secrets in, public
  SDK dogfooded by the standard plugins; uv-python and the secretspec
  resolver deferred.
- [Normative wire schemas](issues/05-normative-wire-schemas.md) —
  DAG-JSON wire over a DAG-CBOR store; the derivation is a standalone
  document whose CID is the derivation hash (provenance = pure links);
  flat claims, explicit secret `shape`, name-speaking resolution
  document, kind-keyed inputs; golden fixtures with real CIDs
  committed; a second adapter gap closed (node-supplied `effect` for
  `command`, design amended).
- [CLI surface v1](issues/06-cli-surface-v1.md) — all eight points
  ratified: `heal` is the verb (day-1 = day-2 from zero), `status`
  heals pures to name the exact checkpoint set, day2-style checkpoint
  prompt, name-first output, paste-ready ambiguity fix, 0/1/2 exit
  contract, `show` + `store cat` inspection, verb inventory final.
- [Stack and libraries](issues/07-stack-and-libraries.md) — libipld in
  production with the hashberg pair cross-checking every golden fixture
  in tests; click + rich; dataclasses + explicit codecs (no validation
  framework); Python ≥3.12; stdlib sqlite3/subprocess/logging; dulwich;
  audit log = schema-versioned JSON-lines prepared for external
  consumption.
- [Package layout and module seams](issues/08-package-layout-and-module-seams.md)
  — nine modules with the §7 in/out line as a package boundary
  (store vs `state`); built-ins in-process behind the same document
  interface (two runner adapters); standard plugins in-repo under
  `plugins/`; public surface = CLI + sdk only; names are glossary
  terms. Layout doc in assets.
- [Testing strategy](issues/10-testing-strategy.md) — /tdd post-
  skeleton, test-along skeleton; seam-first tests with real
  collaborators and no internal mocks; top-level `conformance/` (CDDL +
  goldens, data-only) with triple golden assertions; dual-encoder
  cross-check on every test-minted document, example-based only;
  stdlib-Python fake plugins + misbehavior battery; parametrized store
  contract suite incl. gc; run-twice determinism helper; two-layer
  secrets canary with vacuity guard; linux-only CI over Python 3.12→
  latest stable; no coverage gate. Testing doc in assets.
- [Repo scaffolding](issues/11-repo-scaffolding.md) — template applied
  (uv, hatch git-tag versioning, justfile, pre-commit, CI): nine module
  packages + plugins/ + mirrored tests/, pinned stack wired, `uv.lock`
  committed, conformance/ relocated to top level, guardrails workflow
  (golden regen-diff + Nuitka standalone) — all checks green locally;
  first Nuitka data point 41 s / 42 MB. CI pending the HITL push to
  the new `freckles-dev/freckles` repo.
- [Packaging and distribution](issues/09-packaging-and-distribution.md)
  — Nuitka onefile is the released artifact (PyApp-embed the named
  fallback with a CI-fired trigger); binary-first install story via
  GitHub Releases + SHA256SUMS (pinned URL + checksum = complete
  install), PyPI and conda riding along; linux x86_64 + aarch64 at v1
  (macOS/Windows binaries deferred); tag-gated release matrix in the
  project-owned workflow, built post-skeleton per Milestones; guardrail
  switched to onefile; hidden CI-only `selftest` grows with the organs
  (sqlite, dulwich).
- [Walking skeleton](issues/12-walking-skeleton.md) — the loop runs:
  resolve → run → heal on a real CIDv1 sqlite store, both runner
  adapters live (in-process built-ins + spawned wire-speaking fakes),
  checkpoint set and `prior:` proven under the suite and by hand
  (transcript in assets); the walk mints a golden-checked derivation.
  Frictions fed back: the source-rerun rule (design.md §8 amendment
  proposed, awaiting ratification), pyyaml stack addendum, and the
  plugin-content-ingestion fog patch.
- [Milestones to v1](issues/13-milestones-to-v1.md) — **the map's
  terminal decision, resolved: the map is complete.** Nine milestones
  ([docs/milestones-v1.md](../../docs/milestones-v1.md), GitHub issues
  #1–#9): CLI → secrets → persistence → drift → plugin mechanics/SDK →
  mise route → pixi leg → late imports → release; /tdd drives; the
  acceptance bar is a tag-gating workflow; the source-rerun amendment
  ratified into design.md §8; all remaining fog dispatched (ergonomics
  and ingestion into M5, runtime limits and parallelism out of v1 with
  the recorded contingency trigger).

## Not yet specified

None — the map is complete (Milestones to v1, 2026-08-24). The last
patches graduated into the milestone plan: plugin-author ergonomics and
plugin content ingestion into milestone 5 (Plugin mechanics + SDK).

## Out of scope

- The catalog + rosekube migration effort, including running the real
  rosekube chain as acceptance — its own map, per the design map.
- The formal specification set — its own effort.
- Multi-machine sharing (store sync, the IPFS backend's purpose, team
  keys, provider auth) — inherited deferral.
- Performance optimization beyond what the skeleton and acceptance chain
  need.
- Plugin runtime limits (timeouts, resource caps) — no design semantics;
  ruled out of v1 by Milestones to v1 (post-v1 backlog in the plan doc).
- Parallel/concurrent node execution — sequential v1 stands; out unless
  the plan doc's recorded contingency fires ("if the acceptance chain
  drags").

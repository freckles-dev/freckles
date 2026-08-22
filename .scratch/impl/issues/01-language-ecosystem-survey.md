# Language ecosystem survey

Type: research
Status: resolved
Findings: branch `research/language-ecosystems`, file
`docs/research/language-ecosystems.md` (resolved 2026-08-22; read via
`git show research/language-ecosystems:docs/research/language-ecosystems.md`)

## Question

For each candidate implementation language — **Python, Go, Rust** —
establish from primary sources the v1-critical ecosystem facts, feeding
the Implementation language decision:

- **DAG-CBOR + CIDv1**: libraries producing spec-strict DAG-CBOR
  (beware: RFC 7049 length-first key sorting, not RFC 8949 bytewise —
  see the CAS survey's caveat) and CIDv1/multihash; maturity,
  maintenance, and whether golden-CID conformance against Kubo
  `block/put` is attainable. The existing survey
  (`docs/research/cas-survey.md` on branch `research/cas-survey`, §
  Python) already covers Python — build on it, don't redo it.
- **Embedded git fetch**: pinned-commit fetch over smart HTTP without a
  host `git` (dulwich / go-git / gitoxide): shallow fetch of one commit,
  auth stories (HTTPS token; SSH state of play), binary-size cost. This
  backs the built-in `import-git` (design.md §6: host git would defeat
  the tier).
- **Single-binary distribution**: current state per language — Python:
  PyApp / PyInstaller / shiv or successors; Go/Rust: native. Sizes,
  cross-compilation for linux x86_64/aarch64, build-toolchain burden.
- **sqlite**: bindings quality, blob streaming, WAL behavior.
- **Process-protocol ergonomics**: spawning plugins, stdio document
  exchange, environment scrubbing, PATH construction.
- **CLI library maturity** (arg parsing, rich terminal output).

Deliverable: a comparison table plus per-language narrative with a
recommendation, all claims cited to primary sources; unverifiable facts
flagged. The *decision* belongs to Implementation language, not this
survey.

## Answer

Full findings: `docs/research/language-ecosystems.md` on branch
`research/language-ecosystems` (503 lines, all claims cited to primary
sources, resolved 2026-08-22; eight facts flagged unverified/inferred in
its final section).

- **DAG-CBOR + CIDv1**: all three candidates have a conformant encoder,
  RFC 7049 length-first key sorting verified in actual source — Python
  `libipld` 3.4.1 (Rust-backed; the pure-Python `dag-cbor`/`multiformats`
  pair is frozen since 2023), Go `go-ipld-prime` v0.24.0 (the exact
  library Kubo pins, so golden-CID by construction), Rust `ipld-core` +
  `serde_ipld_dagcbor` (the old `libipld` crate is deprecated).
- **Embedded git fetch** (the built-in `import-git`): dulwich (Python,
  very active) and gix (Rust, cargo's git engine) both do depth-1
  pinned-commit fetch over smart HTTP with token auth; **go-git cannot**
  — no protocol v2, no non-tip SHA wants — a structural misfit for
  pinned-commit imports.
- **Single binary**: native + cross-compiling in Go and Rust (proxies:
  flux 24.8 MB, jj 10.7 MB compressed); Python has no native story —
  PyApp embed ≈55–58 MB, or a ~2 MB launcher that phones home on first
  run; uv calls standalone builds a wish, not a roadmap item.
- **sqlite**: Python stdlib is complete (`blobopen()` since 3.11, WAL,
  zero deps); Rust `rusqlite` complete with bundled amalgamation; Go
  fragmented (cgo vs. missing incremental-blob APIs).
- **Process protocol / CLI**: adequate everywhere; Python
  (click/typer + rich) has the best ergonomics; Go (cobra + charm) and
  Rust (clap + dialoguer/indicatif) are fine for the checkpoint UX.
- **Survey recommendation** (the *decision* is Implementation
  language's): **Rust**, priced honestly in velocity and 0.x API churn;
  **Python + PyApp(embed)** the defensible second if iteration speed
  outweighs distribution polish — noting Python's column already rides
  on Rust underneath (PyApp, libipld, dulwich's accelerators); **Go
  drops out** unless grilling surfaces something new, its two misfits
  (git fetch, sqlite blobs) sitting exactly on load-bearing built-ins.

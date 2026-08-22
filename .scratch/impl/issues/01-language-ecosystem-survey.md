# Language ecosystem survey

Type: research
Status: open
Claimed: research subagent, fired at charting (2026-08-22)
Findings: branch `research/language-ecosystems`, file
`docs/research/language-ecosystems.md`

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

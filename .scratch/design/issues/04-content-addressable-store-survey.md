# Content-addressable store survey

Type: research
Status: resolved
Findings: branch `research/cas-survey`, file `docs/research/cas-survey.md` (resolved 2026-08-20; read via `git show research/cas-survey:docs/research/cas-survey.md`)

## Question

Freckles wants pluggable content-addressable storage for configurations and
outcomes: a simple default backend (folder on disk, or sqlite), with IPFS as a
supported backend — generic and pluggable either way. Survey prior art and
constraints against primary sources.

To establish:

- Prior art in CAS design: git's object store, the Nix store, OSTree,
  IPFS/IPLD (blocks, CIDs, DAG-CBOR), content-addressed sqlite schemes. For
  each: addressing scheme, chunking/granularity, how small structured values
  (dicts!) vs file trees are stored, GC approach.
- Hash and format choices for IPFS compatibility: what it takes for a hash
  computed by a folder/sqlite backend to be *the same address* IPFS would
  assign (multihash, CID versions, codec choice, DAG-CBOR canonicalization) —
  versus accepting per-backend addresses with a mapping. What canonical
  serialization for dict-like outcome documents keeps hashing stable
  (DAG-CBOR? canonical JSON/JCS?).
- The minimal pluggable backend interface implied by the survey: put/get by
  hash, existence check, enumeration, mutable refs (name → hash), pinning/GC.
  What do the surveyed systems show is necessary vs accidental?
- Python ecosystem support: libraries for multihash/CID/DAG-CBOR, IPFS client
  APIs (HTTP API vs embedded), sqlite patterns for blob CAS.

Deliverable: a survey with a recommended addressing scheme + canonical
serialization, and a sketch of the minimal backend interface, feeding the
"Storage and addressing" grilling ticket.

## Answer

Full findings: `docs/research/cas-survey.md` on branch `research/cas-survey`
(545 lines, ~35 primary sources cited; four facts flagged [unverified] in
its §5.3).

- **Prior art converges**: git, Nix, OSTree, IPFS, and Fossil (the canonical
  sqlite CAS) all land on the same shape — immutable blocks + a thin mutable
  ref layer + reachability-from-roots GC. Nix's fingerprint hashing bakes in
  store-dir and name (deliberately avoided in the recommendation); git's
  SHA-1→SHA-256 transition is the cautionary tale for non-self-describing
  addresses; OSTree folds uid/gid/mode/xattrs into content hashes.
- **IPFS compatibility is cheap for documents, expensive for file trees**: a
  CID is fully determined by (version, codec, hash, block bytes), so a
  folder/sqlite backend that encodes dicts as spec-strict DAG-CBOR (codec
  0x71) with sha2-256 multihash gets byte-identical addresses to Kubo's
  `block/put` — no mapping table needed. But `ipfs add`-equality for files
  is a trap (UnixFS CIDs depend on chunker/raw-leaves settings; Kubo still
  defaults to CIDv0). Caveat: DAG-CBOR uses RFC 7049 length-first key
  sorting, not RFC 8949 bytewise — generic "deterministic CBOR" libraries
  are not conformant. JCS (RFC 8785) is the readable alternative but caps
  integers at 2^53 and can never share addresses with IPFS.
- **Recommended addressing**: CIDv1 + sha2-256; `dag-cbor` for documents,
  `raw` for capped opaque blobs (≤1 MiB); do **not** promise file-tree
  address compatibility with `ipfs add` — represent trees as freckles
  documents of (name → CID) pairs instead.
- **Recommended interface**: `put/get/has/cids` + **refs as the only mutable
  state, doubling as GC roots** (a separate pin API is accidental — git/Nix/
  OSTree all prove refs-as-roots suffices), plus `gc(extract_links, grace)`
  with a git-style prune grace period. Backends stay codec-ignorant.
- **Python**: hashberg `multiformats`/`dag-cbor` (stable) or Rust-backed
  `libipld` (active); `ipfshttpclient` is stale — use a small httpx adapter
  over Kubo's RPC API (`block/put`, sidestepping `dag/put` re-encoding
  uncertainty). Sqlite is comfortable as default backend (blobs to 1 GB,
  WAL = many readers/one writer, stdlib `blobopen()` since 3.11).

Adoption/trimming of this is Storage and addressing's decision.

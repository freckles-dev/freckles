# Native addresses are CIDv1 — DAG-CBOR documents, raw blobs

Status: accepted (2026-08-20)

Every store backend — sqlite (default), folder, ipfs — addresses content by
CIDv1 with sha2-256: spec-strict DAG-CBOR (codec 0x71) for documents
(claims, provenance records, resolution documents, tree listings), `raw`
(0x55) for opaque blobs capped at 1 MiB. Rejected alternatives: bare sha256
with export-time mapping (permanent mutable mapping state and
non-self-describing addresses — git's SHA-1→SHA-256 transition is the
cautionary tale), and JCS canonical JSON (2^53 integer ceiling, no native
bytes/links, can never share addresses with IPFS).

Consequences: a local store's addresses are byte-identical to what Kubo
assigns via `block/put`, so IPFS export needs no translation table — even
though freckles never requires IPFS. File trees deliberately get no
`ipfs add` compatibility (UnixFS addresses depend on import parameters); a
tree identity is a freckles document of (name → CID) pairs. Refs are the
only mutable state and double as GC roots; the derivation index is a
prunable local index, never a GC root.

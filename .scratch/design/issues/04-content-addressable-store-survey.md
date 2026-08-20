# Content-addressable store survey

Type: research
Status: open

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

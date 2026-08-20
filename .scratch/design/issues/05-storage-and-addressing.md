# Storage and addressing

Type: grilling
Status: resolved
Blocked by: 01, 04

## Question

Decide the storage model on top of the outcome definition (What is an
outcome?) and the CAS survey findings.

To resolve:

- What is stored content-addressably: user configurations, node configs,
  outcome documents, rendered file trees, transformer plugins themselves?
  The brief says "store our configuration content-addressable" — draw the
  exact line.
- The addressing scheme and canonical serialization (adopt or reject the
  survey's recommendation; IPFS-compatible addresses vs backend-local ones).
- The mutable layer over immutable hashes: how humans name things ("my
  staging cluster", "latest config") — refs? a root document? — and where
  mutability is allowed at all.
- The backend plugin interface (adopt/trim the survey's sketch): folder,
  sqlite, ipfs as the initial set.
- What replaces the vision doc's lockfile-and-artifact-store pair in this
  model, if anything.

Run /grilling and /domain-modeling. Grill against vision.md §8 (catalog
pinning) and open question 6 (artifact store).

## Answer

Resolved 2026-08-20 over two grilling rounds; every point explicitly
adopted by Markus. Assets:
[ADR 0003](../../../docs/adr/0003-cidv1-addressing.md), glossary terms in
[CONTEXT.md](../../../CONTEXT.md), full survey on branch
`research/cas-survey` (ticket 04).

1. **Addressing** — survey §5.1 adopted wholesale: CIDv1 + sha2-256 as the
   native address in every backend; spec-strict DAG-CBOR documents with CID
   links; `raw` blobs capped at 1 MiB (larger content = list-of-blocks
   document); base32 string form. No `ipfs add` compatibility for file
   trees — a tree is a freckles document of (name → CID) pairs. IPFS export
   = `block/put` + assert equal CID.
2. **The in/out line** — in the CAS: claims, provenance records,
   source-imported content (tree documents + raw blocks), resolution
   documents. Out: annotations (local mutable index keyed by claim CID),
   the audit log (local append-only), the user's working-copy
   configuration, realized environments and other local state, and plugin
   content (door open — The plugin contract).
3. **Mutable layer** — refs are the only mutable state and double as GC
   roots. Namespaces: `cfg/<config>/current` → resolution document;
   `cfg/<config>/nodes/<node>` → the node's current claim CID. The
   derivation index (derivation hash → claim CID) is a separate, prunable,
   rebuildable local index — deliberately *not* refs, so cache entries
   never pin outcomes forever. History retention (node history chains,
   old resolution documents) → Effects and day-2.
4. **Resolution document** replaces the vision doc's lockfile-and-artifact-
   store pair: a content-addressed snapshot of the resolved run — config
   snapshot CID, nodes with resolved (post-inference) edges, operation
   plugin + version per node, consumed-claim wiring. Unchanged inputs
   re-resolve to the same CID; day-2 diffing compares two resolution
   documents (usage → Effects and day-2).
5. **Backend interface** — survey §5.2 adopted: `put/get/has/cids`,
   `set_ref/get_ref/refs`, `gc(extract_links, grace≈14d)`; backends
   codec-ignorant. Initial backends: **sqlite (default)**, folder
   (inspection/debugging), ipfs (thin Kubo-RPC adapter; refs → pins).
   Library choice (libipld vs hashberg pair) left to implementation.
6. **Store scope** — one per-user store, refs namespaced per configuration:
   sharing is the point of content addressing (claims and the derivation
   cache dedup across configurations). Markus's caveat recorded: re-think
   if per-config-store use cases emerge; the interface keeps that cheap (a
   store is just a path).

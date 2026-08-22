# Stack and libraries

Type: grilling
Status: open
Blocked by: 02

## Question

Given the language, pin the concrete v1 stack:

- DAG-CBOR/CID library (Python: hashberg `multiformats`/`dag-cbor` vs
  `libipld` — CAS survey left this to implementation; other languages
  per the Language ecosystem survey). Acceptance: a golden-CID check —
  a known claim document must produce the known CID.
- sqlite access layer (blob streaming, WAL).
- Git-fetch library for built-in `import-git` (embedded, no host git —
  design.md §6 consequence).
- CLI framework; schema/validation approach for wire documents;
  subprocess handling for the runner; logging.
- What stays deliberately unpinned until first code.

Run /grilling and /domain-modeling.

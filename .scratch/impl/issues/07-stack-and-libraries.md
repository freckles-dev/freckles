# Stack and libraries

Type: grilling
Status: resolved
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

## Answer

Resolved 2026-08-22 in one grilling round; evidence base: the language
ecosystem survey §2 (branch `research/language-ecosystems`).

1. **DAG-CBOR/CID: `libipld` in production, the hashberg
   `dag-cbor`+`multiformats` pair as a dev-dependency cross-check** —
   the test suite encodes every golden fixture with both and asserts
   identical bytes and CIDs (two independent implementations agreeing),
   which also proves the libipld wheel survives Nuitka packaging.
2. **CLI: click + rich, no typer** — seven ratified verbs don't need a
   layer of indirection; `click.confirm` carries the checkpoint prompt.
3. **Document model: dataclasses + a small explicit codec module**
   written against the CDDL; no validation framework — claims are open
   maps, and the golden fixtures carry the correctness burden.
4. **Python floor: ≥3.12.**
5. **Diagnostics: stdlib `logging` + rich handler. Audit log:
   append-only JSON-lines, prepared for consumption** (Markus's
   framing): each record schema-versioned with a documented field set
   (derivation + claim CIDs, exit code, duration, resolved secret
   names) so external tooling can consume it. The design invariant is
   untouched — never consumed by DAG operations. The record schema is
   written when the audit milestone lands.
6. **Confirmed as pinned**: dulwich (HTTPS-token first; the SSH
   transport choice — host `ssh` vs paramiko extra — deferred to the
   import-git milestone), stdlib `sqlite3`, stdlib `subprocess`;
   pytest expected by Testing strategy; textual/TUI not in v1.

Deliberately unpinned: exact dependency versions (Repo scaffolding),
the dulwich SSH vendor, the final audit-record field list.

# freckles v1 — package layout and module seams

Wayfinder ticket 08, resolved 2026-08-22. Vocabulary per the
codebase-design skill: deep modules, seams, adapters. Module names are
glossary terms; the design doc's §7 in/out line is a package boundary.

```
src/freckles/
  documents/   value model + codecs
  store/       the CAS + refs (immutable — the §7 "in" side)
  state/       machine-local mutable (the §7 "out" side)
  resolver/    configuration -> resolution document
  runner/      one node run, end to end
  heal/        the topological walk
  builtins/    the six built-ins
  sdk/         the public plugin SDK
  cli/         click commands
plugins/       the five standard plugins (standalone SDK-consuming
               scripts; built and published as plugin claims by CI)
tests/
```

## Interfaces (the deep-module contracts)

- **documents** — typed dataclasses for claim, outcome, derivation,
  provenance, resolution, tree, request/outcome/error; codecs:
  `encode(doc) -> (bytes, CID)`, `decode`, `to_wire`/`from_wire`
  (DAG-JSON). Nothing outside this module touches DAG-CBOR, CIDs, or
  libipld.
- **store** — backend seam: `put/get/has/cids`, `set_ref/get_ref/refs`,
  `gc(extract_links, grace)`. Two adapters (sqlite, folder) — a real
  seam by the two-adapter test. Backends stay codec-ignorant.
- **state** — `AnnotationsIndex` (read/write, distrust marks,
  secret-aware redaction), `DerivationIndex` (lookup/record/prune —
  never a GC root), `AuditLog` (append one schema-versioned JSON-lines
  record per run).
- **resolver** — `resolve(config_dir) -> Resolution`: loading, edge
  inference, ambiguity hard errors, one call deep.
- **runner** — `run(resolved_node, inputs, prior, secrets) -> Outcome`:
  workspace materialization, env scrub, PATH construction, the wire
  protocol, the plaintext boundary (ADR 0005). Execution seam with two
  adapters: **in-process** (built-ins — trusted core behind the same
  Request/Outcome documents) and **process** (acquired plugins, spawned,
  speaking DAG-JSON on stdio). `command`'s *wrapped* invocation is a
  real subprocess with full physical enforcement either way.
- **heal** — `walk(resolution, store, state, runner, confirm) ->
  report`: derivation computation, index lookup, pure auto-heal,
  checkpoint set, distrust handling. `confirm` is an injected callback:
  the CLI passes the interactive prompt, `--yes` passes const-true,
  tests pass scripted answers.
- **cli** — thin: each verb composes the modules above; no logic that
  couldn't be driven from Python.

## Public surface

Stable in v1: the CLI and `freckles.sdk`. Everything else is declared
internal/unstable — seams may move as the skeleton teaches us.

## What the walking skeleton instantiates

documents, store (sqlite adapter), state (derivation index +
annotations), resolver, runner (both adapters — built-ins in-process,
plus one spawned fake plugin speaking the wire, so the process path is
real from day one), heal, and a minimal dev entry point. Not in the
skeleton: folder adapter, secrets, bootstraps, gc, CLI polish.

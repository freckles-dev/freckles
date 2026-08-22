# freckles v1 is implemented in Python

Status: accepted (2026-08-22)

The vision doc called freckles "a Python framework" by inheritance; the
implementation map made the language an explicit decision, fed by the
language ecosystem survey (branch `research/language-ecosystems`). The
survey's merit recommendation was Rust — strong on every axis, priced
in velocity and 0.x API churn; Go fell to structural misfits on
load-bearing built-ins (go-git cannot shallow-fetch a non-tip pinned
commit; sqlite forces cgo or missing blob APIs). We chose Python: the
sole maintainer has no Rust mileage, and v1's first year optimizes for
proving a fresh design — compounding a novel model with a novel
language risks the walking skeleton — while Python's column is complete
today (Rust-backed libipld for spec-strict DAG-CBOR/CIDv1, dulwich for
the embedded git fetch, stdlib sqlite with incremental blob I/O,
click/typer + rich for the checkpoint UX).

Consequences: distribution is Python's weak axis, so single-binary
viability is enforced empirically, not assumed — a Nuitka standalone
compile + smoke-run joins CI from repo scaffolding onward, with
PyApp(embed, ~55 MB) as the surveyed fallback and the
runtime-bootstrapping launcher variant ruled out; the
frkl-dev/python-project-template drives scaffolding. The choice is
deliberately port-optional: freckles' contracts (DAG-CBOR documents,
golden CIDs, the process protocol) live outside the language, so a
later port is verifiable against fixtures rather than folklore.
Revisit if the packaging guardrail fails permanently or a measured
performance ceiling appears.

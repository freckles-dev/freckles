# Implementation language

Type: grilling
Status: claimed (markus, 2026-08-22)
Blocked by: 01

## Question

Decide freckles' implementation language. "Python framework" was
inherited from the vision doc and never decided; ADR 0004's process
protocol decouples plugin authorship from the framework's language, so
the choice is freer than the vision assumed.

Candidates: **Python** (incumbent — Markus's tooling, template, and
productivity ecosystem), **Go**, **Rust**.

Weigh, against the Language ecosystem survey's findings:

- The published executable artifact (charter fact: freckles ships as
  one) — native in Go/Rust, machinery in Python.
- The embedded git fetch for built-in `import-git`.
- DAG-CBOR/CID fidelity — golden-CID conformance is non-negotiable.
- Development velocity for a single primary maintainer vs. long-term
  maintenance and contributor surface.
- The fetch-verify bootstrap story: freckles should be installable the
  way it installs tools (pinned URL + checksum).

Consequences to record either way: if Python, the map Notes' template
(frkl-dev/python-project-template) applies to Repo scaffolding; if not,
Stack and libraries absorbs finding the equivalent tooling.

Run /grilling and /domain-modeling.

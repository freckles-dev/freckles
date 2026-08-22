# Implementation language

Type: grilling
Status: resolved
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

## Answer

Resolved 2026-08-22 in one grilling round plus confirmation; asset:
[ADR 0006](../../../docs/adr/0006-python-for-v1.md).

1. **Python.** Decisive grounds: no Rust mileage on the team of one —
   compounding a novel design with a novel language risks the walking
   skeleton; the first year optimizes for design-proving iteration; the
   fat self-contained artifact is culturally acceptable (the
   runtime-bootstrapping launcher variant is ruled out); contributor
   surface carries low weight (plugins are language-agnostic under the
   process protocol either way).
2. **Go dropped** per the survey's structural misfits — nothing saved
   it in grilling.
3. **Rust declined on fit, not merit** — the survey's recommendation
   stands recorded; the port-optionality stance (contracts live outside
   the language, ports verify against golden-CID fixtures) is what
   makes iteration-first safe, per ADR 0006.
4. **Nuitka guardrail** (Markus's Q4 amendment): a Nuitka standalone
   compile + smoke-run of the base package joins CI from Repo
   scaffolding onward and is hardened by Walking skeleton; Packaging
   and distribution gains Nuitka as a named candidate, with PyApp
   (embed) the surveyed fallback.
5. Consequences applied: the frkl-dev/python-project-template drives
   Repo scaffolding; the survey's Python column (libipld, dulwich,
   stdlib sqlite, click/typer + rich) is the starting slate for Stack
   and libraries, which also sets the version floor (≥3.12 default).

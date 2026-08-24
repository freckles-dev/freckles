# Packaging and distribution

Type: grilling
Status: claimed (markus, 2026-08-24)
Blocked by: 02

## Question

The published executable artifact: decide v1's distribution.

- Single-binary route: **Nuitka standalone** (named by the
  Implementation language resolution — its CI guardrail, running from
  Repo scaffolding onward, supplies the empirical data) vs **PyApp
  embed** (the survey's fallback); the runtime-bootstrapping launcher
  variant is ruled out. Plus the language-native channel (PyPI /
  uv tool) alongside or later.
- Platforms: linux x86_64 first? aarch64?
- Versioning and release automation (if Python: the template's hatch +
  git-tag scheme and CI).
- How the embedded git fetch and sqlite ride along in the frozen
  artifact.
- Constraint: the fetch-verify story applies to freckles itself — a
  pinned URL + checksum must be a complete install.

Run /grilling and /domain-modeling.

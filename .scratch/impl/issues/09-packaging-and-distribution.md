# Packaging and distribution

Type: grilling
Status: open
Blocked by: 02

## Question

The published executable artifact: decide v1's distribution.

- Single-binary route per the chosen language (Python: PyApp /
  PyInstaller / successor per the Language ecosystem survey; Go/Rust:
  native) — plus the language-native channel (PyPI / uv tool, go
  install, cargo) alongside or later.
- Platforms: linux x86_64 first? aarch64?
- Versioning and release automation (if Python: the template's hatch +
  git-tag scheme and CI).
- How the embedded git fetch and sqlite ride along in the frozen
  artifact.
- Constraint: the fetch-verify story applies to freckles itself — a
  pinned URL + checksum must be a complete install.

Run /grilling and /domain-modeling.

# Packaging and distribution

Type: grilling
Status: resolved
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

## Answer

Resolved 2026-08-24 in one grilling round; all six points ratified by
Markus. Evidence: the scaffolding guardrail's local data plus the
language ecosystem survey §2.3.

1. **Nuitka is the single-binary route.** PyApp-embed stays the named
   fallback with an explicit trigger: switch only if Nuitka cannot
   package a dependency the v1 cut needs, or a platform build breaks
   and resists a fix — the CI guardrail exists to fire that trigger
   early. Empirical basis: standalone 41 s / 42 MB dist; **onefile
   66 s compile, an 11.8 MB binary, ~0.2 s startup** (vs PyApp-embed's
   ~55 MB compressed plus a Rust toolchain in CI).
2. **The released artifact is Nuitka onefile** — one pinned URL names
   one executable with its checksum beside it, satisfying the
   fetch-verify complete-install constraint verbatim. The guardrail
   was switched to onefile in this resolution (CI proves the shipped
   mode).
3. **Binary platforms at v1: linux x86_64 + aarch64** (GitHub's native
   arm runners make the second leg one matrix entry). macOS arm64 is a
   fast-follow when a real user asks — it drags signing/notarization
   in, deliberately not decided speculatively. No Windows binaries in
   v1; PyPI is the Windows story. Test matrices on darwin/windows
   continue regardless.
4. **Binary-first install story, three channels**: the GitHub Release
   binary + `SHA256SUMS` is the canonical documented install; PyPI
   (wheel/sdist, `uv tool install freckles`) and conda (anaconda org
   `freckles`) ride along, already wired by scaffolding. The uv-python
   route stays deferred per The v1 cut.
5. **Release pipeline**: on version tags, a matrix job in the
   project-owned workflow (never template-owned files) compiles
   onefile per platform, names artifacts
   `freckles-<version>-linux-<arch>`, emits `SHA256SUMS`, attaches all
   to the GitHub Release, and gates on the tag's test/typecheck/lint
   jobs — same gating as the PyPI job. Built post-skeleton, scheduled
   by Milestones to v1. **No signing/attestation in v1**; the checksum
   file is the integrity story (sigstore/SLSA deliberately deferred).
6. **Proof the organs ride along**: a **hidden** `selftest` command
   (click `hidden=True`, CI-only, invisible in `--help` — ruled
   outside the ratified eight-verb CLI surface) exercises each frozen
   dependency and grows with the surface: sqlite3 + libipld when the
   walking skeleton lands, dulwich when import-git lands. The
   guardrail smoke calls it once it exists.

Deliberately unpinned: exact nuitka flags beyond `--onefile`, the
onefile extraction-cache spec, release-artifact naming details.

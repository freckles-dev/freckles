# Repo scaffolding

Type: task
Status: resolved
Blocked by: 02, 07

## Question

Scaffold the implementation into this repo, cohabiting with `docs/` and
`.scratch/`:

- If the language is Python: apply
  [frkl-dev/python-project-template](https://github.com/frkl-dev/python-project-template)
  (uv; hatch build/publish with git-tag versioning; CI for
  tests/lint/typecheck; wheel/sdist + conda; justfile). Otherwise: the
  chosen language's equivalent, per Stack and libraries.
- Wire the pinned stack dependencies; empty package skeleton; CI green
  on an empty test suite — including the **Nuitka guardrail**: a
  standalone compile + smoke-run of the base package (Implementation
  language rider, ADR 0006).

The answer records what now exists: paths, the commands that work
(`just test`, etc.), CI status — the facts Walking skeleton builds on.

## Answer

Resolved 2026-08-24 (scaffolding commit `7a43387` on `develop`).
Template applied via copier (answers file committed, so
`just update-template` works). Markus's calls during the task:
**AGPL-3.0-only** (may change later), GitHub org **freckles-dev**,
anaconda user **freckles** (conda packaging in), and the template's
**develop-flow branching** — `develop` is the working branch from here;
tags release and merge to `main`.

**What exists now**

- `src/freckles/` with the nine layout-doc modules (glossary-named,
  docstrings carry each contract); `freckles.cli:main` is the `freckles`
  console script (click group, `--version` answers).
- `plugins/` (standard-plugin home, README stub), `tests/` mirroring the
  modules plus `tests/e2e/`, smoke tests green.
- `conformance/` at top level — store.cddl, wire.cddl, golden fixtures,
  `make_golden.py` — relocated from the ticket-05 assets per Testing
  strategy; regeneration verified byte-identical.
- Pinned stack wired: `click`, `dulwich`, `libipld`, `rich` in
  production (mirrored into `conda.recipe/recipe.yaml`; libipld exists
  on conda-forge, 3.4.1); hashberg `dag-cbor` + `multiformats[full]` as
  dev cross-check pair; `nuitka` + `patchelf` in a separate `compile`
  group. `uv.lock` committed. Test markers removed per Testing
  strategy (one undivided suite; `--strict-markers` kept).
- CI: template workflows (linux/darwin/windows tests 3.12–3.14,
  typecheck, lint, commitlint, build, tag-triggered release) plus the
  project-owned `freckles-guardrails.yaml` — golden regenerate-and-diff
  and the ADR 0006 Nuitka standalone compile + smoke run — kept outside
  template-owned files so `copier update` never touches it.

**Commands that work** (all verified): `just tests` / `just test <pat>`
/ `just typecheck` / `just typecheck-ty` / `just lint` / `just format`
/ `just pre-commit` / `just build-conda`; `uv build` (wheel + sdist,
git-derived version); `uv run conformance/golden/make_golden.py`;
`uv sync --group compile && uv run nuitka --standalone
--assume-yes-for-downloads --output-dir=build/nuitka
scripts/nuitka_entry.py`.

**First Nuitka data point** (for Packaging and distribution): standalone
compile 41 s wall / 2 m 19 s CPU on this machine, 42 MB dist directory,
binary answers `--version` with libipld's compiled extension packaged.

**CI status: not yet run — no git remote exists.** HITL handoff:
create `freckles-dev/freckles` on GitHub, push `main` and `develop`
(make `develop` the default working branch), then check the Actions
tab. `TODO.md` (template-generated) covers PyPI trusted publishing and
the `ANACONDA_PUSH_TOKEN` secret — release-time concerns, not needed
for green CI.

# Repo scaffolding

Type: task
Status: open
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

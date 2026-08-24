---
name: run-demo
description: Launch freckles against a scratch demo chain. Use when asked to run, demo, or smoke the real CLI, or to see a change working outside the test suite.
---

# Demo chain through the real CLI

Everything happens in the scratchpad: the configuration is the current
directory, and the store goes wherever `FRECKLES_DATA_DIR` points.

## Steps

1. Make `demo/` and `data/` in the scratchpad; write the chain below as
   `demo/freckles.yaml` plus `demo/cluster.yaml`; `cd demo` and
   `export FRECKLES_DATA_DIR=../data`.
2. Drive the verbs with `uv --project <repo> run freckles …`:
   `heal --yes` (day 1 from zero) → `status` (current, exit 0) → edit
   `cluster.yaml` → `status` (names the checkpoint set, exit 2) →
   `echo y | … heal` (the R3 prompt) → `show deploy/site` →
   `store cat <cid>` with a CID from `resolve`.
3. Read the run against the exit contract — 0 current · 1 error ·
   2 not current — and the ratified transcript
   (`.scratch/impl/assets/06-cli-surface/transcript.md`) for the intended
   feel; its literal text is illustrative, the decisions are binding.

## The chain (verified working)

```yaml
# freckles.yaml
nodes:
  values/apps:
    op: import-values
    config: {file: cluster.yaml, key: apps}
  render/site:
    op: command
    consumes: [values]
    config:
      kind: file-tree
      effect: pure
      cmd: [sh, -c, "mkdir -p out && cp inputs/values out/site.yaml"]
  deploy/site:
    op: command
    consumes: [file-tree]
    config:
      kind: deployed-site
      effect: effectful
      cmd: [sh, -c, "cat inputs/file-tree/site.yaml > /dev/null"]
      claim: {site: demo}
```

```yaml
# cluster.yaml — edit `enabled` to make the chain stale
apps:
  karakeep:
    enabled: false
```

## With a secret

Add an `import-sops` node and a `secret-env` on the deploy (see
`tests/cli/conftest.py` `SECRET_CHAIN` for a verified shape). Mint the
sops file and age key the way `tests/conftest.py`'s `sops_lab` fixture
does — it is the reference implementation for encrypting hermetically —
and point `SOPS_AGE_KEY_FILE` at the generated identity.

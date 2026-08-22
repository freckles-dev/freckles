# The freckles v1 CLI — agreed surface (wayfinder ticket 06)

Ratified 2026-08-22, all eight reaction points as embodied. Nothing here
runs; the *decisions* (verbs, prompt shape, exit codes, redaction) are
binding for v1, the literal output text stays illustrative. The chain is the walking-skeleton chain plus one secret
(`values/apps` → `render/site` → `deploy/site`, with
`secrets/deploy-token` consumed by the deploy). Names and vocabulary are
CONTEXT.md's; CIDs are abbreviated `bafyre…xxx` per reaction point R4.

## Scene 1 — first heal (day-1 is just day-2 from zero)

```console
$ freckles heal
resolving… ok  resolution bafyre…5da  (4 nodes)
stale: 4 of 4 (first run — no claims yet)

  values/apps           import-values   pure       healed → bafyre…u4m
  secrets/deploy-token  import-sops     pure       healed → bafyre…a7e
  render/site           command         pure       healed → bafyre…9dq

checkpoint set: 1

  ▶ deploy/site  (command · effectful)
      creates      deployed-site  (first claim — nothing superseded)
      receives plaintext secrets: deploy-token
      proceed? [y/N] y
      running… ok → deployed-site bafyre…x2f

deployment current — checkpoint set empty.
```

There is no `install`/`up`/`apply`: healing from zero *is* the first
deployment (R1).

## Scene 2 — status when current

```console
$ freckles status
resolution bafyre…5da (unchanged)
4 nodes, all current — checkpoint set empty.

$ echo $?
0
```

## Scene 3 — a values edit; status names the exact checkpoint set

```console
$ $EDITOR cluster.yaml        # enable karakeep

$ freckles status
re-resolving… ok  resolution bafyre…hh2  (config snapshot changed)
pure heal: values/apps → bafyre…22a, render/site → bafyre…9mb

checkpoint set: 1
  deploy/site   stale — input file-tree changed (render/site)

$ echo $?
2
```

`status` walks the DAG and heals stale *pure* nodes on the spot — safe
by design, and the only way to name the checkpoint set exactly, since
downstream derivations need upstream claims (R2). `--frozen` reports
without deriving:

```console
$ freckles status --frozen
stale: values/apps; downstream undetermined until pure heal
```

```console
$ freckles heal
checkpoint set: 1

  ▶ deploy/site  (command · effectful)
      supersedes   deployed-site bafyre…x2f
      receives plaintext secrets: deploy-token
      prior        available (claim + annotations)
      proceed? [y/N] y
      running… ok → deployed-site bafyre…m1q

deployment current — checkpoint set empty.
```

## Scene 4 — ambiguity is a hard error with a ready-to-paste fix

```console
$ freckles status
re-resolving… error

ambiguous edge: render/site consumes kind `values`, 2 providers:
    values/apps
    values/cluster
fix: select one explicitly in render/site:
    use: { values: values/apps }

$ echo $?
1
```

## Scene 5 — secret rotation; the extensional ripple-stop, visible

```console
$ sops set secrets.sops.yaml '["deploy_token"]' '"nt-9xk…"'

$ freckles heal
pure heal: secrets/deploy-token → bafyre…f31

checkpoint set: 1

  ▶ deploy/site  (command · effectful)
      supersedes   deployed-site bafyre…m1q
      receives plaintext secrets: deploy-token
      prior        available (claim + annotations)
      proceed? [y/N] y
      running… ok → deployed-site bafyre…m1q  (claim unchanged — ripple stops)

deployment current — checkpoint set empty.
```

## Scene 6 — drift: verify, distrust, heal

```console
$ freckles verify deploy/site
  deploy/site  verify → CONTRADICTED (health endpoint unreachable)
  claim bafyre…m1q marked distrusted — node stale.

$ freckles heal
checkpoint set: 1
  ▶ deploy/site …(as above)… ok → deployed-site bafyre…m1q
deployment current.
```

## Scene 7 — inspection: `show` (human, redacted) and `store cat` (raw)

```console
$ freckles show deploy/site
deploy/site   deployed-site   bafyre…m1q   current · trusted
claim
  kind: deployed-site
  url:  https://site.example
annotations (this machine)
  deployed_at:  2026-08-22T14:03:11Z
  admin_token:  <secret — not shown>
provenance    derivation bafyre…bhu  (command @ freckles 0.1.0)

$ freckles store cat bafyre…m1q      # raw DAG-JSON of any store document
{ "schema": 1, "kind": "deployed-site", "url": "https://site.example" }
```

## Scene 8 — gc

```console
$ freckles gc
refs: 9 roots · 31 blocks reachable
unreferenced: 7 (grace 14d: 5 kept, 2 collected)
freed 3.1 KiB
```

## Scene 9 — automation (auto-confirm is a deliberate opt-in)

```console
$ freckles heal --yes            # confirms every checkpoint; for CI
$ freckles status --check        # exit 0 current / 2 stale — no output
$ freckles status --check || notify "deployment stale"
```

## Exit codes (the whole contract)

| code | meaning |
|---|---|
| 0 | success; for `status`: deployment current |
| 1 | error — resolution failure (incl. ambiguity), plugin failure, bad usage |
| 2 | not current — checkpoint set non-empty, or a checkpoint was declined |

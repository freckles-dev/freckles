# PROTOTYPE — throwaway (wayfinder ticket 10). Day-2 deltas.

Two deltas, chosen to stress opposite properties: (A) a config change that
should ripple exactly one checkpoint; (B) a secret rotation that must ripple
*into* an effectful node and *stop* there. Staleness is always the same
question (Effects and day-2): **is the node's current claim the one its
current derivation produced?** — a derivation-index lookup, nothing more.

## Delta A — enable karakeep

Edit `cluster.yaml`: add `karakeep: { enabled: true }` under `apps:`.
Re-resolve → resolution document `bafy_RES_V2` (only the config snapshot CID
changed; every edge identical). Walk the derivation index:

| node                    | new derivation      | index lookup                | current claim         | stale? |
|-------------------------|---------------------|-----------------------------|-----------------------|--------|
| bootstrap, tools/*      | unchanged           | hit                         | unchanged             | no     |
| sources/values/cluster  | unchanged (`#cluster` untouched) | hit            | unchanged             | no     |
| sources/values/apps     | `drv_VAL_APPS_V2`   | miss → re-import (pure)     | `bafy_CLAIM_VAL_APPS_V2` | healed automatically |
| sources/secrets/*       | unchanged           | hit                         | unchanged             | no     |
| infra/staging           | unchanged — consumes cluster values, not apps | hit | `bafy_CLAIM_INFRA_V1` | **no** |
| render/flux-tree        | `drv_TREE_V2` (new apps claim input) | miss → re-render (pure) | `bafy_CLAIM_TREE_V2` (tree `bafy_TREE_FLUX_V2`, + `apps/karakeep/`) | healed automatically |
| k8s/flux-bootstrap      | unchanged           | hit                         | `bafy_CLAIM_GITOPS`   | **no** |
| k8s/push-config         | `drv_SYNCED_V2` (new tree claim input) | miss        | `bafy_CLAIM_SYNCED_V1` | **YES → checkpoint** |

Stale set: `{k8s/push-config}`. One confirmation, one `git push`, new claim
`bafy_CLAIM_SYNCED_V2` (commit `4c77aa1...`, tree `bafy_TREE_FLUX_V2`); Flux
does the rest. This reproduces vision §10 step 4's promise ("the only stale
execute stage is push repo") — but **only because the values were split**
(reaction point R2): with one coarse `config` claim, `infra/staging`'s
derivation would have changed too, and `tofu apply` would sit spuriously in
the stale set.

Refs after healing: `cfg/staging/current -> bafy_RES_V2`, apps /
render/flux-tree / push-config node refs advance; `bafy_CLAIM_SYNCED_V1`
and the old apps/tree claims become GC-fodder after grace.

## Delta B — rotate the Proxmox API token

Rotate in the Proxmox UI, then `sops set` the new value: new ciphertext →
`sources/secrets/proxmox-api-token` re-imports (pure) to claim
`bafy_CLAIM_SECRET_PROXMOX_V2`. Resolution → `bafy_RES_V3`.

| node                  | new derivation   | index lookup | stale?                 |
|-----------------------|------------------|--------------|------------------------|
| sources/secrets/proxmox-api-token | `drv_SECRET_PROXMOX_V2` | miss → re-import | healed automatically |
| infra/staging         | `drv_INFRA_V2` (new secret claim input) | miss | **YES → checkpoint** |
| everything else       | unchanged        | hit          | no                     |

The checkpoint prompt names the superseded claim and the plaintext access:

    node infra/staging (tofu-apply@0.4.2)
    supersedes: bafy_CLAIM_INFRA_V1 (talos-cluster staging)
    receives plaintext secrets: proxmox-api-token
    proceed? [y/N]

The re-run receives `prior:` (the old outcome, claim + annotations — the
`tf_workdir` makes tofu converge instead of recreate). The cluster is
unchanged, so the plugin returns **the same claim**: extensional addressing
(ADR 0001) means the outcome address is `bafy_CLAIM_INFRA_V1` again. A *new*
provenance record `bafy_PROV_INFRA_V2` records that the new derivation also
produces it; the index gains `drv_INFRA_V2 -> bafy_CLAIM_INFRA_V1`.

Downstream: `k8s/flux-bootstrap`'s derivation hashes its *input claim CIDs*
— all unchanged — so it is **not stale**. The ripple stops at the node that
actually consumed the rotated secret. (Intensional addressing would have
re-keyed the cluster claim here and marched the staleness wave through
flux-bootstrap and push-config for no reason — this delta is the concrete
case ADR 0001 was held open for, and it lands on the right side.)

Also updated by the re-run: `applied_at` and the (unchanged-in-content)
`kubeconfig` credential annotation; the audit log records the run with both
derivation and claim CIDs, names of resolved secrets, never values.

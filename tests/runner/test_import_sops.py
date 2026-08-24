"""import-sops (design.md §9): per-key ciphertext becomes a secret-value claim.

Extraction only — no decryption happens at import time, so these tests use a
sops-format file with prototype-style fake ENC values. Decryption is the
runner boundary's business (its own tests).
"""

from freckles.documents import ResolvedNode
from freckles.runner import run_node

IMPORT_SOPS = {"builtin": "import-sops", "freckles": "0.0.0-test"}

SOPS_FILE = """\
proxmox_api_token: ENC[AES256_GCM,data:9xK2mQ...,iv:Ub3f...,tag:pR8s...,type:str]
deploy_token: ENC[AES256_GCM,data:zQ4vLn...,iv:Rc8a...,tag:mW2d...,type:str]
sops:
    age:
        - recipient: age1testrecipient
          enc: |
            -----BEGIN AGE ENCRYPTED FILE-----
            fake
            -----END AGE ENCRYPTED FILE-----
    lastmodified: "2026-08-24T10:00:00Z"
    mac: ENC[AES256_GCM,data:fakemac...,type:str]
    version: 3.9.1
"""


def secret_node(**config_extra) -> ResolvedNode:
    return ResolvedNode(
        plugin=IMPORT_SOPS,
        produces="secret",
        effect="pure",
        config={"file": "secrets.sops.yaml", "key": "proxmox_api_token"} | config_extra,
        consumes={},
    )


def test_import_sops_mints_a_secret_value_claim(ctx, encode_checked):
    (ctx.config_dir / "secrets.sops.yaml").write_text(SOPS_FILE)

    outcome = run_node("secrets/proxmox-api-token", secret_node(), {}, ctx)

    claim = outcome.claim
    assert claim["kind"] == "secret"
    assert claim["shape"] == "value"
    assert claim["name"] == "proxmox-api-token"  # logical name, dash convention
    # identity is the ciphertext: exactly this key's ENC bytes, in the CAS
    ciphertext = ctx.store.get(claim["ciphertext"])
    assert (
        ciphertext == b"ENC[AES256_GCM,data:9xK2mQ...,iv:Ub3f...,tag:pR8s...,type:str]"
    )
    assert b"deploy_token" not in ciphertext  # granularity: one key only
    # machine-local realization facts, never identity
    assert outcome.annotations["imported_from"].endswith(
        "secrets.sops.yaml#proxmox_api_token"
    )
    encode_checked(claim)  # dual-encoder cross-check on the minted document


def test_detached_variant_same_claim_bytes_never_enter_the_cas(ctx):
    """store: false keeps the hash (and the rotation ripple) — not the bytes."""
    (ctx.config_dir / "secrets.sops.yaml").write_text(SOPS_FILE)

    detached = run_node("secrets/token", secret_node(store=False), {}, ctx)
    assert not ctx.store.has(detached.claim["ciphertext"])

    attached = run_node("secrets/token", secret_node(), {}, ctx)
    assert attached.claim == detached.claim  # detachment is store behavior only
    assert ctx.store.has(attached.claim["ciphertext"])


def test_import_sops_is_deterministic(ctx):
    """The run-twice determinism harness ("Testing strategy"), applied."""
    (ctx.config_dir / "secrets.sops.yaml").write_text(SOPS_FILE)

    first = run_node("secrets/token", secret_node(), {}, ctx)
    second = run_node("secrets/token", secret_node(), {}, ctx)
    assert first.claim == second.claim

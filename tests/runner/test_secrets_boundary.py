"""ADR 0005: plaintext exists only in the effectful request document, in memory.

Layer 1 of the secrets-boundary assertions ("Testing strategy"): unit tests
at the request-builder seam, with a real import and real decryption via the
hermetic sops lab.
"""

from freckles.documents import ResolvedNode
from freckles.runner import build_request, run_node

IMPORT_SOPS = {"builtin": "import-sops", "freckles": "0.0.0-test"}
COMMAND = {"builtin": "command", "freckles": "0.0.0-test"}


def imported_secret(ctx, sops_lab, plaintext: str) -> dict:
    """Run a real import-sops and shape its outcome as a request input entry."""
    sops_lab.encrypt(ctx.config_dir / "secrets.sops.yaml", {"deploy_token": plaintext})
    node = ResolvedNode(
        plugin=IMPORT_SOPS,
        produces="secret",
        effect="pure",
        config={"file": "secrets.sops.yaml", "key": "deploy_token"},
        consumes={},
    )
    outcome = run_node("secrets/deploy-token", node, {}, ctx)
    return {
        "cid": "bafyre-test",
        "claim": outcome.claim,
        "annotations": outcome.annotations,
    }


def consumer(effect: str) -> ResolvedNode:
    return ResolvedNode(
        plugin=COMMAND,
        produces="deployed-site",
        effect=effect,
        config={"kind": "deployed-site", "effect": effect, "cmd": ["true"]},
        consumes={"secret": "secrets/deploy-token"},
    )


def test_effectful_request_carries_resolved_plaintext(ctx, sops_lab):
    inputs = {"secret": imported_secret(ctx, sops_lab, "hunter2-plaintext")}

    request = build_request(
        "deploy/site", consumer("effectful"), inputs, "/ws", [], None
    )

    assert request["inputs"]["secret"]["resolved"] == {"value": "hunter2-plaintext"}


def test_pure_request_never_carries_plaintext(ctx, sops_lab):
    """Flow B: pure consumers get the ciphertext claim — nothing more."""
    inputs = {"secret": imported_secret(ctx, sops_lab, "hunter2-plaintext")}

    request = build_request("render/site", consumer("pure"), inputs, "/ws", [], None)

    entry = request["inputs"]["secret"]
    assert "resolved" not in entry
    assert "annotations" not in entry
    assert entry["claim"]["kind"] == "secret"  # the ciphertext claim itself flows


def test_reference_shape_fails_cleanly(ctx):
    """v1 resolves shape 'value' only; references are expressible, not runnable."""
    import pytest

    from freckles.runner import RunError

    reference = {
        "cid": "bafyre-test",
        "claim": {
            "schema": 1,
            "kind": "secret",
            "shape": "reference",
            "name": "vault-token",
        },
    }

    with pytest.raises(RunError, match="no resolver"):
        build_request(
            "deploy/site", consumer("effectful"), {"secret": reference}, "/ws", [], None
        )


def test_detached_secret_resolves_from_the_working_copy(ctx, sops_lab):
    """store: false changes CAS residency, never resolvability."""
    sops_lab.encrypt(ctx.config_dir / "secrets.sops.yaml", {"deploy_token": "det4ched"})
    node = ResolvedNode(
        plugin=IMPORT_SOPS,
        produces="secret",
        effect="pure",
        config={"file": "secrets.sops.yaml", "key": "deploy_token", "store": False},
        consumes={},
    )
    outcome = run_node("secrets/deploy-token", node, {}, ctx)
    inputs = {
        "secret": {
            "cid": "bafyre-test",
            "claim": outcome.claim,
            "annotations": outcome.annotations,
        }
    }

    request = build_request(
        "deploy/site", consumer("effectful"), inputs, "/ws", [], None
    )

    assert request["inputs"]["secret"]["resolved"] == {"value": "det4ched"}


def test_tampered_ciphertext_fails_authentication(ctx, sops_lab):
    """GCM + path AAD carry integrity (the MAC is a named v1 cut)."""
    import re

    import pytest

    from freckles.runner import RunError

    inputs = {"secret": imported_secret(ctx, sops_lab, "hunter2-plaintext")}
    source = ctx.config_dir / "secrets.sops.yaml"
    tampered = re.sub(
        r"data:[A-Za-z0-9+/=]+", "data:dGFtcGVyZWQtYnl0ZXM=", source.read_text()
    )
    source.write_text(tampered)

    with pytest.raises(RunError, match="authentication"):
        build_request("deploy/site", consumer("effectful"), inputs, "/ws", [], None)


def test_command_secret_env_hands_plaintext_to_the_wrapped_process(ctx, sops_lab):
    """The effectful command adapter: config-named env vars, in memory only."""
    inputs = {"secret": imported_secret(ctx, sops_lab, "hunter2-plaintext")}
    node = ResolvedNode(
        plugin=COMMAND,
        produces="deployed-site",
        effect="effectful",
        config={
            "kind": "deployed-site",
            "effect": "effectful",
            # the wrapped command attests receipt: wrong or absent env fails it
            "cmd": ["sh", "-c", 'test "$TOKEN" = hunter2-plaintext'],
            "secret-env": {"TOKEN": "secret"},
            "claim": {"site": "demo"},
        },
        consumes={"secret": "secrets/deploy-token"},
    )

    outcome = run_node("deploy/site", node, inputs, ctx)

    assert outcome.claim["site"] == "demo"


def test_missing_age_key_fails_cleanly(ctx, sops_lab, monkeypatch):
    import pytest

    from freckles.runner import RunError

    inputs = {"secret": imported_secret(ctx, sops_lab, "hunter2-plaintext")}
    monkeypatch.delenv("SOPS_AGE_KEY_FILE")

    with pytest.raises(RunError, match="SOPS_AGE_KEY_FILE"):
        build_request("deploy/site", consumer("effectful"), inputs, "/ws", [], None)

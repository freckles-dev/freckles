"""The two-layer secrets canary (Testing strategy, ADR 0005).

A chain whose secret value is a high-entropy sentinel runs end to end
through the real CLI; afterwards a byte-scan over everything that persists
— store, state db, workspaces, the working copy — asserts the plaintext
appears nowhere. The vacuity guard: the effectful command attests the
sha256 of the plaintext it received, so the scan cannot pass vacuously by
the secret never flowing. A negative control proves the guard bites.
"""

import hashlib

import pytest
from click.testing import CliRunner

from freckles.cli import main
from freckles.runner import RunError

SENTINEL = "canary-XK9QVJ2ZWM4YT7-0d8f3a1c9b6e-entangled"
ROTATED = "canary-ROTATED-PB5NHG8CWL2RD6-4e7a2f9c1d3b"


def chain(digest: str) -> str:
    attest = (
        'test "$(printf %s "$DEPLOY_TOKEN" | sha256sum | cut -d" " -f1)" = ' + digest
    )
    return f"""
nodes:
  secrets/deploy-token:
    op: import-sops
    config: {{file: secrets.sops.yaml, key: deploy_token}}
  deploy/site:
    op: command
    consumes: [secret]
    config:
      kind: deployed-site
      effect: effectful
      cmd: [sh, -c, '{attest}']
      secret-env: {{DEPLOY_TOKEN: secret}}
      claim: {{site: canary}}
"""


def digest(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode()).hexdigest()


@pytest.fixture
def canary_world(tmp_path, monkeypatch, sops_lab):
    config_dir = tmp_path / "canary"
    config_dir.mkdir()
    monkeypatch.chdir(config_dir)

    def invoke(*args: str):
        return CliRunner().invoke(
            main,
            list(args),
            env={"FRECKLES_DATA_DIR": str(tmp_path / "data")},
            catch_exceptions=False,
        )

    return config_dir, tmp_path / "data", sops_lab, invoke


def scan(root, sentinels: list[bytes]) -> int:
    scanned = 0
    for path in root.rglob("*"):
        if path.is_file():
            scanned += 1
            data = path.read_bytes()
            for sentinel in sentinels:
                assert sentinel not in data, f"plaintext leaked into {path}"
    return scanned


def test_the_plaintext_sentinel_never_persists(canary_world):
    config_dir, data_dir, sops_lab, invoke = canary_world
    (config_dir / "freckles.yaml").write_text(chain(digest(SENTINEL)))
    sops_lab.encrypt(config_dir / "secrets.sops.yaml", {"deploy_token": SENTINEL})

    result = invoke("heal", "--yes")
    assert result.exit_code == 0  # the attestation inside the checkpoint held

    # rotation: new ciphertext ripples into the checkpoint, prior: flows
    (config_dir / "freckles.yaml").write_text(chain(digest(ROTATED)))
    sops_lab.encrypt(config_dir / "secrets.sops.yaml", {"deploy_token": ROTATED})
    rerun = invoke("heal", "--yes")
    assert rerun.exit_code == 0

    sentinels = [SENTINEL.encode(), ROTATED.encode()]
    assert scan(data_dir, sentinels) > 2  # store, state, workspaces all seen
    scan(config_dir, sentinels)  # the working copy holds ciphertext only
    assert SENTINEL not in result.output + rerun.output


def test_the_vacuity_guard_bites(canary_world):
    """The negative control: a wrong plaintext must fail the checkpoint."""
    config_dir, _, sops_lab, invoke = canary_world
    (config_dir / "freckles.yaml").write_text(chain(digest(SENTINEL)))
    sops_lab.encrypt(config_dir / "secrets.sops.yaml", {"deploy_token": "not-it"})

    with pytest.raises(RunError, match="exited 1"):
        invoke("heal", "--yes")

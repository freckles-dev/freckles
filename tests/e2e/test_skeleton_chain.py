"""The walking skeleton's end-to-end loop (wayfinder ticket 12) — the done-condition.

resolve a three-node chain -> heal (day-1 = day-2 from zero) -> claims,
derivations, provenance, and the resolution document land in a sqlite CAS
under real CIDv1 addresses -> edit config -> re-resolve -> the heal walk
computes the checkpoint set -> confirm the checkpoint -> the plugin receives
`prior:` -> the ripple stops when claims re-mint identically.
"""

from pathlib import Path

import pytest

from freckles.documents import Cid
from freckles.heal import heal
from freckles.resolver import resolve
from freckles.runner import RunContext
from freckles.state import AnnotationsIndex, DerivationIndex, StateDb
from freckles.store import SqliteStore

FRECKLES_VERSION = "0.1.0"  # pinned to match the golden skeleton-chain fixtures


def golden_cid(name: str) -> str:
    """Look a fixture's CID up in the committed golden manifest."""
    manifest = Path(__file__).parents[2] / "conformance" / "golden" / "CIDS.txt"
    for line in manifest.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == name:
            return parts[0]
    raise AssertionError(f"no golden fixture named {name}")


CONFIG = """
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
"""


@pytest.fixture
def world(tmp_path):
    config_dir = tmp_path / "demo"
    config_dir.mkdir()
    (config_dir / "freckles.yaml").write_text(CONFIG)
    (config_dir / "cluster.yaml").write_text(
        "apps:\n  karakeep:\n    enabled: false\ncluster:\n  name: staging\n"
    )
    store = SqliteStore(tmp_path / "store.sqlite")
    db = StateDb(tmp_path / "state.sqlite")
    ctx = RunContext(
        store=store,
        annotations=AnnotationsIndex(db),
        config_dir=config_dir,
        freckles_version=FRECKLES_VERSION,
        workspace_root=tmp_path / "run",
    )
    ctx.workspace_root.mkdir()
    return ctx, DerivationIndex(db), config_dir


def heal_current(ctx, index, confirm):
    resolution, _ = resolve(ctx.config_dir, ctx.store, FRECKLES_VERSION)
    return heal(resolution, "demo", ctx, index, confirm)


def test_the_skeleton_loop(world):
    ctx, index, config_dir = world

    # --- day 1: everything heals; the effectful node is a confirmed checkpoint
    report = heal_current(ctx, index, confirm=lambda name: True)
    assert report.healed == ["values/apps", "render/site"]
    assert report.checkpoint_set == ["deploy/site"]
    assert report.confirmed == ["deploy/site"]
    assert report.deployment_current

    # real CIDv1 addressing, golden-checked: the walk minted the exact golden
    # derivation document for values/apps
    assert ctx.store.has(Cid.parse(golden_cid("derivation-values-apps")))

    # refs advanced per node; the claim behind the deploy ref is retrievable
    deploy_ref = ctx.store.get_ref("cfg/demo/nodes/deploy/site")
    from freckles.store import get_doc

    assert get_doc(ctx.store, deploy_ref)["site"] == "demo"

    # day-1 run had no prior
    workspace = Path(ctx.annotations.get(deploy_ref)["workspace"])
    assert not (workspace / "prior.json").exists()

    # --- steady state: an unchanged configuration is fully current
    report = heal_current(ctx, index, confirm=lambda name: True)
    assert report.current == ["values/apps", "render/site", "deploy/site"]
    assert not report.checkpoint_set

    # --- day 2: enable the app; pures heal, the checkpoint set is exactly deploy
    (config_dir / "cluster.yaml").write_text(
        "apps:\n  karakeep:\n    enabled: true\ncluster:\n  name: staging\n"
    )
    report = heal_current(ctx, index, confirm=lambda name: False)
    assert report.healed == ["values/apps", "render/site"]
    assert report.checkpoint_set == ["deploy/site"]
    assert not report.confirmed
    assert not report.deployment_current

    # --- confirm the checkpoint: deploy re-runs and receives prior:
    report = heal_current(
        ctx, index, confirm=lambda checkpoint: checkpoint.name == "deploy/site"
    )
    assert report.confirmed == ["deploy/site"]
    assert report.deployment_current
    new_deploy_ref = ctx.store.get_ref("cfg/demo/nodes/deploy/site")
    workspace = Path(ctx.annotations.get(new_deploy_ref)["workspace"])
    assert (workspace / "prior.json").exists()  # the plugin received prior:

    # extensional ripple-stop: same claim re-minted, so the ref is unchanged
    assert new_deploy_ref == deploy_ref


def test_unconfirmed_checkpoint_hides_downstream(world):
    ctx, index, config_dir = world
    (config_dir / "freckles.yaml").write_text(
        CONFIG
        + """
  audit/site:
    op: command
    consumes: [deployed-site]
    config:
      kind: audit-report
      effect: pure
      cmd: [sh, -c, "mkdir -p out && echo ok > out/report"]
"""
    )
    report = heal_current(ctx, index, confirm=lambda name: False)
    assert report.checkpoint_set == ["deploy/site"]
    assert report.hidden == ["audit/site"]  # downstream stays hidden

    report = heal_current(ctx, index, confirm=lambda name: True)
    assert report.confirmed == ["deploy/site"]
    assert "audit/site" in report.healed  # the walk resumes past the checkpoint

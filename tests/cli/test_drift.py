"""Drift (design.md §8): distrust feeds the one staleness mechanism.

A distrusted claim makes its node stale — the checkpoint set names it,
re-running heals, and the healed claim (often byte-identical) is trusted
again.
"""

from freckles.state import AnnotationsIndex, StateDb
from freckles.store import SqliteStore


def _distrust_current_claim(world, node: str, reason: str) -> AnnotationsIndex:
    store = SqliteStore(world.data_dir / "store.sqlite")
    claim = store.get_ref(f"cfg/demo/nodes/{node}")
    assert claim is not None
    store.close()
    index = AnnotationsIndex(StateDb(world.data_dir / "state.sqlite"))
    index.distrust(claim, reason)
    return index


def test_distrusted_claim_rejoins_the_checkpoint_set_and_heals(world):
    world.invoke("heal", "--yes")
    index = _distrust_current_claim(world, "deploy/site", "endpoint unreachable")

    status = world.invoke("status")
    assert status.exit_code == 2
    assert "deploy/site" in status.output  # stale through the one mechanism

    healed = world.invoke("heal", "--yes")
    assert healed.exit_code == 0

    # the re-run re-minted the claim (identical inputs) and restored trust
    store = SqliteStore(world.data_dir / "store.sqlite")
    claim = store.get_ref("cfg/demo/nodes/deploy/site")
    assert claim is not None
    assert index.distrusted(claim) is None
    assert world.invoke("status").exit_code == 0


def test_frozen_status_sees_distrust_without_deriving(world):
    world.invoke("heal", "--yes")
    _distrust_current_claim(world, "deploy/site", "drifted")

    result = world.invoke("status", "--frozen")

    assert result.exit_code == 2
    assert "deploy/site" in result.output

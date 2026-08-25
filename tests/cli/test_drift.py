"""Drift (design.md §8): distrust feeds the one staleness mechanism.

A distrusted claim makes its node stale — the checkpoint set names it,
re-running heals, and the healed claim (often byte-identical) is trusted
again.
"""

from freckles.state import AnnotationsIndex, StateDb
from freckles.store import SqliteStore

VERIFYING_CHAIN = """
nodes:
  values/apps:
    op: import-values
    config: {file: cluster.yaml, key: apps}
  deploy/site:
    op: command
    consumes: [values]
    config:
      kind: deployed-site
      effect: effectful
      cmd: [sh, -c, "true"]
      verify: [sh, -c, "echo 'health endpoint unreachable' >&2; exit 7"]
      claim: {site: demo}
"""


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


def test_verify_contradicted_marks_distrusted_and_exits_2(world):
    (world.config_dir / "freckles.yaml").write_text(VERIFYING_CHAIN)
    world.invoke("heal", "--yes")

    result = world.invoke("verify", "deploy/site")

    assert result.exit_code == 2
    assert "CONTRADICTED" in result.output
    assert "health endpoint unreachable" in result.output
    assert "distrusted" in result.output
    # the mark feeds the one staleness mechanism
    status = world.invoke("status")
    assert status.exit_code == 2
    assert "deploy/site" in status.output


def test_verify_confirmed_reads_the_claim_from_stdin(world):
    """Exit 0 iff the claim document arrived on the verify command's stdin."""
    chain = VERIFYING_CHAIN.replace(
        """verify: [sh, -c, "echo 'health endpoint unreachable' >&2; exit 7"]""",
        """verify: [sh, -c, "grep -q deployed-site"]""",
    )
    (world.config_dir / "freckles.yaml").write_text(chain)
    world.invoke("heal", "--yes")

    result = world.invoke("verify", "deploy/site")

    assert result.exit_code == 0
    assert "CONFIRMED" in result.output
    assert world.invoke("status").exit_code == 0  # no mark, still current


def test_verify_without_entrypoint_is_an_error_not_a_contradiction(world):
    world.invoke("heal", "--yes")  # the default chain has no verify anywhere

    result = world.invoke("verify", "deploy/site")

    assert result.exit_code == 1
    assert "no verify entrypoint" in result.stderr
    assert world.invoke("status").exit_code == 0  # nothing was marked


def test_verify_unknown_node_exits_1(world):
    world.invoke("heal", "--yes")

    result = world.invoke("verify", "no/such-node")

    assert result.exit_code == 1
    assert "unknown node" in result.stderr


def test_frozen_status_sees_distrust_without_deriving(world):
    world.invoke("heal", "--yes")
    _distrust_current_claim(world, "deploy/site", "drifted")

    result = world.invoke("status", "--frozen")

    assert result.exit_code == 2
    assert "deploy/site" in result.output

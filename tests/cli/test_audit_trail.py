"""Every run lands in the audit log.

design.md §8: it answers "what was deployed when" even after gc has
collected the blocks.
"""

import json

FAILING_CHAIN = """
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
      cmd: [sh, -c, "exit 3"]
"""


def _records(world):
    path = world.data_dir / "audit.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def test_heal_appends_one_record_per_run(world):
    world.invoke("heal", "--yes")

    records = _records(world)
    assert [r["node"] for r in records] == ["values/apps", "render/site", "deploy/site"]
    assert all(r["schema"] == 1 for r in records)
    assert all(r["config"] == "demo" for r in records)
    assert all(r["ok"] and r["exit_code"] == 0 for r in records)
    assert all(r["derivation"].startswith("baf") for r in records)
    assert all(r["claim"].startswith("baf") for r in records)


def test_cache_hits_run_nothing_so_record_nothing(world):
    world.invoke("heal", "--yes")
    world.invoke("heal", "--yes")

    records = _records(world)
    # the second walk re-runs only the source (re-import is the run);
    # pure and effectful cache hits never ran, so they never recorded
    assert [r["node"] for r in records[3:]] == ["values/apps"]


def test_status_records_the_pure_heals_it_performs(world):
    world.invoke("heal", "--yes")
    world.edit_values()

    world.invoke("status")

    tail = [r["node"] for r in _records(world)[3:]]
    assert "render/site" in tail  # the pure heal ran and recorded
    assert "deploy/site" not in tail  # the checkpoint was named, never run


def test_failed_run_records_the_failure(world):
    (world.config_dir / "freckles.yaml").write_text(FAILING_CHAIN)

    result = world.invoke("heal", "--yes")

    assert result.exit_code == 1
    record = _records(world)[-1]
    assert record["node"] == "render/site"
    assert record["ok"] is False
    assert record["claim"] is None  # failures never mint outcomes
    assert record["exit_code"] == 3
    assert "exited 3" in record["error"]

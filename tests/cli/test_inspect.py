"""Inspection is exactly two commands (R7): `show <node>` and `store cat <cid>`."""

import re

FULL_CID = re.compile(r"bafy[a-z0-9]{20,}")


def test_show_prints_claim_annotations_and_provenance(world):
    world.invoke("heal", "--yes")

    result = world.invoke("show", "deploy/site")

    assert result.exit_code == 0
    assert "deploy/site" in result.output
    assert "deployed-site" in result.output  # the claim's kind
    assert FULL_CID.search(result.output)  # inspection shows the full CID
    assert "annotations" in result.output
    assert "derivation" in result.output  # the provenance link


def test_show_unknown_node_exits_1(world):
    world.invoke("heal", "--yes")

    result = world.invoke("show", "no/such")

    assert result.exit_code == 1
    assert "no/such" in result.stderr


def test_store_cat_prints_raw_dag_json(world):
    import json

    world.invoke("heal", "--yes")
    resolution_cid = world.invoke("resolve").output.split()[-1]

    result = world.invoke("store", "cat", resolution_cid)

    assert result.exit_code == 0
    document = json.loads(result.output)  # raw DAG-JSON, machine-readable
    assert "nodes" in document


def test_store_cat_bad_cid_exits_1(world):
    world.invoke("heal", "--yes")

    result = world.invoke("store", "cat", "bafyreinotarealcid")

    assert result.exit_code == 1
    assert "error" in result.stderr

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


def test_show_redacts_secret_marked_annotations(secret_world):
    """R7: the human view shows secret names, never secret material."""
    from freckles.state import AnnotationsIndex, StateDb
    from freckles.store import SqliteStore

    secret_world.invoke("heal", "--yes")
    # a credential minted by the effectful run, recorded machine-locally
    # (the state seam is public — same db the CLI reads)
    store = SqliteStore(secret_world.data_dir / "store.sqlite")
    claim = store.get_ref("cfg/demo/nodes/deploy/site")
    assert claim is not None
    index = AnnotationsIndex(StateDb(secret_world.data_dir / "state.sqlite"))
    index.set(
        claim,
        index.get(claim) | {"admin_token": {"value": "cr3d-material", "secret": True}},
    )

    result = secret_world.invoke("show", "deploy/site")

    assert result.exit_code == 0
    assert "admin_token" in result.output  # the name is shown
    assert "cr3d-material" not in result.output  # the material never is
    assert "not shown" in result.output


def test_store_cat_bad_cid_exits_1(world):
    world.invoke("heal", "--yes")

    result = world.invoke("store", "cat", "bafyreinotarealcid")

    assert result.exit_code == 1
    assert "error" in result.stderr


def test_show_names_the_trust_state(world):
    """Scene 7's trust column: trusted by default, distrusted with the reason."""
    from freckles.state import AnnotationsIndex, StateDb
    from freckles.store import SqliteStore

    world.invoke("heal", "--yes")
    assert "trusted" in world.invoke("show", "deploy/site").output

    store = SqliteStore(world.data_dir / "store.sqlite")
    claim = store.get_ref("cfg/demo/nodes/deploy/site")
    assert claim is not None
    store.close()
    AnnotationsIndex(StateDb(world.data_dir / "state.sqlite")).distrust(
        claim, "endpoint unreachable"
    )

    shown = world.invoke("show", "deploy/site").output
    assert "distrusted" in shown
    assert "endpoint unreachable" in shown

"""`freckles resolve` — plumbing (R8): re-resolve only, nothing runs."""


def test_resolve_prints_the_resolution_cid_and_runs_nothing(world):
    result = world.invoke("resolve")

    assert result.exit_code == 0
    assert "resolution" in result.output
    assert "bafyre" in result.output  # the document's CID, plumbing-visible
    assert "healed" not in result.output
    assert "proceed?" not in result.output

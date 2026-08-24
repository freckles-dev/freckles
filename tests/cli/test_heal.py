"""`freckles heal` — the verb (R1): day-1 is day-2 from zero."""


def test_heal_from_zero_with_yes_reports_current(world):
    result = world.invoke("heal", "--yes")

    assert result.exit_code == 0
    # name-first output: every node of the chain is named
    for name in ("values/apps", "render/site", "deploy/site"):
        assert name in result.output
    assert "deployment current" in result.output
    # the store landed under FRECKLES_DATA_DIR — one store per user
    assert (world.data_dir / "store.sqlite").exists()

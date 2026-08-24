"""`freckles status` — R2: heals stale pures to name the exact checkpoint set."""


def test_status_when_current_exits_0(world):
    world.invoke("heal", "--yes")

    result = world.invoke("status")

    assert result.exit_code == 0
    assert "checkpoint set empty" in result.output


def test_status_after_edit_heals_pures_and_names_checkpoint_set(world):
    """R2: pure re-derivation is safe; the checkpoint set comes out exact."""
    world.invoke("heal", "--yes")
    world.edit_values()

    result = world.invoke("status")

    assert result.exit_code == 2
    assert "values/apps" in result.output  # pures healed on the spot
    assert "render/site" in result.output
    assert "checkpoint set" in result.output
    assert "deploy/site" in result.output
    # the effectful node was neither prompted nor run
    assert "proceed?" not in result.output

    # status is honest, not destructive: asking again still says stale
    again = world.invoke("status")
    assert again.exit_code == 2

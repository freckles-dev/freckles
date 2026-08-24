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


def test_status_frozen_when_current_exits_0(world):
    """--frozen looks without touching; an untouched current world reads current."""
    world.invoke("heal", "--yes")

    result = world.invoke("status", "--frozen")

    assert result.exit_code == 0
    assert "checkpoint set empty" in result.output


def test_status_frozen_after_edit_names_frontier_without_deriving(world):
    """--frozen names the stale frontier; downstream stays undetermined."""
    world.invoke("heal", "--yes")
    world.edit_values()

    result = world.invoke("status", "--frozen")

    assert result.exit_code == 2
    assert "values/apps" in result.output  # the source frontier
    assert "undetermined" in result.output

    # nothing was derived: a plain status still has all the pure healing to do
    after = world.invoke("status")
    assert "values/apps" in after.output
    assert "render/site" in after.output


def test_status_check_answers_silently(world):
    """R6: --check is the CI question — exit code only, no output."""
    world.invoke("heal", "--yes")

    current = world.invoke("status", "--check")
    assert current.exit_code == 0
    assert current.output == ""

    world.edit_values()
    stale = world.invoke("status", "--check")
    assert stale.exit_code == 2
    assert stale.output == ""

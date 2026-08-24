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


def test_checkpoint_prompt_names_the_facts_and_runs_on_yes(world):
    """R3: the prompt shows node, plugin, effect, and what is superseded."""
    result = world.invoke("heal", input="y\n")

    assert result.exit_code == 0
    assert "deploy/site" in result.output
    assert "command" in result.output  # the plugin behind the checkpoint
    assert "effectful" in result.output  # its declared effect
    assert "first claim" in result.output  # day 1: nothing superseded
    assert "deployment current" in result.output


def test_declined_checkpoint_leaves_deployment_stale_exit_2(world):
    """R6: a declined checkpoint means not current — exit 2, set named."""
    result = world.invoke("heal", input="n\n")

    assert result.exit_code == 2
    assert "checkpoint set" in result.output
    assert "deploy/site" in result.output
    assert "deployment current" not in result.output


def test_day2_checkpoint_prompt_shows_supersedes_and_prior(world):
    """R3: a re-run names the claim it supersedes and offers prior:."""
    world.invoke("heal", "--yes")
    world.edit_values()

    result = world.invoke("heal", input="y\n")

    assert result.exit_code == 0
    assert "supersedes" in result.output
    assert "first claim" not in result.output
    assert "prior" in result.output
    assert "deployment current" in result.output

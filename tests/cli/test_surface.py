"""R8: the verb inventory is exactly the ratified surface; dev commands retired."""


def test_the_ratified_verbs_are_the_surface(world):
    result = world.invoke("--help")

    assert result.exit_code == 0
    for verb in ("heal", "status", "resolve", "show", "store"):
        assert verb in result.output
    assert "dev" not in result.output.split()  # not even listed


def test_the_dev_group_is_retired(world):
    result = world.invoke("dev")

    assert result.exit_code == 2
    assert "no such command" in result.stderr.lower()

"""`freckles gc` — scene 8: roots and reachable, the kept/collected split, freed."""


def test_gc_prints_the_report(world):
    world.invoke("heal", "--yes")

    result = world.invoke("gc")

    assert result.exit_code == 0
    assert "roots" in result.output
    assert "blocks reachable" in result.output
    assert "unreferenced: 0" in result.output  # a fresh heal roots everything
    assert "grace 14d" in result.output
    assert "freed" in result.output


def test_gc_on_a_day2_store_keeps_superseded_claims_in_grace(world):
    world.invoke("heal", "--yes")
    world.edit_values()
    world.invoke("heal", "--yes")  # supersedes claims -> unreferenced blocks

    result = world.invoke("gc")

    assert result.exit_code == 0
    assert "unreferenced: 0" not in result.output
    assert "0 collected" in result.output  # grace holds everything for now

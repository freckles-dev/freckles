"""Resolution failures on the surface — exit 1, and R5's paste-ready fix."""


def test_ambiguous_edge_exits_1_with_paste_ready_fix(world):
    world.add_second_values_provider()

    result = world.invoke("status")

    assert result.exit_code == 1
    # both providers are named, and the fix can be pasted verbatim
    assert "values/apps" in result.stderr
    assert "values/cluster" in result.stderr
    assert "render/site" in result.stderr
    assert "use: {values: values/apps}" in result.stderr

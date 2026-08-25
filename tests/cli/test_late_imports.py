"""Late imports through the real CLI (M8): import-git and import-file-tree.

Three file-tree sources — a branch-following repository, a commit-pinned
repository, and a working-copy directory — each feeding its own consumer.
Sources re-run every walk; extensional addressing decides who ripples.
"""

import pytest

LATE_IMPORTS = """
nodes:
  sources/repo:
    op: import-git
    config: {{url: {tracking_url}, ref: main}}
  sources/pinned:
    op: import-git
    config: {{url: {pinned_url}, commit: {pinned_commit}}}
  sources/assets:
    op: import-file-tree
    config: {{dir: assets}}
  render/site:
    op: command
    consumes: [file-tree]
    use: {{file-tree: sources/repo}}
    config:
      kind: rendered
      effect: pure
      cmd: [sh, -c, "mkdir -p out && cp inputs/file-tree/app.yaml out/app.yaml"]
  check/pinned:
    op: command
    consumes: [file-tree]
    use: {{file-tree: sources/pinned}}
    config:
      kind: checked
      effect: pure
      cmd: [sh, -c, "mkdir -p out && cp inputs/file-tree/config.yaml out/c.yaml"]
  bundle/assets:
    op: command
    consumes: [file-tree]
    use: {{file-tree: sources/assets}}
    config:
      kind: bundled
      effect: pure
      cmd: [sh, -c, "mkdir -p out && cp inputs/file-tree/logo.txt out/logo.txt"]
"""


@pytest.fixture
def imports_world(world, git_lab):
    tracking = git_lab({"app.yaml": "version: 1\n"})
    pinned = git_lab({"config.yaml": "pinned: true\n"})
    pinned_commit = pinned.head
    pinned.commit({"config.yaml": "pinned: false\n"})  # the pin must not follow
    assets = world.config_dir / "assets"
    assets.mkdir()
    (assets / "logo.txt").write_text("freckles")
    (world.config_dir / "freckles.yaml").write_text(
        LATE_IMPORTS.format(
            tracking_url=tracking.url,
            pinned_url=pinned.url,
            pinned_commit=pinned_commit,
        )
    )
    return world, tracking


def healed(output: str) -> set[str]:
    return {
        line.split()[0] for line in output.splitlines() if line.endswith("  healed")
    }


def test_day1_heal_imports_all_three_sources(imports_world):
    world, _ = imports_world

    result = world.invoke("heal")

    assert result.exit_code == 0, result.output
    assert healed(result.output) == {
        "sources/repo",
        "sources/pinned",
        "sources/assets",
        "render/site",
        "check/pinned",
        "bundle/assets",
    }


def test_branch_advance_ripples_exactly_its_consumer(imports_world):
    world, tracking = imports_world
    world.invoke("heal")

    tracking.commit({"app.yaml": "version: 2\n"})
    result = world.invoke("heal")

    assert result.exit_code == 0, result.output
    assert healed(result.output) == {"sources/repo", "render/site"}


def test_asset_edit_ripples_exactly_its_consumer(imports_world):
    world, _ = imports_world
    world.invoke("heal")

    (world.config_dir / "assets" / "logo.txt").write_text("freckles v2")
    result = world.invoke("heal")

    assert result.exit_code == 0, result.output
    assert healed(result.output) == {"sources/assets", "bundle/assets"}


def test_unchanged_world_heals_nothing(imports_world):
    world, _ = imports_world
    world.invoke("heal")

    result = world.invoke("heal")

    assert result.exit_code == 0, result.output
    assert healed(result.output) == set()

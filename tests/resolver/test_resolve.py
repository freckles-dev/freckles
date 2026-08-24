"""Resolver seam tests: inference, ambiguity, use:, determinism of the document."""

import pytest

from freckles.resolver import ResolutionError, resolve
from freckles.store import SqliteStore

CHAIN = """
nodes:
  values/apps:
    op: import-values
    config: {file: cluster.yaml, key: apps}
  render/site:
    op: command
    consumes: [values]
    config:
      kind: file-tree
      effect: pure
      cmd: [render.sh]
  deploy/site:
    op: command
    consumes: [file-tree]
    config:
      kind: deployed-site
      effect: effectful
      cmd: [deploy.sh]
"""


@pytest.fixture
def store(tmp_path):
    return SqliteStore(tmp_path / "store.sqlite")


@pytest.fixture
def config_dir(tmp_path):
    directory = tmp_path / "demo"
    directory.mkdir()
    (directory / "freckles.yaml").write_text(CHAIN)
    (directory / "cluster.yaml").write_text("apps: {karakeep: {enabled: false}}\n")
    return directory


def test_resolves_the_skeleton_chain(store, config_dir):
    resolution, cid = resolve(config_dir, store, "0.0.0-test")
    render = resolution.nodes["render/site"]
    assert render.consumes == {"values": "values/apps"}
    assert render.produces == "file-tree"
    assert render.effect == "pure"
    deploy = resolution.nodes["deploy/site"]
    assert deploy.consumes == {"file-tree": "render/site"}
    assert deploy.effect == "effectful"
    assert store.get_ref("cfg/demo/current") == cid


def test_unchanged_configuration_resolves_to_same_cid(store, config_dir):
    _, first = resolve(config_dir, store, "0.0.0-test")
    _, second = resolve(config_dir, store, "0.0.0-test")
    assert first == second


def test_config_edit_changes_the_resolution_cid(store, config_dir):
    _, first = resolve(config_dir, store, "0.0.0-test")
    (config_dir / "cluster.yaml").write_text("apps: {karakeep: {enabled: true}}\n")
    _, second = resolve(config_dir, store, "0.0.0-test")
    assert first != second  # the config snapshot is part of the document


def test_ambiguity_is_a_hard_error(store, tmp_path):
    directory = tmp_path / "ambiguous"
    directory.mkdir()
    (directory / "freckles.yaml").write_text(
        """
nodes:
  values/a: {op: import-values, config: {file: v.yaml, key: a}}
  values/b: {op: import-values, config: {file: v.yaml, key: b}}
  render/site:
    op: command
    consumes: [values]
    config: {kind: file-tree, effect: pure, cmd: [render.sh]}
"""
    )
    (directory / "v.yaml").write_text("a: 1\nb: 2\n")
    with pytest.raises(ResolutionError, match="ambiguous"):
        resolve(directory, store, "0.0.0-test")


def test_use_breaks_the_tie(store, tmp_path):
    directory = tmp_path / "tied"
    directory.mkdir()
    (directory / "freckles.yaml").write_text(
        """
nodes:
  values/a: {op: import-values, config: {file: v.yaml, key: a}}
  values/b: {op: import-values, config: {file: v.yaml, key: b}}
  render/site:
    op: command
    consumes: [values]
    use: {values: values/b}
    config: {kind: file-tree, effect: pure, cmd: [render.sh]}
"""
    )
    (directory / "v.yaml").write_text("a: 1\nb: 2\n")
    resolution, _ = resolve(directory, store, "0.0.0-test")
    assert resolution.nodes["render/site"].consumes == {"values": "values/b"}


def test_missing_provider_is_a_hard_error(store, tmp_path):
    directory = tmp_path / "orphan"
    directory.mkdir()
    (directory / "freckles.yaml").write_text(
        """
nodes:
  deploy/site:
    op: command
    consumes: [file-tree]
    config: {kind: deployed-site, effect: effectful, cmd: [deploy.sh]}
"""
    )
    with pytest.raises(ResolutionError, match="no provider"):
        resolve(directory, store, "0.0.0-test")


def test_adapter_without_kind_or_effect_is_a_hard_error(store, tmp_path):
    directory = tmp_path / "bare"
    directory.mkdir()
    (directory / "freckles.yaml").write_text(
        "nodes:\n  x: {op: command, config: {cmd: [true]}}\n"
    )
    with pytest.raises(ResolutionError, match="node-supplied kind/effect"):
        resolve(directory, store, "0.0.0-test")

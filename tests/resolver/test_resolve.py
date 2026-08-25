"""Resolver seam tests: inference, ambiguity, use:, determinism of the document."""

import pytest

from freckles.resolver import ResolutionError, resolve, resolve_round
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


def test_purity_gate_rejects_plaintext_wiring_into_a_pure_node(store, tmp_path):
    """ADR 0005: wiring a secret's plaintext into a pure node is a hard error."""
    directory = tmp_path / "impure"
    directory.mkdir()
    (directory / "freckles.yaml").write_text(
        """
nodes:
  secrets/token:
    op: import-sops
    config: {file: secrets.sops.yaml, key: token}
  render/site:
    op: command
    consumes: [secret]
    config:
      kind: file-tree
      effect: pure
      cmd: [render.sh]
      secret-env: {TOKEN: secret}
"""
    )
    with pytest.raises(ResolutionError, match="purity"):
        resolve(directory, store, "0.0.0-test")


# --- op -> plugin claim binding (M5): by manifest name, pinned by CID -------


def _put_plugin(store, name="copier", version="0.2.0", produces="file-tree"):
    from freckles.documents import SCHEMA
    from freckles.store import put_blob, put_doc

    payload = put_blob(store, b"#!/usr/bin/env python3\npass\n")
    return put_doc(
        store,
        {
            "schema": SCHEMA,
            "kind": "plugin",
            "name": name,
            "version": version,
            "produces": produces,
            "effect": "pure",
            "entrypoint": name,
            "payload": payload,
        },
    )


def test_op_binds_to_the_store_plugin_claim_by_manifest_name(store, config_dir):
    plugin_cid = _put_plugin(store)
    (config_dir / "freckles.yaml").write_text(
        """
nodes:
  render/scaffold:
    op: copier
    config: {template: web}
"""
    )

    resolution, _ = resolve(config_dir, store, "0.0.0-test")

    node = resolution.nodes["render/scaffold"]
    assert node.plugin == plugin_cid
    assert node.produces == "file-tree"
    assert node.effect == "pure"


def test_node_version_pin_selects_among_plugin_versions(store, config_dir):
    _put_plugin(store, version="0.1.0")
    pinned = _put_plugin(store, version="0.2.0")
    (config_dir / "freckles.yaml").write_text(
        """
nodes:
  render/scaffold:
    op: copier
    version: 0.2.0
    config: {template: web}
"""
    )

    resolution, _ = resolve(config_dir, store, "0.0.0-test")

    assert resolution.nodes["render/scaffold"].plugin == pinned


def test_unknown_op_with_no_provider_is_a_hard_error(store, config_dir):
    (config_dir / "freckles.yaml").write_text(
        """
nodes:
  render/scaffold:
    op: nonexistent-op
    config: {}
"""
    )

    with pytest.raises(ResolutionError, match="nonexistent-op"):
        resolve(config_dir, store, "0.0.0-test")


def test_deferral_cascades_through_consumers_of_consumers(store, tmp_path):
    """Design §6: "its consumers defer transitively" — at any depth (M9).

    The acceptance chain's shape: a command node consumes the product of a
    node that itself waits on a deferred acquisition. Round 1 must defer
    the whole downstream, not error on the second hop.
    """
    directory = tmp_path / "deep"
    directory.mkdir()
    (directory / "freckles.yaml").write_text(
        """
nodes:
  plugins/greeter:
    op: fetch-verify
    config:
      kind: plugin
      url: http://127.0.0.1:9/greeter
      sha256: "0000000000000000000000000000000000000000000000000000000000000000"
      manifest: {name: greeter, version: 0.1.0, produces: greeting, effect: pure}
  greet:
    op: greeter
    config: {}
  render/site:
    op: command
    consumes: [greeting]
    config: {kind: file-tree, effect: pure, cmd: [render.sh]}
  deploy/site:
    op: command
    consumes: [file-tree]
    config:
      kind: deployed-site
      effect: effectful
      cmd: [deploy.sh]
      claim: {site: demo}
"""
    )

    _, _, deferred = resolve_round(directory, store, "0.0.0-test")

    assert set(deferred) == {"greet", "render/site", "deploy/site"}

"""bootstrap-pixi: the first-class peer bootstrap (design.md §11)."""

import hashlib
import os
import re

import pytest

from freckles.documents import ResolvedNode
from freckles.runner import RunError, run_node

PIXI_DIST = b"#!/usr/bin/env python3\nprint('fake pixi')\n"

MANIFEST = {
    "name": "bootstrap-pixi",
    "version": "0.1.0",
    "produces": "bootstrap",
    "effect": "pure",
}


def bootstrap_node(plugin_cid, config):
    return ResolvedNode(
        plugin=plugin_cid,
        produces="bootstrap",
        effect="pure",
        config=config,
        consumes={},
    )


@pytest.fixture
def pinned_config(lab):
    (lab.docroot / "pixi-dist").write_bytes(PIXI_DIST)
    return {
        "version": "0.77.0",
        "url": f"{lab.url}/pixi-dist",
        "sha256": hashlib.sha256(PIXI_DIST).hexdigest(),
    }


def test_realizes_pixi_under_the_envs_root(ctx, install_plugin, pinned_config):
    plugin = install_plugin("bootstrap_pixi.py", **MANIFEST)

    outcome = run_node("bootstrap", bootstrap_node(plugin, pinned_config), {}, ctx)

    binary = ctx.envs_root / "pixi" / "0.77.0" / "bin" / "pixi"
    assert outcome.annotations["path"] == str(binary)
    assert binary.read_bytes() == PIXI_DIST
    assert os.access(binary, os.X_OK)


def test_claim_is_machine_independent(ctx, install_plugin, pinned_config):
    plugin = install_plugin("bootstrap_pixi.py", **MANIFEST)

    outcome = run_node("bootstrap", bootstrap_node(plugin, pinned_config), {}, ctx)

    claim = outcome.claim
    assert claim["kind"] == "bootstrap"
    assert claim["tool"] == "pixi"
    assert claim["version"] == "0.77.0"
    # The tool-claim platform convention, shared across every bootstrap and
    # install plugin — the swappable contract's identity hinges on it.
    assert re.fullmatch(r"[a-z]+-(x64|arm64)", claim["platform"])
    assert "content" not in claim
    assert "path" not in claim


def test_reruns_mint_the_byte_identical_claim(
    ctx, install_plugin, pinned_config, encode_checked
):
    """The determinism harness, applied as pure standard plugins land."""
    plugin = install_plugin("bootstrap_pixi.py", **MANIFEST)
    node = bootstrap_node(plugin, pinned_config)

    first = run_node("bootstrap", node, {}, ctx)
    second = run_node("bootstrap", node, {}, ctx)

    assert encode_checked(first.claim) == encode_checked(second.claim)


def test_checksum_mismatch_names_both_digests(ctx, install_plugin, pinned_config):
    plugin = install_plugin("bootstrap_pixi.py", **MANIFEST)
    config = {**pinned_config, "sha256": "0" * 64}

    with pytest.raises(RunError, match=f"expected {'0' * 64}, got [0-9a-f]{{64}}"):
        run_node("bootstrap", bootstrap_node(plugin, config), {}, ctx)


def test_default_url_is_the_pixi_release_artifact(load_plugin_module):
    """Pixi's release layout: rust-triple artifact names, musl on linux."""
    bootstrap_pixi = load_plugin_module("bootstrap_pixi")

    url = bootstrap_pixi.default_url("0.77.0", "x86_64-unknown-linux-musl")

    assert url == (
        "https://github.com/prefix-dev/pixi/releases/download/v0.77.0/"
        "pixi-x86_64-unknown-linux-musl"
    )


def test_linux_triple_is_musl(load_plugin_module):
    """The static-binary variant — the userspace story the research pinned."""
    bootstrap_pixi = load_plugin_module("bootstrap_pixi")

    assert bootstrap_pixi.rust_triple("linux", "x86_64") == (
        "x86_64-unknown-linux-musl"
    )
    assert bootstrap_pixi.rust_triple("darwin", "arm64") == "aarch64-apple-darwin"

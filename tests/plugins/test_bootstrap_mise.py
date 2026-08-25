"""bootstrap-mise: the default bootstrap realizes a pinned mise (design.md §11)."""

import hashlib
import os
import re

import pytest

from freckles.documents import ResolvedNode
from freckles.runner import RunError, run_node

MISE_DIST = b"#!/usr/bin/env python3\nprint('fake mise')\n"

MANIFEST = {
    "name": "bootstrap-mise",
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
    (lab.docroot / "mise-dist").write_bytes(MISE_DIST)
    return {
        "version": "2025.8.1",
        "url": f"{lab.url}/mise-dist",
        "sha256": hashlib.sha256(MISE_DIST).hexdigest(),
    }


def test_realizes_mise_under_the_envs_root(ctx, install_plugin, pinned_config):
    plugin = install_plugin("bootstrap_mise.py", **MANIFEST)

    outcome = run_node("bootstrap", bootstrap_node(plugin, pinned_config), {}, ctx)

    binary = ctx.envs_root / "mise" / "2025.8.1" / "bin" / "mise"
    assert outcome.annotations["path"] == str(binary)
    assert binary.read_bytes() == MISE_DIST
    assert os.access(binary, os.X_OK)


def test_claim_is_machine_independent(ctx, install_plugin, pinned_config):
    plugin = install_plugin("bootstrap_mise.py", **MANIFEST)

    outcome = run_node("bootstrap", bootstrap_node(plugin, pinned_config), {}, ctx)

    claim = outcome.claim
    assert claim["kind"] == "bootstrap"
    assert claim["tool"] == "mise"
    assert claim["version"] == "2025.8.1"
    # mise's release-artifact naming (the default URL is derived from it).
    assert re.fullmatch(r"[a-z]+-(x64|arm64)", claim["platform"])
    assert "content" not in claim  # realized environments stay out of the CAS
    assert "path" not in claim  # the realized path is annotation, never identity


def test_reruns_mint_the_byte_identical_claim(
    ctx, install_plugin, pinned_config, encode_checked
):
    """The determinism harness, applied as pure standard plugins land."""
    plugin = install_plugin("bootstrap_mise.py", **MANIFEST)
    node = bootstrap_node(plugin, pinned_config)

    first = run_node("bootstrap", node, {}, ctx)
    second = run_node("bootstrap", node, {}, ctx)

    assert encode_checked(first.claim) == encode_checked(second.claim)


def test_checksum_mismatch_names_both_digests(ctx, install_plugin, pinned_config):
    plugin = install_plugin("bootstrap_mise.py", **MANIFEST)
    config = {**pinned_config, "sha256": "0" * 64}

    with pytest.raises(RunError, match=f"expected {'0' * 64}, got [0-9a-f]{{64}}"):
        run_node("bootstrap", bootstrap_node(plugin, config), {}, ctx)


def test_default_url_is_the_mise_release_artifact(load_plugin_module):
    """The documented mise release layout — the version pin derives the URL."""
    bootstrap_mise = load_plugin_module("bootstrap_mise")

    url = bootstrap_mise.default_url("2025.8.1", "linux-x64")

    assert url == (
        "https://github.com/jdx/mise/releases/download/v2025.8.1/"
        "mise-v2025.8.1-linux-x64"
    )

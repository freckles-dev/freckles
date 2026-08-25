"""pixi-install: sha256-locked tools from conda-forge (design.md §11, M7).

The hash-locked route: a per-tool pixi workspace whose pixi.lock records
per-package sha256 — never `pixi global`, which pins by version spec only
(Bootstrap tool evaluation).
"""

import json

import pytest

from freckles.documents import ResolvedNode
from freckles.runner import RunError, run_node

MANIFEST = {
    "name": "pixi-install",
    "version": "0.1.0",
    "produces": "tool",
    "effect": "pure",
    "consumes": {"bootstrap": {}},
}


def install_node(plugin_cid, package="copier", version="9.17.2"):
    return ResolvedNode(
        plugin=plugin_cid,
        produces="tool",
        effect="pure",
        config={"package": package, "version": version},
        consumes={"bootstrap": "bootstrap"},
    )


def test_realizes_the_tool_and_mints_its_claim(ctx, install_plugin, realized_pixi):
    plugin = install_plugin("pixi_install.py", **MANIFEST)

    outcome = run_node("tools/copier", install_node(plugin), realized_pixi, ctx)

    claim = outcome.claim
    assert claim["kind"] == "tool"
    assert claim["tool"] == "copier"
    assert claim["version"] == "9.17.2"
    assert "content" not in claim  # realized environments stay out of the CAS
    workspace = ctx.envs_root / "pixi-workspaces" / "copier" / "9.17.2"
    binary = workspace / ".pixi" / "envs" / "default" / "bin" / "copier"
    assert outcome.annotations["path"] == str(binary)
    assert binary.exists()


def test_workspace_manifest_pins_exactly_from_conda_forge(
    ctx, install_plugin, realized_pixi
):
    """The plugin-authored manifest: exact ==version pin, conda-forge channel."""
    plugin = install_plugin("pixi_install.py", **MANIFEST)

    run_node("tools/copier", install_node(plugin), realized_pixi, ctx)

    manifest = (
        ctx.envs_root / "pixi-workspaces" / "copier" / "9.17.2" / "pixi.toml"
    ).read_text()
    assert 'copier = "==9.17.2"' in manifest
    assert "conda-forge" in manifest


def test_install_goes_through_the_workspace_never_global(
    ctx, install_plugin, realized_pixi
):
    """sha256 locking lives in the workspace's pixi.lock — global has none."""
    plugin = install_plugin("pixi_install.py", **MANIFEST)

    run_node("tools/copier", install_node(plugin), realized_pixi, ctx)

    workspace = ctx.envs_root / "pixi-workspaces" / "copier" / "9.17.2"
    log = workspace / "invocations.jsonl"
    invocations = [json.loads(line) for line in log.read_text().splitlines()]
    assert ["install", "--manifest-path", str(workspace)] in invocations


def test_reruns_mint_the_byte_identical_claim(
    ctx, install_plugin, realized_pixi, encode_checked
):
    """The determinism harness, applied as pure standard plugins land."""
    plugin = install_plugin("pixi_install.py", **MANIFEST)
    node = install_node(plugin)

    first = run_node("tools/copier", node, realized_pixi, ctx)
    second = run_node("tools/copier", node, realized_pixi, ctx)

    assert encode_checked(first.claim) == encode_checked(second.claim)


FAILING_PIXI = """\
#!/usr/bin/env python3
import sys
print("solver on fire", file=sys.stderr)
sys.exit(3)
"""


def test_pixi_failure_surfaces_as_a_structured_error(
    ctx, install_plugin, realized_pixi
):
    binary = ctx.envs_root / "pixi" / "0.77.0" / "bin" / "pixi"
    binary.write_text(FAILING_PIXI)
    plugin = install_plugin("pixi_install.py", **MANIFEST)

    with pytest.raises(RunError, match="pixi install copier==9.17.2 failed"):
        run_node("tools/copier", install_node(plugin), realized_pixi, ctx)


def test_missing_pixi_binary_fails_cleanly(ctx, install_plugin, realized_pixi):
    (ctx.envs_root / "pixi" / "0.77.0" / "bin" / "pixi").unlink()
    plugin = install_plugin("pixi_install.py", **MANIFEST)

    with pytest.raises(RunError, match="pixi not found"):
        run_node("tools/copier", install_node(plugin), realized_pixi, ctx)

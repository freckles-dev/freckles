"""mise-install: tool claims realized through the bootstrap chain (design.md §11)."""

import json

import pytest

from freckles.documents import ResolvedNode
from freckles.runner import RunError, run_node

MANIFEST = {
    "name": "mise-install",
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


def test_realizes_the_tool_and_mints_its_claim(ctx, install_plugin, realized_mise):
    plugin = install_plugin("mise_install.py", **MANIFEST)

    outcome = run_node("tools/copier", install_node(plugin), realized_mise, ctx)

    claim = outcome.claim
    assert claim["kind"] == "tool"
    assert claim["tool"] == "copier"
    assert claim["version"] == "9.17.2"
    assert "content" not in claim  # realized environments stay out of the CAS
    binary = ctx.envs_root / "mise-data" / "installs" / "copier" / "9.17.2"
    assert outcome.annotations["path"] == str(binary / "bin" / "copier")
    assert (binary / "bin" / "copier").exists()


def test_version_only_locking_is_the_whole_pin(ctx, install_plugin, realized_mise):
    """pipx-backend tools lock by version alone (Bootstrap tool evaluation)."""
    plugin = install_plugin("mise_install.py", **MANIFEST)

    run_node("tools/copier", install_node(plugin), realized_mise, ctx)

    log = ctx.envs_root / "mise-data" / "invocations.jsonl"
    invocations = [json.loads(line) for line in log.read_text().splitlines()]
    assert ["install", "copier@9.17.2"] in invocations


def test_reruns_mint_the_byte_identical_claim(
    ctx, install_plugin, realized_mise, encode_checked
):
    """The determinism harness, applied as pure standard plugins land."""
    plugin = install_plugin("mise_install.py", **MANIFEST)
    node = install_node(plugin)

    first = run_node("tools/copier", node, realized_mise, ctx)
    second = run_node("tools/copier", node, realized_mise, ctx)

    assert encode_checked(first.claim) == encode_checked(second.claim)


FAILING_MISE = """\
#!/usr/bin/env python3
import sys
print("registry on fire", file=sys.stderr)
sys.exit(3)
"""


def test_mise_failure_surfaces_as_a_structured_error(
    ctx, install_plugin, realized_mise
):
    binary = ctx.envs_root / "mise" / "2025.8.1" / "bin" / "mise"
    binary.write_text(FAILING_MISE)
    plugin = install_plugin("mise_install.py", **MANIFEST)

    with pytest.raises(RunError, match="mise install copier@9.17.2 failed"):
        run_node("tools/copier", install_node(plugin), realized_mise, ctx)


def test_missing_mise_binary_fails_cleanly(ctx, install_plugin, realized_mise):
    """The annotation says realized, the binary is gone: drift, named plainly."""
    (ctx.envs_root / "mise" / "2025.8.1" / "bin" / "mise").unlink()
    plugin = install_plugin("mise_install.py", **MANIFEST)

    with pytest.raises(RunError, match="mise not found"):
        run_node("tools/copier", install_node(plugin), realized_mise, ctx)

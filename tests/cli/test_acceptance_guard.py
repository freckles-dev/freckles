"""Per-push guard: the acceptance chains resolve through the real CLI.

The acceptance suite (`acceptance/`) is network-bound and runs only in
its own workflow — manual dispatch and version tags. This hermetic guard
resolves the very same chain documents per-push, so a YAML or schema
drift in the acceptance chains breaks here, not at tag time. Resolve
runs nothing: the plugin URLs never get fetched, and day-1 from zero the
strict verb reports the acquisition frontier as unbound ops (R8) — the
guard pins that frontier exactly, since any malformed chain fails with a
different error before deferral is reached.
"""

import importlib.util
from pathlib import Path

ACCEPTANCE_DIR = Path(__file__).parent.parent.parent / "acceptance"

DUMMY_URL = "http://127.0.0.1:9/unfetched"
DUMMY_SHA = "0" * 64


def _chains():
    spec = importlib.util.spec_from_file_location(
        "acceptance_chains", ACCEPTANCE_DIR / "chains.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_both_acceptance_chains_resolve_from_zero(world, sops_lab, tmp_path):
    chains = _chains()
    routes = {
        "mise": chains.mise_chain(
            bootstrap_mise_url=DUMMY_URL,
            bootstrap_mise_sha256=DUMMY_SHA,
            mise_install_url=DUMMY_URL,
            mise_install_sha256=DUMMY_SHA,
            state_dir=str(tmp_path / "state"),
        ),
        "pixi": chains.pixi_chain(
            bootstrap_pixi_url=DUMMY_URL,
            bootstrap_pixi_sha256=DUMMY_SHA,
            pixi_install_url=DUMMY_URL,
            pixi_install_sha256=DUMMY_SHA,
            state_dir=str(tmp_path / "state"),
        ),
    }
    (world.config_dir / "cluster.yaml").write_text("apps:\n  site:\n    on: true\n")
    sops_lab.encrypt(
        world.config_dir / "secrets.sops.yaml", {"deploy_token": "guard-sentinel"}
    )

    frontiers = {
        "mise": ("bootstrap", "tools/uv", "tools/copier", "render/site", "deploy/site"),
        "pixi": ("bootstrap", "tools/copier", "render/site", "deploy/site"),
    }
    for route, chain in routes.items():
        (world.config_dir / "freckles.yaml").write_text(chain)

        result = world.invoke("resolve")

        assert result.exit_code == 1, f"{route}: {result.output}"
        assert "unbound ops remain" in result.output, f"{route}: {result.output}"
        for node in frontiers[route]:
            assert node in result.output, f"{route}: {result.output}"


def _seed_plugin_claims(data_dir):
    """The post-acquisition store state, minted directly.

    One plugin claim per standard plugin, shaped the way fetch-verify
    mints them.
    """
    from freckles.documents import SCHEMA
    from freckles.store import SqliteStore, put_blob, put_doc

    data_dir.mkdir(parents=True, exist_ok=True)
    store = SqliteStore(data_dir / "store.sqlite")
    plugins = {
        "bootstrap-mise": ("bootstrap", {}),
        "mise-install": ("tool", {"bootstrap": {}}),
        "bootstrap-pixi": ("bootstrap", {}),
        "pixi-install": ("tool", {"bootstrap": {}}),
    }
    for name, (produces, consumes) in plugins.items():
        payload = put_blob(store, b"#!/usr/bin/env python3\npass\n")
        put_doc(
            store,
            {
                "schema": SCHEMA,
                "kind": "plugin",
                "name": name,
                "version": "0.1.0",
                "produces": produces,
                "consumes": consumes,
                "effect": "pure",
                "entrypoint": name,
                "payload": payload,
            },
        )
    store.close()


def test_seeded_with_plugin_claims_both_chains_resolve_fully(world, sops_lab, tmp_path):
    """Past the acquisition frontier, the strict resolve must fully bind.

    With the plugin claims in the store, every op binds and every edge
    wires — the hermetic stand-in for the resolution the acceptance heal
    reaches on round 2.
    """
    chains = _chains()
    _seed_plugin_claims(world.data_dir)
    (world.config_dir / "cluster.yaml").write_text("apps:\n  site:\n    on: true\n")
    sops_lab.encrypt(
        world.config_dir / "secrets.sops.yaml", {"deploy_token": "guard-sentinel"}
    )
    routes = {
        "mise": chains.mise_chain(
            bootstrap_mise_url=DUMMY_URL,
            bootstrap_mise_sha256=DUMMY_SHA,
            mise_install_url=DUMMY_URL,
            mise_install_sha256=DUMMY_SHA,
            state_dir=str(tmp_path / "state"),
        ),
        "pixi": chains.pixi_chain(
            bootstrap_pixi_url=DUMMY_URL,
            bootstrap_pixi_sha256=DUMMY_SHA,
            pixi_install_url=DUMMY_URL,
            pixi_install_sha256=DUMMY_SHA,
            state_dir=str(tmp_path / "state"),
        ),
    }

    for route, chain in routes.items():
        (world.config_dir / "freckles.yaml").write_text(chain)

        result = world.invoke("resolve")

        assert result.exit_code == 0, f"{route}: {result.output}"
        assert "bafyre" in result.output, route


def test_the_mechanics_tail_is_byte_identical_across_routes(tmp_path):
    """The swap's ripple-stop needs the consumer nodes identical, not similar."""
    chains = _chains()
    kwargs = dict(state_dir=str(tmp_path / "state"))
    mise = chains.mise_chain(
        bootstrap_mise_url=DUMMY_URL,
        bootstrap_mise_sha256=DUMMY_SHA,
        mise_install_url=DUMMY_URL,
        mise_install_sha256=DUMMY_SHA,
        **kwargs,
    )
    pixi = chains.pixi_chain(
        bootstrap_pixi_url=DUMMY_URL,
        bootstrap_pixi_sha256=DUMMY_SHA,
        pixi_install_url=DUMMY_URL,
        pixi_install_sha256=DUMMY_SHA,
        **kwargs,
    )

    tail_marker = "  values/apps:"
    assert mise[mise.index(tail_marker) :] == pixi[pixi.index(tail_marker) :]

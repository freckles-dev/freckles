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

    for route, chain in routes.items():
        (world.config_dir / "freckles.yaml").write_text(chain)

        result = world.invoke("resolve")

        assert result.exit_code == 1, f"{route}: {result.output}"
        assert "unbound ops remain" in result.output, f"{route}: {result.output}"
        for node in ("bootstrap", "tools/copier", "render/site", "deploy/site"):
            assert node in result.output, f"{route}: {result.output}"


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

"""The pixi leg through the real CLI (M7): the peer bootstrap route.

Same shape as the mise route — fetch-verify acquires the payloads, one
heal from zero realizes pixi and a conda-forge tool through a sha256-locked
per-tool workspace, and the attesting command node proves the tool answers
to its bare name on the constructed PATH.
"""

import hashlib
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from freckles.sdk.build import build_payload

PLUGINS_DIR = Path(__file__).parent.parent.parent / "plugins"

PIXI_ROUTE = """
nodes:
  plugins/bootstrap-pixi:
    op: fetch-verify
    config:
      kind: plugin
      url: {url}/bootstrap-pixi
      sha256: "{bootstrap_pixi_sha}"
      manifest:
        {{name: bootstrap-pixi, version: 0.1.0, produces: bootstrap, effect: pure}}
  plugins/pixi-install:
    op: fetch-verify
    config:
      kind: plugin
      url: {url}/pixi-install
      sha256: "{pixi_install_sha}"
      manifest:
        name: pixi-install
        version: 0.1.0
        produces: tool
        effect: pure
        consumes: {{bootstrap: {{}}}}
  bootstrap:
    op: bootstrap-pixi
    config: {{version: "0.77.0", url: {url}/pixi-dist, sha256: "{pixi_dist_sha}"}}
  tools/copier:
    op: pixi-install
    config: {{package: copier, version: "9.17.2"}}
  render/scaffold:
    op: command
    consumes: [tool]
    config:
      kind: file-tree
      effect: pure
      cmd:
        [sh, -c, 'test "$(copier)" = "copier 9.17.2" && mkdir -p out
          && copier > out/copier.txt']
"""


@pytest.fixture
def pixi_world(world, tmp_path, fake_pixi_source):
    docroot = tmp_path / "www"
    docroot.mkdir()
    artifacts = {
        "bootstrap-pixi": build_payload(PLUGINS_DIR / "bootstrap_pixi.py"),
        "pixi-install": build_payload(PLUGINS_DIR / "pixi_install.py"),
        "pixi-dist": fake_pixi_source.encode(),
    }
    for name, data in artifacts.items():
        (docroot / name).write_bytes(data)
    handler = partial(SimpleHTTPRequestHandler, directory=str(docroot))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    (world.config_dir / "freckles.yaml").write_text(
        PIXI_ROUTE.format(
            url=f"http://127.0.0.1:{server.server_port}",
            bootstrap_pixi_sha=hashlib.sha256(artifacts["bootstrap-pixi"]).hexdigest(),
            pixi_install_sha=hashlib.sha256(artifacts["pixi-install"]).hexdigest(),
            pixi_dist_sha=hashlib.sha256(artifacts["pixi-dist"]).hexdigest(),
        )
    )
    yield world, server
    server.shutdown()


def test_one_heal_walks_the_pixi_route_from_zero(pixi_world):
    world, _ = pixi_world

    result = world.invoke("heal")

    assert result.exit_code == 0, result.output
    for node in (
        "plugins/bootstrap-pixi",
        "plugins/pixi-install",
        "bootstrap",
        "tools/copier",
        "render/scaffold",
    ):
        assert node in result.output
    # The sha256 lock landed beside the per-tool manifest.
    workspace = world.data_dir / "envs" / "pixi-workspaces" / "copier" / "9.17.2"
    assert (workspace / "pixi.lock").exists()


def test_second_heal_is_current_with_the_server_gone(pixi_world):
    """Every acquisition is pinned: nothing refetches, nothing reinstalls."""
    world, server = pixi_world
    world.invoke("heal")
    server.shutdown()

    result = world.invoke("heal")

    assert result.exit_code == 0, result.output
    assert "healed" not in result.output

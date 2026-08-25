"""The mise route through the real CLI (M6): the design.md §11 bootstrap chain.

One `freckles heal` from zero: fetch-verify acquires both standard-plugin
payloads, bootstrap-mise realizes the (fake) mise, mise-install realizes a
copier-shaped tool, and a command node proves the tool answers to its bare
name on the constructed PATH. Everything is pinned, so a second heal is
fully current — even with the server gone.
"""

import hashlib
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from freckles.sdk.build import build_payload

PLUGINS_DIR = Path(__file__).parent.parent.parent / "plugins"

# The wrapped command attests the tool: a wrong or missing `copier` on the
# constructed PATH fails the run, so a green heal cannot be vacuous.
MISE_ROUTE = """
nodes:
  plugins/bootstrap-mise:
    op: fetch-verify
    config:
      kind: plugin
      url: {url}/bootstrap-mise
      sha256: "{bootstrap_mise_sha}"
      manifest:
        {{name: bootstrap-mise, version: 0.1.0, produces: bootstrap, effect: pure}}
  plugins/mise-install:
    op: fetch-verify
    config:
      kind: plugin
      url: {url}/mise-install
      sha256: "{mise_install_sha}"
      manifest:
        name: mise-install
        version: 0.1.0
        produces: tool
        effect: pure
        consumes: {{bootstrap: {{}}}}
  bootstrap:
    op: bootstrap-mise
    config: {{version: "2025.8.1", url: {url}/mise-dist, sha256: "{mise_dist_sha}"}}
  tools/copier:
    op: mise-install
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
def mise_world(world, tmp_path, fake_mise_source):
    docroot = tmp_path / "www"
    docroot.mkdir()
    artifacts = {
        "bootstrap-mise": build_payload(PLUGINS_DIR / "bootstrap_mise.py"),
        "mise-install": build_payload(PLUGINS_DIR / "mise_install.py"),
        "mise-dist": fake_mise_source.encode(),
    }
    for name, data in artifacts.items():
        (docroot / name).write_bytes(data)
    handler = partial(SimpleHTTPRequestHandler, directory=str(docroot))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    (world.config_dir / "freckles.yaml").write_text(
        MISE_ROUTE.format(
            url=f"http://127.0.0.1:{server.server_port}",
            bootstrap_mise_sha=hashlib.sha256(artifacts["bootstrap-mise"]).hexdigest(),
            mise_install_sha=hashlib.sha256(artifacts["mise-install"]).hexdigest(),
            mise_dist_sha=hashlib.sha256(artifacts["mise-dist"]).hexdigest(),
        )
    )
    yield world, server
    server.shutdown()


def test_one_heal_walks_the_bootstrap_chain_from_zero(mise_world):
    world, _ = mise_world

    result = world.invoke("heal")

    assert result.exit_code == 0, result.output
    for node in (
        "plugins/bootstrap-mise",
        "plugins/mise-install",
        "bootstrap",
        "tools/copier",
        "render/scaffold",
    ):
        assert node in result.output
    # The tool answered to its bare name: the attesting command ingested it.
    assert (world.data_dir / "envs" / "mise" / "2025.8.1" / "bin" / "mise").exists()


def test_second_heal_is_current_with_the_server_gone(mise_world):
    """Every acquisition is pinned: nothing refetches, nothing reinstalls."""
    world, server = mise_world
    world.invoke("heal")
    server.shutdown()

    result = world.invoke("heal")

    assert result.exit_code == 0, result.output
    assert "healed" not in result.output

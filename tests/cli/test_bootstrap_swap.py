"""The swappable-bootstrap contract, tested not asserted (The v1 cut, M7).

Tool claims are route-independent — {kind, tool, version, platform}, no
provenance in identity — so swapping bootstrap-mise → bootstrap-pixi
re-derives the tool but mints the byte-identical claim, and downstream
consumers see the same input CID and stay current: design.md §10's
extensional ripple-stop, applied to the bootstrap route itself.
"""

import hashlib
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from freckles.sdk.build import build_payload

PLUGINS_DIR = Path(__file__).parent.parent.parent / "plugins"

# The consumer is byte-identical across routes — its derivation may only
# change if the tool claim it consumes changes.
SHARED_CONSUMER = """
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

MISE_LEG = """
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
"""

PIXI_LEG = """
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
"""


@pytest.fixture
def swap_world(world, tmp_path, fake_mise_source, fake_pixi_source):
    docroot = tmp_path / "www"
    docroot.mkdir()
    artifacts = {
        "bootstrap-mise": build_payload(PLUGINS_DIR / "bootstrap_mise.py"),
        "mise-install": build_payload(PLUGINS_DIR / "mise_install.py"),
        "mise-dist": fake_mise_source.encode(),
        "bootstrap-pixi": build_payload(PLUGINS_DIR / "bootstrap_pixi.py"),
        "pixi-install": build_payload(PLUGINS_DIR / "pixi_install.py"),
        "pixi-dist": fake_pixi_source.encode(),
    }
    for name, data in artifacts.items():
        (docroot / name).write_bytes(data)
    handler = partial(SimpleHTTPRequestHandler, directory=str(docroot))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    shas = {
        f"{name.replace('-', '_')}_sha": hashlib.sha256(data).hexdigest()
        for name, data in artifacts.items()
    }
    mise_route = MISE_LEG.format(url=url, **shas) + SHARED_CONSUMER
    pixi_route = PIXI_LEG.format(url=url, **shas) + SHARED_CONSUMER
    yield world, mise_route, pixi_route
    server.shutdown()


def claim_cid(world, node: str) -> str:
    output = world.invoke("show", node).output
    return output.splitlines()[0].split()[2]


def test_swapping_the_route_remints_the_claim_and_spares_downstream(swap_world):
    world, mise_route, pixi_route = swap_world
    (world.config_dir / "freckles.yaml").write_text(mise_route)
    assert world.invoke("heal").exit_code == 0
    cid_via_mise = claim_cid(world, "tools/copier")

    (world.config_dir / "freckles.yaml").write_text(pixi_route)
    result = world.invoke("heal")

    assert result.exit_code == 0, result.output
    # The tool re-derives through the new route...
    assert "tools/copier  healed" in result.output
    # ...mints the byte-identical claim...
    assert claim_cid(world, "tools/copier") == cid_via_mise
    # ...and the ripple stops dead: the consumer never re-runs.
    assert "render/scaffold  healed" not in result.output

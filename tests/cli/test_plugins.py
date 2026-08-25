"""Plugin acquisition through the DAG (M5): fetch → re-resolve → run, one heal."""

import hashlib
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

GREETER = b"""#!/usr/bin/env python3
import json, sys
json.load(sys.stdin)
json.dump({"schema": 1,
           "claim": {"schema": 1, "kind": "greeting", "text": "hello"}},
          sys.stdout)
"""


@pytest.fixture
def plugin_world(world, tmp_path):
    docroot = tmp_path / "www"
    docroot.mkdir()
    (docroot / "greeter-plugin").write_bytes(GREETER)
    handler = partial(SimpleHTTPRequestHandler, directory=str(docroot))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    sha = hashlib.sha256(GREETER).hexdigest()
    (world.config_dir / "freckles.yaml").write_text(
        f"""
nodes:
  plugins/greeter:
    op: fetch-verify
    config:
      kind: plugin
      url: http://127.0.0.1:{server.server_port}/greeter-plugin
      sha256: "{sha}"
      manifest: {{name: greeter, version: 0.1.0, produces: greeting, effect: pure}}
  hello/world:
    op: greeter
    config: {{}}
"""
    )
    yield world, server
    server.shutdown()


def test_day1_heal_acquires_the_plugin_and_runs_its_node(plugin_world):
    world, _ = plugin_world

    result = world.invoke("heal", "--yes")

    assert result.exit_code == 0
    assert "plugins/greeter" in result.output
    assert "hello/world" in result.output
    assert "greeting" in world.invoke("show", "hello/world").output


def test_second_heal_is_current_even_with_the_server_gone(plugin_world):
    """fetch-verify is not a source: the checksum pins the world, no refetch."""
    world, server = plugin_world
    world.invoke("heal", "--yes")
    server.shutdown()

    result = world.invoke("heal", "--yes")

    assert result.exit_code == 0

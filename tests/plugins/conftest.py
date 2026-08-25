"""Standard-plugin tests: built payloads spawned through the real runner.

The payload under test is exactly what CI publishes — `plugins/<script>.py`
run through `freckles.sdk.build` — stored as a plugin claim the way
fetch-verify mints one, then spawned as a real subprocess. The localhost
lab keeps downloads hermetic.
"""

import threading
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from freckles.documents import SCHEMA, cid_for_blob
from freckles.runner import RunContext
from freckles.sdk.build import build_payload
from freckles.state import AnnotationsIndex, StateDb
from freckles.store import SqliteStore, put_doc

PLUGINS_DIR = Path(__file__).parent.parent.parent / "plugins"


@pytest.fixture
def ctx(tmp_path):
    store = SqliteStore(tmp_path / "store.sqlite")
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    workspace_root = tmp_path / "run"
    workspace_root.mkdir()
    return RunContext(
        store=store,
        annotations=AnnotationsIndex(StateDb(tmp_path / "state.sqlite")),
        config_dir=config_dir,
        freckles_version="0.0.0-test",
        workspace_root=workspace_root,
        envs_root=tmp_path / "envs",
    )


@pytest.fixture
def install_plugin(ctx):
    """Build a standard plugin's payload and store its claim, as fetch-verify would."""

    def _install(script_name, **manifest):
        payload = build_payload(PLUGINS_DIR / script_name)
        payload_cid = cid_for_blob(payload)
        ctx.store.put(payload_cid, payload)
        claim = {"schema": SCHEMA, "kind": "plugin", "payload": payload_cid, **manifest}
        claim.setdefault("entrypoint", claim.get("name"))
        return put_doc(ctx.store, claim)

    return _install


@dataclass
class Lab:
    docroot: Path
    url: str  # base, no trailing slash


@pytest.fixture
def lab(tmp_path):
    docroot = tmp_path / "www"
    docroot.mkdir()
    handler = partial(SimpleHTTPRequestHandler, directory=str(docroot))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield Lab(docroot=docroot, url=f"http://127.0.0.1:{server.server_port}")
    server.shutdown()


@pytest.fixture
def realized_mise(ctx, fake_mise_source):
    """A realized bootstrap claim whose annotated path is the fake mise."""
    binary = ctx.envs_root / "mise" / "2025.8.1" / "bin" / "mise"
    binary.parent.mkdir(parents=True)
    binary.write_text(fake_mise_source)
    binary.chmod(0o755)
    return {
        "bootstrap": {
            "cid": "bafyre-test",
            "claim": {
                "schema": SCHEMA,
                "kind": "bootstrap",
                "tool": "mise",
                "version": "2025.8.1",
                "platform": "linux-x64",
            },
            "annotations": {"path": str(binary)},
        }
    }


@pytest.fixture
def load_plugin_module():
    """Import a plugin script in-process (for its pure helpers only)."""
    import importlib.util

    def _load(name: str):
        spec = importlib.util.spec_from_file_location(name, PLUGINS_DIR / f"{name}.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return _load

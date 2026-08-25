"""Runner test fixtures: a live RunContext and a fake-plugin factory.

Fake plugins are stdlib-only Python scripts spawned as real subprocesses
speaking DAG-JSON on stdio ("Testing strategy") — the designed substitution
point; nothing internal is ever mocked.
"""

import pytest

from freckles.documents import SCHEMA, cid_for_blob
from freckles.runner import RunContext
from freckles.state import AnnotationsIndex, StateDb
from freckles.store import SqliteStore, put_doc


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
    )


@pytest.fixture
def make_plugin(ctx):
    """Store a fake plugin (claim + payload blob); returns the claim's CID."""

    def _make(name, body, produces="thing", effect="pure", verify=False):
        payload = f"#!/usr/bin/env python3\n{body}\n".encode()
        payload_cid = cid_for_blob(payload)
        ctx.store.put(payload_cid, payload)
        manifest = {
            "schema": SCHEMA,
            "kind": "plugin",
            "name": name,
            "version": "0.0.1",
            "produces": produces,
            "effect": effect,
            "entrypoint": name,
            "payload": payload_cid,
        }
        if verify:
            manifest["verify"] = True  # the minimal verify entrypoint (M4)
        return put_doc(ctx.store, manifest)

    return _make

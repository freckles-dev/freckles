"""The backend contract suite: one parametrized suite every store backend passes.

Both v1 backends run it: sqlite (default) and folder (inspection).
Covers block/ref semantics, reopen persistence, and gc (refs as the only
roots, extract_links traversal, two-phase unreferenced-since grace).
"""

import pytest

from freckles.defaults import GC_GRACE
from freckles.documents import cid_for_blob
from freckles.store import (
    FolderStore,
    SqliteStore,
    extract_links,
    get_doc,
    put_blob,
    put_doc,
)


@pytest.fixture(params=["sqlite", "folder"])
def backend_factory(request, tmp_path):
    """Opens the same store on every call — reopening is part of the contract."""
    if request.param == "sqlite":
        return lambda: SqliteStore(tmp_path / "store.sqlite")
    if request.param == "folder":
        return lambda: FolderStore(tmp_path / "store")
    raise AssertionError(f"unknown backend {request.param}")


@pytest.fixture
def backend(backend_factory):
    return backend_factory()


def test_put_get_round_trips(backend):
    cid = cid_for_blob(b"hello")
    backend.put(cid, b"hello")
    assert backend.get(cid) == b"hello"


def test_get_missing_raises_keyerror(backend):
    with pytest.raises(KeyError):
        backend.get(cid_for_blob(b"absent"))


def test_has(backend):
    cid = cid_for_blob(b"x")
    assert not backend.has(cid)
    backend.put(cid, b"x")
    assert backend.has(cid)


def test_reput_is_idempotent(backend):
    cid = cid_for_blob(b"same")
    backend.put(cid, b"same")
    backend.put(cid, b"same")
    assert backend.cids() == [cid]


def test_cids_lists_all_blocks(backend):
    cids = {put_blob(backend, data) for data in (b"a", b"b", b"c")}
    assert set(backend.cids()) == cids


def test_refs_set_get_update_list(backend):
    a, b = cid_for_blob(b"a"), cid_for_blob(b"b")
    assert backend.get_ref("cfg/demo/current") is None
    backend.set_ref("cfg/demo/current", a)
    assert backend.get_ref("cfg/demo/current") == a
    backend.set_ref("cfg/demo/current", b)  # refs are mutable
    assert backend.get_ref("cfg/demo/current") == b
    backend.set_ref("cfg/demo/nodes/values", a)
    assert backend.refs() == {
        "cfg/demo/current": b,
        "cfg/demo/nodes/values": a,
    }


def test_doc_helpers_round_trip(backend):
    doc = {"schema": 1, "kind": "values", "key": "apps"}
    cid = put_doc(backend, doc)
    assert get_doc(backend, cid) == doc


def test_gc_first_pass_keeps_unreachable_within_grace(backend):
    blob = put_blob(backend, b"payload")
    doc = put_doc(backend, {"schema": 1, "kind": "file-tree", "content": blob})
    backend.set_ref("cfg/demo/nodes/tree", doc)
    orphan = put_blob(backend, b"orphan bytes")

    report = backend.gc(extract_links, GC_GRACE)

    assert report.roots == 1
    assert report.reachable == 2  # the rooted doc and the blob it links
    assert report.unreferenced == 1
    assert (report.kept, report.collected) == (1, 0)
    assert report.freed_bytes == 0
    assert backend.has(orphan)  # grace holds it


def test_persistence_across_reopen(backend_factory):
    first = backend_factory()
    cid = put_blob(first, b"durable")
    first.set_ref("r", cid)
    first.close()

    second = backend_factory()
    assert second.get(cid) == b"durable"
    assert second.get_ref("r") == cid

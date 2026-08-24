"""Seam tests for machine-local state: derivation index and annotations index."""

import pytest

from freckles.documents import cid_for_blob
from freckles.state import AnnotationsIndex, DerivationIndex, StateDb


@pytest.fixture
def db(tmp_path):
    return StateDb(tmp_path / "state.sqlite")


def test_derivation_index_lookup_miss_then_hit(db):
    index = DerivationIndex(db)
    derivation, claim = cid_for_blob(b"d"), cid_for_blob(b"c")
    assert index.lookup(derivation) is None
    index.record(derivation, claim)
    assert index.lookup(derivation) == claim


def test_derivation_index_is_prunable_and_rebuildable(db):
    index = DerivationIndex(db)
    derivation, claim = cid_for_blob(b"d"), cid_for_blob(b"c")
    index.record(derivation, claim)
    index.prune()
    assert index.lookup(derivation) is None
    index.record(derivation, claim)  # rebuilding is just recording again
    assert index.lookup(derivation) == claim


def test_annotations_default_empty_and_round_trip(db):
    index = AnnotationsIndex(db)
    claim = cid_for_blob(b"claim")
    assert index.get(claim) == {}
    index.set(claim, {"workspace": "/tmp/x", "host": "laptop"})
    assert index.get(claim) == {"workspace": "/tmp/x", "host": "laptop"}


def test_annotations_update_under_unchanged_claim(db):
    index = AnnotationsIndex(db)
    claim = cid_for_blob(b"claim")
    index.set(claim, {"kubeconfig": "old"})
    index.set(claim, {"kubeconfig": "new"})
    assert index.get(claim) == {"kubeconfig": "new"}

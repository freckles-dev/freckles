"""Pytest configuration and shared fixtures for freckles tests."""

from pathlib import Path

import pytest

# Installs the dbg/DBG/ic/insp/wat builtins (and activates snoop) for all tests.
import freckles._debug  # noqa: F401

CONFORMANCE = Path(__file__).parent.parent / "conformance"


def hashberg_encode(document: dict) -> bytes:
    """Encode a value-model document with the hashberg pair (dag-cbor/multiformats).

    The independent second encoder of the dual-encoder cross-check: tests
    assert its bytes match the production (libipld) encoding exactly.
    """
    import dag_cbor
    from multiformats import CID as HbCID

    from freckles.documents import Cid

    def lower(value):
        if isinstance(value, Cid):
            return HbCID.decode(str(value))
        if isinstance(value, dict):
            return {k: lower(v) for k, v in value.items()}
        if isinstance(value, list):
            return [lower(v) for v in value]
        return value

    return dag_cbor.encode(lower(document))


@pytest.fixture
def encode_checked():
    """Encode a store document with BOTH encoders, asserting byte-identity.

    Seam tests mint documents through this wherever practical, making the
    whole suite a rolling cross-implementation check ("Testing strategy").
    Returns (bytes, Cid) exactly like `documents.encode`.
    """
    from freckles.documents import encode

    def _encode(document: dict):
        data, cid = encode(document)
        assert hashberg_encode(document) == data, (
            "libipld and hashberg dag-cbor encodings diverge"
        )
        return data, cid

    return _encode

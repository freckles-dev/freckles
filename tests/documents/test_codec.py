"""Codec seam tests: the value model, CIDs, and the DAG-JSON wire."""

import pytest

from freckles.documents import (
    Cid,
    Derivation,
    Provenance,
    Resolution,
    ResolvedNode,
    cid_for_blob,
    decode,
    encode,
    from_wire,
    to_wire,
)


def test_blob_cid_uses_raw_codec():
    cid = cid_for_blob(b"hello")
    assert cid.codec == 0x55
    assert str(cid).startswith("bafkrei")


def test_document_cid_uses_dag_cbor_codec(encode_checked):
    _, cid = encode_checked({"schema": 1, "kind": "values", "key": "apps"})
    assert cid.codec == 0x71
    assert str(cid).startswith("bafyrei")


def test_cid_parse_round_trips():
    cid = cid_for_blob(b"content")
    assert Cid.parse(str(cid)) == cid


def test_links_survive_encode_decode(encode_checked):
    inner = cid_for_blob(b"blob")
    data, _ = encode_checked({"schema": 1, "kind": "values", "content": inner})
    assert decode(data)["content"] == inner


def test_floats_are_rejected():
    with pytest.raises(TypeError):
        encode({"schema": 1, "kind": "x", "ratio": 0.5})


def test_wire_link_and_bytes_forms():
    cid = cid_for_blob(b"x")
    wire = to_wire({"link": cid, "data": b"\x01\x02"})
    parsed = from_wire(wire)
    assert parsed["link"] == cid
    assert parsed["data"] == b"\x01\x02"
    assert '"/"' in wire


def test_derivation_document_shape(encode_checked):
    claim_cid = cid_for_blob(b"claim")
    derivation = Derivation(
        plugin={"builtin": "import-values", "freckles": "0.1.0"},
        config={"file": "values.yaml", "key": "apps"},
        inputs={"values": claim_cid},
    )
    doc = derivation.to_doc()
    assert set(doc) == {"schema", "plugin", "config", "inputs"}
    encode_checked(doc)


def test_provenance_document_shape(encode_checked):
    a, b = cid_for_blob(b"a"), cid_for_blob(b"b")
    doc = Provenance(derivation=a, outcome=b).to_doc()
    assert set(doc) == {"schema", "derivation", "outcome"}
    encode_checked(doc)


def test_resolution_round_trips_through_docs(encode_checked):
    resolution = Resolution(
        config_snapshot=cid_for_blob(b"cfg"),
        nodes={
            "values/apps": ResolvedNode(
                plugin={"builtin": "import-values", "freckles": "0.1.0"},
                produces="values",
                effect="pure",
                config={"file": "v.yaml", "key": "apps"},
                consumes={},
            )
        },
    )
    doc = resolution.to_doc()
    data, _ = encode_checked(doc)
    assert Resolution.from_doc(decode(data)) == resolution

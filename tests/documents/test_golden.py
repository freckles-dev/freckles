"""The golden-CID suite: every conformance fixture round-trips to its committed CID.

Three assertions per fixture ("Testing strategy"): codec round-trip reproduces
the committed CID; libipld and the hashberg pair agree byte-for-byte (via the
`encode_checked` fixture); the regenerate-and-diff check runs in CI
(freckles-guardrails workflow).
"""

from pathlib import Path

import pytest

from freckles.documents import decode, from_wire, to_wire

GOLDEN = Path(__file__).parents[2] / "conformance" / "golden"


def golden_cids() -> dict[str, str]:
    cids: dict[str, str] = {}
    for line in (GOLDEN / "CIDS.txt").read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2 and not parts[1].startswith("blob:"):
            cids[parts[1]] = parts[0]
    return cids


FIXTURES = sorted(p.name.removesuffix(".dagjson.json") for p in GOLDEN.glob("*.json"))


def test_manifest_covers_all_fixtures():
    assert set(golden_cids()) == set(FIXTURES)


@pytest.mark.parametrize("name", FIXTURES)
def test_golden_fixture(name, encode_checked):
    document = from_wire((GOLDEN / f"{name}.dagjson.json").read_text())

    data, cid = encode_checked(document)  # asserts both encoders agree
    assert str(cid) == golden_cids()[name], f"{name}: CID drifted"

    assert decode(data) == document, f"{name}: decode is not the inverse of encode"
    assert from_wire(to_wire(document)) == document, f"{name}: wire round-trip"

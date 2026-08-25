"""freckles.sdk: thin wire helpers for plugin authors (public v1 surface).

Sugar, never contract (design.md §6) — everything here round-trips through
the same DAG-JSON codecs the process protocol speaks.
"""

import io

from freckles.documents import from_wire, to_wire
from freckles.sdk import emit_error, emit_outcome, read_request


def test_read_request_parses_the_wire_document():
    request = {
        "schema": 1,
        "node": {"name": "hello/world", "config": {"greeting": "hi"}},
        "inputs": {},
        "workspace": {"dir": "/tmp/ws", "path": ["/usr/bin"]},
    }

    parsed = read_request(io.StringIO(to_wire(request)))

    assert parsed == request


def test_emit_outcome_stamps_schema_and_round_trips():
    out = io.StringIO()

    emit_outcome({"kind": "greeting", "text": "hi"}, ingest="out", stream=out)

    assert from_wire(out.getvalue()) == {
        "schema": 1,
        "claim": {"schema": 1, "kind": "greeting", "text": "hi"},
        "ingest": "out",
    }


def test_emit_outcome_carries_annotations():
    out = io.StringIO()

    emit_outcome(
        {"schema": 1, "kind": "deployed-site"},
        annotations={"deployed_at": "2026-08-25T12:00:00Z"},
        stream=out,
    )

    document = from_wire(out.getvalue())
    assert document["annotations"] == {"deployed_at": "2026-08-25T12:00:00Z"}
    assert "ingest" not in document


def test_emit_error_shapes_the_structured_error():
    out = io.StringIO()

    emit_error("disk on fire", detail="smoke everywhere", exit_code=3, stream=out)

    assert from_wire(out.getvalue()) == {
        "schema": 1,
        "error": {
            "message": "disk on fire",
            "detail": "smoke everywhere",
            "exit_code": 3,
        },
    }

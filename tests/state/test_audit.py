"""The audit log: append-only JSON-lines answering "what was deployed when".

Field list finalized by M3 (the named design act): derivation + claim CIDs,
exit code, duration, resolved secret names — logs stay out (v1 cut).
"""

import json

from freckles.state import AuditLog, AuditRecord


def test_append_and_iterate_round_trip(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    log.append(
        AuditRecord(
            config="demo",
            node="deploy/site",
            op="command @ freckles 0.1.0",
            derivation="bafyreiderivation",
            claim="bafyreiclaim",
            ok=True,
            exit_code=0,
            duration_ms=412,
            secrets=["admin_password"],
        )
    )
    log.append(
        AuditRecord(
            config="demo",
            node="render/site",
            op="command @ freckles 0.1.0",
            derivation="bafyreiother",
            claim="bafyreiother2",
            ok=True,
            exit_code=0,
            duration_ms=7,
            secrets=[],
        )
    )

    records = log.records()
    assert [r["node"] for r in records] == ["deploy/site", "render/site"]
    first = records[0]
    assert first["schema"] == 1
    assert first["ts"].endswith("Z")
    assert first["derivation"] == "bafyreiderivation"
    assert first["claim"] == "bafyreiclaim"
    assert (first["ok"], first["exit_code"], first["duration_ms"]) == (True, 0, 412)
    assert first["secrets"] == ["admin_password"]
    assert "error" not in first


def test_failure_records_carry_error_and_no_claim(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    log.append(
        AuditRecord(
            config="demo",
            node="deploy/site",
            op="command @ freckles 0.1.0",
            derivation="bafyreiderivation",
            claim=None,
            ok=False,
            exit_code=3,
            duration_ms=90,
            secrets=[],
            error="plugin exited 3",
        )
    )

    (record,) = log.records()
    assert record["ok"] is False
    assert record["claim"] is None  # failures never mint outcomes
    assert record["error"] == "plugin exited 3"


def test_append_only_across_reopen(tmp_path):
    path = tmp_path / "audit.jsonl"
    AuditLog(path).append(
        AuditRecord(
            config="demo",
            node="values/apps",
            op="import-values @ freckles 0.1.0",
            derivation="bafyreid1",
            claim="bafyreic1",
            ok=True,
            exit_code=0,
            duration_ms=3,
            secrets=[],
        )
    )
    AuditLog(path).append(
        AuditRecord(
            config="demo",
            node="values/apps",
            op="import-values @ freckles 0.1.0",
            derivation="bafyreid2",
            claim="bafyreic2",
            ok=True,
            exit_code=0,
            duration_ms=4,
            secrets=[],
        )
    )

    lines = path.read_text().strip().splitlines()
    assert len(lines) == 2  # one JSON document per line, nothing rewritten
    assert [json.loads(line)["derivation"] for line in lines] == [
        "bafyreid1",
        "bafyreid2",
    ]

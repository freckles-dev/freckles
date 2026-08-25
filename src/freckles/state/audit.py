# audit.py
#
# Copyright (c) 2026 Markus Binsteiner
# All rights reserved.
#
# SPDX-License-Identifier: AGPL-3.0-only
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""The audit log: append-only JSON-lines, local, never consumed downstream.

It answers "what was deployed when" even after gc has collected the blocks
(design.md §8). Field list finalized by M3: derivation + claim CIDs, exit
code, duration, resolved secret *names* — plaintext never lands here, and
run logs stay out (v1 cut, dated note in §8).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = 1


@dataclass(frozen=True)
class AuditRecord:
    """One run — pure or effectful, success or failure."""

    config: str
    node: str
    op: str
    derivation: str
    claim: str | None  # None on failure: failures never mint outcomes
    ok: bool
    exit_code: int
    duration_ms: int
    secrets: list[str]
    error: str | None = None


class AuditLog:
    """One JSON-lines file, append-only; every append is one flushed line."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def append(self, record: AuditRecord, ts: datetime | None = None) -> None:
        stamped = ts if ts is not None else datetime.now(UTC)
        line: dict[str, Any] = {
            "schema": SCHEMA,
            "ts": stamped.isoformat().replace("+00:00", "Z"),
            "config": record.config,
            "node": record.node,
            "op": record.op,
            "derivation": record.derivation,
            "claim": record.claim,
            "ok": record.ok,
            "exit_code": record.exit_code,
            "duration_ms": record.duration_ms,
            "secrets": record.secrets,
        }
        if record.error is not None:
            line["error"] = record.error
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(line) + "\n")

    def records(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        return [
            json.loads(line)
            for line in self._path.read_text(encoding="utf-8").splitlines()
            if line
        ]

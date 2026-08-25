# db.py
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

"""Machine-local state: the derivation index and the annotations index.

Both live in one sqlite file on the design's "out" side — never in the CAS.
The derivation index is a prunable, rebuildable cache and never a GC root.
The audit log lives beside them as JSON-lines (audit.py); distrust marks
join with the drift milestone.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from freckles.documents import Cid


class StateDb:
    def __init__(self, path: str | Path) -> None:
        self._conn = sqlite3.connect(str(path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        with self._conn:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS derivations "
                "(derivation_cid TEXT PRIMARY KEY, claim_cid TEXT)"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS annotations "
                "(claim_cid TEXT PRIMARY KEY, data TEXT)"
            )

    def close(self) -> None:
        self._conn.close()


class DerivationIndex:
    """derivation hash (CID) -> claim CID. Lookup, record, prune."""

    def __init__(self, db: StateDb) -> None:
        self._conn = db._conn

    def lookup(self, derivation: Cid) -> Cid | None:
        row = self._conn.execute(
            "SELECT claim_cid FROM derivations WHERE derivation_cid = ?",
            (str(derivation),),
        ).fetchone()
        return Cid.parse(row[0]) if row else None

    def record(self, derivation: Cid, claim: Cid) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO derivations (derivation_cid, claim_cid) VALUES (?, ?) "
                "ON CONFLICT(derivation_cid) DO UPDATE SET claim_cid = excluded.claim_cid",
                (str(derivation), str(claim)),
            )

    def prune(self) -> None:
        """Drop the whole cache — always safe: entries are rebuildable."""
        with self._conn:
            self._conn.execute("DELETE FROM derivations")


class AnnotationsIndex:
    """claim CID -> annotations (free-form, machine-local, never travels)."""

    def __init__(self, db: StateDb) -> None:
        self._conn = db._conn

    def get(self, claim: Cid) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT data FROM annotations WHERE claim_cid = ?", (str(claim),)
        ).fetchone()
        return json.loads(row[0]) if row else {}

    def redacted(self, claim: Cid) -> dict[str, Any]:
        """The display view: secret-marked entries never leave as values.

        Effectful runs receive the full annotations via `get`; everything
        freckles *prints* goes through here (design.md §9).
        """
        return {
            key: "<secret — not shown>"
            if isinstance(value, dict) and value.get("secret")
            else value
            for key, value in self.get(claim).items()
        }

    def set(self, claim: Cid, annotations: dict[str, Any]) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO annotations (claim_cid, data) VALUES (?, ?) "
                "ON CONFLICT(claim_cid) DO UPDATE SET data = excluded.data",
                (str(claim), json.dumps(annotations)),
            )

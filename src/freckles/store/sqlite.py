# sqlite.py
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

"""The sqlite store backend (default, design.md §7)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from freckles.documents import Cid


class SqliteStore:
    """Blocks and refs in one sqlite file, WAL mode."""

    def __init__(self, path: str | Path) -> None:
        self._conn = sqlite3.connect(str(path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        with self._conn:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS blocks (cid TEXT PRIMARY KEY, data BLOB)"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS refs (name TEXT PRIMARY KEY, cid TEXT)"
            )

    def put(self, cid: Cid, data: bytes) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO blocks (cid, data) VALUES (?, ?)",
                (str(cid), data),
            )

    def get(self, cid: Cid) -> bytes:
        row = self._conn.execute(
            "SELECT data FROM blocks WHERE cid = ?", (str(cid),)
        ).fetchone()
        if row is None:
            raise KeyError(str(cid))
        return row[0]

    def has(self, cid: Cid) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM blocks WHERE cid = ?", (str(cid),)
        ).fetchone()
        return row is not None

    def cids(self) -> list[Cid]:
        rows = self._conn.execute("SELECT cid FROM blocks ORDER BY cid").fetchall()
        return [Cid.parse(r[0]) for r in rows]

    def set_ref(self, name: str, cid: Cid) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT INTO refs (name, cid) VALUES (?, ?) "
                "ON CONFLICT(name) DO UPDATE SET cid = excluded.cid",
                (name, str(cid)),
            )

    def get_ref(self, name: str) -> Cid | None:
        row = self._conn.execute(
            "SELECT cid FROM refs WHERE name = ?", (name,)
        ).fetchone()
        return Cid.parse(row[0]) if row else None

    def refs(self) -> dict[str, Cid]:
        rows = self._conn.execute("SELECT name, cid FROM refs ORDER BY name").fetchall()
        return {name: Cid.parse(cid) for name, cid in rows}

    def close(self) -> None:
        self._conn.close()

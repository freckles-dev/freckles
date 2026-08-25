# folder.py
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

"""The folder store backend (inspection, design.md §7).

Everything is a plain file: `blocks/<cid>` holds a block's bytes, and a
ref's path-like name maps to a file under `refs/` whose content is the CID
string — the whole store stays greppable and cattable.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from freckles.documents import Cid
from freckles.store.base import ExtractLinks, GcReport, compute_reachable


class FolderStore:
    """Blocks and refs as plain files under one root directory."""

    def __init__(self, path: str | Path) -> None:
        self._root = Path(path)
        self._blocks = self._root / "blocks"
        self._refs = self._root / "refs"
        self._blocks.mkdir(parents=True, exist_ok=True)
        self._refs.mkdir(parents=True, exist_ok=True)

    def put(self, cid: Cid, data: bytes) -> None:
        target = self._blocks / str(cid)
        if target.exists():
            return  # blocks are immutable: re-put is a no-op
        self._write_atomic(target, data)

    def get(self, cid: Cid) -> bytes:
        target = self._blocks / str(cid)
        if not target.exists():
            raise KeyError(str(cid))
        return target.read_bytes()

    def has(self, cid: Cid) -> bool:
        return (self._blocks / str(cid)).exists()

    def cids(self) -> list[Cid]:
        return [Cid.parse(p.name) for p in sorted(self._blocks.iterdir())]

    def set_ref(self, name: str, cid: Cid) -> None:
        target = self._refs.joinpath(*name.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        self._write_atomic(target, str(cid).encode())

    def get_ref(self, name: str) -> Cid | None:
        target = self._refs.joinpath(*name.split("/"))
        if not target.exists():
            return None
        return Cid.parse(target.read_text())

    def refs(self) -> dict[str, Cid]:
        return {
            p.relative_to(self._refs).as_posix(): Cid.parse(p.read_text())
            for p in sorted(self._refs.rglob("*"))
            if p.is_file()
        }

    def gc(
        self,
        extract_links: ExtractLinks,
        grace: timedelta,
        now: datetime | None = None,
    ) -> GcReport:
        roots = self.refs()
        reachable = compute_reachable(list(roots.values()), self.get, extract_links)
        unreferenced = [cid for cid in self.cids() if cid not in reachable]
        return GcReport(
            roots=len(roots),
            reachable=len(self.cids()) - len(unreferenced),
            unreferenced=len(unreferenced),
            kept=len(unreferenced),
            collected=0,
            freed_bytes=0,
        )

    def close(self) -> None:
        pass  # nothing held open

    def _write_atomic(self, target: Path, data: bytes) -> None:
        tmp = target.with_name(target.name + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, target)

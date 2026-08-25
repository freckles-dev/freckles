# base.py
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

"""The backend seam: codec-ignorant block + ref storage (design.md §7).

Backends store opaque bytes under CID strings and mutable name -> CID refs;
they never encode, decode, or interpret. gc keeps them ignorant too: the
caller passes `extract_links`, so traversal knowledge stays in the store
layer while the backend only walks, marks, and deletes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from freckles.documents import Cid

ExtractLinks = Callable[[Cid, bytes], list[Cid]]


@dataclass(frozen=True)
class GcReport:
    """One gc pass, counted the way `freckles gc` reports it (scene 8)."""

    roots: int
    reachable: int
    unreferenced: int
    kept: int
    collected: int
    freed_bytes: int


def gc_pass(
    backend: StoreBackend,
    extract_links: ExtractLinks,
    grace: timedelta,
    now: datetime | None,
    *,
    marks: dict[Cid, datetime],
    set_mark: Callable[[Cid, datetime], None],
    clear_mark: Callable[[Cid], None],
    delete_block: Callable[[Cid], int],
) -> GcReport:
    """The two-phase pass both backends share; they supply mark + delete.

    A block's grace clock starts when a pass first sees it unreferenced,
    not when it was added — a claim superseded after months still gets its
    full grace window. Reachable again means the mark is cleared.
    """
    current = now if now is not None else datetime.now(UTC)
    roots = backend.refs()
    reachable = compute_reachable(list(roots.values()), backend.get, extract_links)
    stored = backend.cids()
    unreferenced = [cid for cid in stored if cid not in reachable]
    unreferenced_set = set(unreferenced)

    for cid in marks:
        if cid not in unreferenced_set:
            clear_mark(cid)

    kept = collected = freed = 0
    for cid in unreferenced:
        since = marks.get(cid)
        if since is None:
            set_mark(cid, current)
            kept += 1
        elif current - since >= grace:
            freed += delete_block(cid)
            clear_mark(cid)
            collected += 1
        else:
            kept += 1

    return GcReport(
        roots=len(roots),
        reachable=len(stored) - len(unreferenced),
        unreferenced=len(unreferenced),
        kept=kept,
        collected=collected,
        freed_bytes=freed,
    )


def compute_reachable(
    roots: list[Cid],
    get: Callable[[Cid], bytes],
    extract_links: ExtractLinks,
) -> set[Cid]:
    """Every CID reachable from the roots via document links."""
    seen: set[Cid] = set()
    stack = list(roots)
    while stack:
        cid = stack.pop()
        if cid in seen:
            continue
        seen.add(cid)
        try:
            data = get(cid)
        except KeyError:
            continue  # a dangling ref roots nothing further
        stack.extend(extract_links(cid, data))
    return seen


class StoreBackend(Protocol):
    def put(self, cid: Cid, data: bytes) -> None:
        """Store a block. Re-putting an existing CID is a no-op."""
        ...

    def get(self, cid: Cid) -> bytes:
        """Return the block's bytes; raise KeyError if absent."""
        ...

    def has(self, cid: Cid) -> bool: ...

    def cids(self) -> list[Cid]: ...

    def set_ref(self, name: str, cid: Cid) -> None: ...

    def get_ref(self, name: str) -> Cid | None: ...

    def refs(self) -> dict[str, Cid]: ...

    def gc(
        self,
        extract_links: ExtractLinks,
        grace: timedelta,
        now: datetime | None = None,
    ) -> GcReport:
        """Collect blocks unreachable from the refs, after grace.

        Two-phase (unreferenced-since): a pass marks unreachable blocks
        with the time it first saw them unreferenced; a later pass collects
        marks older than `grace`. Re-referenced blocks lose their mark.
        `now` exists for tests; None means the current UTC time.
        """
        ...

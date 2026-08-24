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
they never encode, decode, or interpret. `gc` joins the interface with its
milestone (post-skeleton, per The v1 cut).
"""

from __future__ import annotations

from typing import Protocol

from freckles.documents import Cid


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

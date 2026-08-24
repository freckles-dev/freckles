# cid.py
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

"""CIDv1 addressing: sha2-256, dag-cbor (0x71) for documents, raw (0x55) for blobs."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import libipld

DAG_CBOR = 0x71
RAW = 0x55

_SHA2_256 = 0x12


@dataclass(frozen=True, slots=True)
class Cid:
    """A CIDv1, held as its raw binary form (version + codec + multihash)."""

    bytes: bytes

    @classmethod
    def parse(cls, text: str) -> Cid:
        """Parse the base32 string form ("bafy…")."""
        _base, raw = libipld.decode_multibase(text)
        return cls(raw)

    @property
    def codec(self) -> int:
        return self.bytes[1]

    def __str__(self) -> str:
        return libipld.encode_cid(self.bytes)

    def __repr__(self) -> str:
        return f"Cid({str(self)!r})"


def _cid(codec: int, data: bytes) -> Cid:
    digest = hashlib.sha256(data).digest()
    return Cid(bytes([1, codec, _SHA2_256, len(digest)]) + digest)


def cid_for_document(encoded: bytes) -> Cid:
    """The CID of spec-strict DAG-CBOR document bytes."""
    return _cid(DAG_CBOR, encoded)


def cid_for_blob(data: bytes) -> Cid:
    """The CID of a raw blob (design.md §7: capped at 1 MiB)."""
    if len(data) > 1 << 20:
        raise ValueError("blob exceeds 1 MiB; use a list-of-blocks document")
    return _cid(RAW, data)

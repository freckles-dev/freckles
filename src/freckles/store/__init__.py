# __init__.py
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

"""The content-addressed store: immutable CAS plus refs (the design's "in" side).

Backend seam (`put/get/has/cids`, refs, gc) with sqlite and folder adapters;
backends stay codec-ignorant.
"""

from freckles.documents import Cid, cid_for_blob, decode, encode
from freckles.store.base import StoreBackend
from freckles.store.sqlite import SqliteStore

__all__ = [
    "SqliteStore",
    "StoreBackend",
    "get_doc",
    "provenance_for",
    "put_blob",
    "put_doc",
]

_DAG_CBOR = 0x71


def put_doc(backend: StoreBackend, document: dict) -> Cid:
    """Encode a store document and put it; returns its CID."""
    data, cid = encode(document)
    backend.put(cid, data)
    return cid


def get_doc(backend: StoreBackend, cid: Cid) -> dict:
    """Fetch and decode a store document."""
    return decode(backend.get(cid))


def provenance_for(backend: StoreBackend, claim: Cid) -> dict | None:
    """The provenance document naming this claim as its outcome, if stored.

    A linear scan over document CIDs — provenance is a separate
    content-addressed record with no reverse index by design (ADR: the audit
    chain never enters the claim's address), and inspection is rare.
    """
    for cid in backend.cids():
        if cid.codec != _DAG_CBOR:
            continue  # raw blobs are not documents
        document = get_doc(backend, cid)
        if document.get("outcome") == claim and "derivation" in document:
            return document
    return None


def put_blob(backend: StoreBackend, data: bytes) -> Cid:
    """Put raw bytes as a blob; returns its CID."""
    cid = cid_for_blob(data)
    backend.put(cid, data)
    return cid

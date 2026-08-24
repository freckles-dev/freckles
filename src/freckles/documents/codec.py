# codec.py
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

"""Codecs for store documents (DAG-CBOR) and the wire (DAG-JSON).

Nothing outside `freckles.documents` touches DAG-CBOR, CIDs, or libipld.
Store documents use the claim value model (no floats, no raw bytes — bytes
appear only as CID links); the wire is DAG-JSON, lossless against the same
data model (links as {"/": "bafy…"}, bytes as {"/": {"bytes": "<base64>"}}).
"""

from __future__ import annotations

import base64
import json
from typing import Any

import libipld

from freckles.documents.cid import Cid, cid_for_document


def _to_ipld(value: Any) -> Any:
    """Lower the Python value model to what libipld encodes (Cid -> raw bytes)."""
    if isinstance(value, Cid):
        return value.bytes
    if isinstance(value, dict):
        return {k: _to_ipld(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_ipld(v) for v in value]
    if isinstance(value, bool | int | str) or value is None:
        return value
    raise TypeError(f"value outside the claim value model: {type(value).__name__}")


def _from_ipld(value: Any) -> Any:
    """Raise decoded values back into the model (link bytes -> Cid)."""
    if isinstance(value, bytes):
        return Cid(value)
    if isinstance(value, dict):
        return {k: _from_ipld(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_from_ipld(v) for v in value]
    return value


def encode(document: dict[str, Any]) -> tuple[bytes, Cid]:
    """Encode a store document to spec-strict DAG-CBOR bytes plus its CID."""
    data = libipld.encode_dag_cbor(_to_ipld(document))
    return data, cid_for_document(data)


def decode(data: bytes) -> dict[str, Any]:
    """Decode DAG-CBOR document bytes back into the value model."""
    return _from_ipld(libipld.decode_dag_cbor(data))


def _to_wire_value(value: Any) -> Any:
    if isinstance(value, Cid):
        return {"/": str(value)}
    if isinstance(value, bytes):
        return {"/": {"bytes": base64.b64encode(value).decode().rstrip("=")}}
    if isinstance(value, dict):
        return {k: _to_wire_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_wire_value(v) for v in value]
    return value


def _from_wire_value(value: Any) -> Any:
    if isinstance(value, dict):
        if set(value) == {"/"}:
            inner = value["/"]
            if isinstance(inner, str):
                return Cid.parse(inner)
            if isinstance(inner, dict) and set(inner) == {"bytes"}:
                b64 = inner["bytes"]
                return base64.b64decode(b64 + "=" * (-len(b64) % 4))
        return {k: _from_wire_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_from_wire_value(v) for v in value]
    return value


def to_wire(document: dict[str, Any]) -> str:
    """Encode a document into its DAG-JSON wire form."""
    return json.dumps(_to_wire_value(document), sort_keys=True)


def from_wire(text: str | bytes) -> dict[str, Any]:
    """Decode a DAG-JSON wire document back into the value model."""
    return _from_wire_value(json.loads(text))

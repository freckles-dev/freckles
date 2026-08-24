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

"""Value model and codecs: claim, outcome, derivation, provenance, resolution.

Nothing outside this module touches DAG-CBOR, CIDs, or libipld.
"""

from freckles.documents.cid import Cid, cid_for_blob, cid_for_document
from freckles.documents.codec import decode, encode, from_wire, to_wire
from freckles.documents.model import (
    SCHEMA,
    Derivation,
    Outcome,
    Provenance,
    Resolution,
    ResolvedNode,
    tree_doc,
)

__all__ = [
    "SCHEMA",
    "Cid",
    "Derivation",
    "Outcome",
    "Provenance",
    "ResolvedNode",
    "Resolution",
    "cid_for_blob",
    "cid_for_document",
    "decode",
    "encode",
    "from_wire",
    "to_wire",
    "tree_doc",
]

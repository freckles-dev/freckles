# model.py
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

"""Typed store documents (dataclasses + explicit to_doc/from_doc codecs).

Claims are open maps and stay plain dicts; the structured documents around
them get dataclasses. `to_doc` produces exactly the shapes `conformance/`
fixes in store.cddl.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from freckles.documents.cid import Cid

SCHEMA = 1

PluginId = Cid | dict[str, str]  # plugin claim CID, or {"builtin": …, "freckles": …}


@dataclass(frozen=True, slots=True)
class Derivation:
    """The canonical bytes behind the derivation hash (its CID *is* the hash)."""

    plugin: PluginId
    config: dict[str, Any]
    inputs: dict[str, Cid]  # consumed kind -> input claim CID

    def to_doc(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "plugin": self.plugin,
            "config": self.config,
            "inputs": self.inputs,
        }


@dataclass(frozen=True, slots=True)
class Provenance:
    """Pure links: which derivation produced which claim."""

    derivation: Cid
    outcome: Cid

    def to_doc(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "derivation": self.derivation,
            "outcome": self.outcome,
        }


@dataclass(frozen=True, slots=True)
class ResolvedNode:
    plugin: PluginId
    produces: str
    effect: str  # "pure" | "effectful"
    config: dict[str, Any]
    consumes: dict[str, str]  # consumed kind -> provider node name

    def to_doc(self) -> dict[str, Any]:
        return {
            "plugin": self.plugin,
            "produces": self.produces,
            "effect": self.effect,
            "config": self.config,
            "consumes": self.consumes,
        }

    @classmethod
    def from_doc(cls, doc: dict[str, Any]) -> ResolvedNode:
        return cls(
            plugin=doc["plugin"],
            produces=doc["produces"],
            effect=doc["effect"],
            config=doc["config"],
            consumes=doc["consumes"],
        )


@dataclass(frozen=True, slots=True)
class Resolution:
    """Snapshot of one resolved run — the lockfile's successor."""

    config_snapshot: Cid
    nodes: dict[str, ResolvedNode]

    def to_doc(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "config-snapshot": self.config_snapshot,
            "nodes": {name: node.to_doc() for name, node in self.nodes.items()},
        }

    @classmethod
    def from_doc(cls, doc: dict[str, Any]) -> Resolution:
        return cls(
            config_snapshot=doc["config-snapshot"],
            nodes={name: ResolvedNode.from_doc(n) for name, n in doc["nodes"].items()},
        )


@dataclass(frozen=True, slots=True)
class Outcome:
    """What a successful run returns: a claim plus machine-local annotations."""

    claim: dict[str, Any]
    annotations: dict[str, Any] = field(default_factory=dict)


def tree_doc(entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """A tree document: relative path -> {content: <blob CID>, exec?: bool}."""
    return {"schema": SCHEMA, "entries": entries}

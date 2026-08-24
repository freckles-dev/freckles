# resolve.py
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

"""Configuration -> resolution document: loading, edge inference, hard errors.

The configuration is the working copy: `freckles.yaml` (the named-node DAG)
plus the files beside it. Nodes bind an `op`, node config, an optional
node-supplied `consumes` list (the adapter selector mechanism, design.md §6),
and optional `use:` tie-breakers. Inference wires unambiguous consumed kinds;
ambiguity is a hard error resolved by `use:`; explicit edges always win.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from freckles.builtins import BUILTINS
from freckles.documents import Cid, Resolution, ResolvedNode, tree_doc
from freckles.store import get_doc, put_blob, put_doc
from freckles.store.base import StoreBackend


class ResolutionError(Exception):
    """The configuration cannot resolve: unknown op, ambiguity, missing provider, cycle."""


def resolve(
    config_dir: str | Path,
    store: StoreBackend,
    freckles_version: str,
    config_name: str | None = None,
) -> tuple[Resolution, Cid]:
    """Resolve the configuration; snapshot, document, and ref land in the store."""
    config_dir = Path(config_dir)
    name = config_name or config_dir.name
    raw = yaml.safe_load((config_dir / "freckles.yaml").read_text())

    declared: dict[str, dict[str, Any]] = raw["nodes"]
    facts = {
        node_name: _node_facts(node_name, node, store, freckles_version)
        for node_name, node in declared.items()
    }

    nodes: dict[str, ResolvedNode] = {}
    for node_name, (plugin, produces, effect, consumed_kinds) in facts.items():
        use: dict[str, str] = declared[node_name].get("use", {})
        consumes: dict[str, str] = {}
        for kind in consumed_kinds:
            consumes[kind] = _wire_edge(node_name, kind, use, facts)
        nodes[node_name] = ResolvedNode(
            plugin=plugin,
            produces=produces,
            effect=effect,
            config=declared[node_name].get("config", {}),
            consumes=consumes,
        )

    _check_acyclic(nodes)

    snapshot_cid = _snapshot(config_dir, store)
    resolution = Resolution(config_snapshot=snapshot_cid, nodes=nodes)
    resolution_cid = put_doc(store, resolution.to_doc())
    store.set_ref(f"cfg/{name}/current", resolution_cid)
    return resolution, resolution_cid


def _node_facts(
    node_name: str, node: dict[str, Any], store: StoreBackend, freckles_version: str
) -> tuple[Any, str, str, list[str]]:
    """(plugin id, produced kind, effect, consumed kinds) for one declared node."""
    op = node["op"]
    config = node.get("config", {})
    consumed: list[str] = node.get("consumes", [])

    if op in BUILTINS:
        builtin = BUILTINS[op]
        produces = builtin.produces or config.get("kind")
        effect = builtin.effect or config.get("effect")
        if produces is None or effect is None:
            raise ResolutionError(
                f"{node_name}: op {op!r} needs node-supplied kind/effect in config"
            )
        return (
            {"builtin": op, "freckles": freckles_version},
            produces,
            effect,
            consumed or list(builtin.consumes),
        )

    if plugin_ref := node.get("plugin"):
        plugin_cid = Cid.parse(plugin_ref)
        manifest = get_doc(store, plugin_cid)
        return (
            plugin_cid,
            manifest["produces"],
            manifest["effect"],
            consumed or sorted(manifest.get("consumes", {})),
        )

    raise ResolutionError(f"{node_name}: unknown op {op!r} and no plugin pinned")


def _wire_edge(
    node_name: str,
    kind: str,
    use: dict[str, str],
    facts: dict[str, tuple[Any, str, str, list[str]]],
) -> str:
    if kind in use:
        provider = use[kind]
        if provider not in facts:
            raise ResolutionError(f"{node_name}: use names unknown node {provider!r}")
        if facts[provider][1] != kind:
            raise ResolutionError(
                f"{node_name}: use.{kind} -> {provider!r}, which produces "
                f"{facts[provider][1]!r}"
            )
        return provider

    candidates = [
        other
        for other, (_, produces, _, _) in facts.items()
        if produces == kind and other != node_name
    ]
    if not candidates:
        raise ResolutionError(f"{node_name}: no provider for consumed kind {kind!r}")
    if len(candidates) > 1:
        raise ResolutionError(
            f"{node_name}: consumed kind {kind!r} is ambiguous "
            f"({', '.join(sorted(candidates))}) — break the tie with "
            f"use: {{{kind}: <node>}}"
        )
    return candidates[0]


def _check_acyclic(nodes: dict[str, ResolvedNode]) -> None:
    state: dict[str, int] = {}  # 0 visiting, 1 done

    def visit(name: str, trail: list[str]) -> None:
        if state.get(name) == 1:
            return
        if state.get(name) == 0:
            cycle = " -> ".join([*trail, name])
            raise ResolutionError(f"configuration has a cycle: {cycle}")
        state[name] = 0
        for provider in nodes[name].consumes.values():
            visit(provider, [*trail, name])
        state[name] = 1

    for name in nodes:
        visit(name, [])


def _snapshot(config_dir: Path, store: StoreBackend) -> Cid:
    """The configuration working copy as a tree document (content, never git state)."""
    entries: dict[str, Any] = {}
    for file in sorted(p for p in config_dir.rglob("*") if p.is_file()):
        # Tree keys are identity: always /-separated, on every platform.
        relative = file.relative_to(config_dir).as_posix()
        if relative.startswith(".git/"):
            continue
        entries[relative] = {"content": put_blob(store, file.read_bytes())}
    return put_doc(store, tree_doc(entries))

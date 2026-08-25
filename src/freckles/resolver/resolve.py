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


class UnknownOp(ResolutionError):
    """An op that is neither a built-in nor a store plugin claim."""

    def __init__(self, node_name: str, op: str, message: str) -> None:
        super().__init__(message)
        self.node_name = node_name
        self.op = op


def resolve(
    config_dir: str | Path,
    store: StoreBackend,
    freckles_version: str,
    config_name: str | None = None,
) -> tuple[Resolution, Cid]:
    """Resolve fully — every op bound; an unacquired plugin is an error here.

    The acquisition-aware entry is `resolve_round` (M5): heal drives rounds
    until nothing stays deferred, and this strict form serves every verb
    that must not run anything.
    """
    resolution, cid, deferred = resolve_round(
        config_dir, store, freckles_version, config_name
    )
    if deferred:
        names = ", ".join(sorted(deferred))
        raise ResolutionError(
            f"unbound ops remain (plugins not yet acquired): {names} — "
            "run: freckles heal"
        )
    return resolution, cid


def resolve_round(
    config_dir: str | Path,
    store: StoreBackend,
    freckles_version: str,
    config_name: str | None = None,
) -> tuple[Resolution, Cid, dict[str, str]]:
    """One resolution round (M5): snapshot, document, and ref land in the store.

    A node whose op names a plugin no store claim provides is DEFERRED —
    not an error — when a declared node produces `kind: plugin` with that
    manifest name; its consumers defer transitively. The returned mapping
    is deferred node -> why; a complete round returns it empty.
    """
    config_dir = Path(config_dir)
    name = config_name or config_dir.name
    raw = yaml.safe_load((config_dir / "freckles.yaml").read_text())

    declared: dict[str, dict[str, Any]] = raw["nodes"]

    # op name -> the produced kind its plugin will produce, per the
    # provider's declared manifest (the fetch-verify pattern).
    provided_ops = {
        manifest["name"]: manifest.get("produces")
        for node in declared.values()
        if (config := node.get("config", {})).get("kind") == "plugin"
        and (manifest := config.get("manifest"))
    }

    deferred: dict[str, str] = {}
    facts = {}
    for node_name, node in declared.items():
        try:
            facts[node_name] = _node_facts(node_name, node, store, freckles_version)
        except UnknownOp as unknown:
            if unknown.op in provided_ops:
                deferred[node_name] = f"op {unknown.op!r} not yet acquired"
            else:
                raise

    # Transitive deferral: a consumer whose kind only a deferred node's
    # plugin would produce waits for the same acquisition.
    pending_kinds = {provided_ops[op] for op in provided_ops} - {None}
    changed = True
    while changed:
        changed = False
        for node_name in list(facts):
            _, _, _, consumed_kinds = facts[node_name]
            use: dict[str, str] = declared[node_name].get("use", {})
            for kind in consumed_kinds:
                try:
                    _wire_edge(node_name, kind, use, facts)
                except ResolutionError:
                    if kind in pending_kinds and deferred:
                        deferred[node_name] = f"consumes deferred kind {kind!r}"
                        del facts[node_name]
                        changed = True
                        break
                    raise

    nodes: dict[str, ResolvedNode] = {}
    for node_name, (plugin, produces, effect, consumed_kinds) in facts.items():
        node_config = declared[node_name].get("config", {})
        if effect == "pure" and "secret-env" in node_config:
            raise ResolutionError(
                f"{node_name}: purity gate — secret-env wires plaintext into a "
                "pure node; plaintext reaches effectful operations only (ADR 0005)"
            )
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
    return resolution, resolution_cid, deferred


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

    found = _find_plugin(store, node_name, op, node.get("version"))
    if found is not None:
        plugin_cid, manifest = found
        return (
            plugin_cid,
            manifest["produces"],
            manifest["effect"],
            consumed or sorted(manifest.get("consumes", {})),
        )

    raise UnknownOp(
        node_name,
        op,
        f"{node_name}: unknown op {op!r} — not a built-in, and no plugin "
        f"claim named {op!r} in the store",
    )


_DAG_CBOR = 0x71


def _find_plugin(
    store: StoreBackend, node_name: str, name: str, version: str | None
) -> tuple[Cid, dict[str, Any]] | None:
    """The op -> plugin binding (M5), matched by manifest name.

    The match is pinned into the resolution by CID. Multiple acquired
    versions without a node `version:` pin are a hard error — resolution
    never guesses an ordering.
    """
    matches = [
        (cid, doc)
        for cid in store.cids()
        if cid.codec == _DAG_CBOR
        and (doc := get_doc(store, cid)).get("kind") == "plugin"
        and doc.get("name") == name
        and (version is None or doc.get("version") == version)
    ]
    if not matches:
        return None
    if len(matches) > 1:
        versions = ", ".join(sorted(str(doc.get("version")) for _, doc in matches))
        raise ResolutionError(
            f"{node_name}: multiple plugin claims named {name!r} "
            f"(versions {versions}) — pin one with: version: <version>"
        )
    return matches[0]


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
        providers = sorted(candidates)
        raise ResolutionError(
            f"ambiguous edge: {node_name} consumes kind {kind!r}, "
            f"{len(providers)} providers: {', '.join(providers)}\n"
            f"fix: select one explicitly in {node_name}:\n"
            f"    use: {{{kind}: {providers[0]}}}"
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

# walk.py
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

"""The heal walk (design.md §8): one loop for day-1 and day-2.

Topological order; each node's derivation is computed from its current input
claims and looked up in the derivation index. A hit means current. A miss on
a pure node re-derives on the spot — often re-minting the same claim, which
stops the ripple (extensional addressing, ADR 0001). A miss on an effectful
node joins the checkpoint set; unconfirmed, it hides its downstream until its
checkpoint runs. `confirm` is injected: the CLI passes the prompt, `--yes`
passes const-true, tests pass scripted answers.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from graphlib import TopologicalSorter
from typing import Any

from freckles.builtins import BUILTINS
from freckles.documents import (
    Cid,
    Derivation,
    Provenance,
    Resolution,
    ResolvedNode,
    encode,
)
from freckles.runner import RunContext, run_node
from freckles.state import DerivationIndex
from freckles.store import get_doc, put_doc


def _is_source(node: ResolvedNode) -> bool:
    if isinstance(node.plugin, dict) and (
        builtin := BUILTINS.get(node.plugin["builtin"])
    ):
        return builtin.source
    return False


def _op_label(node: ResolvedNode) -> str:
    if isinstance(node.plugin, dict) and "builtin" in node.plugin:
        return node.plugin["builtin"]
    return str(node.plugin)


@dataclass(slots=True)
class Checkpoint:
    """The facts a human needs to confirm one effectful run (prompt R3)."""

    name: str
    op: str
    effect: str
    produces: str
    supersedes: Cid | None  # the claim this run would replace, if any
    prior_available: bool  # a prior claim (+ its annotations) can be passed


@dataclass(slots=True)
class HealReport:
    current: list[str] = field(default_factory=list)  # derivation hit, untouched
    healed: list[str] = field(default_factory=list)  # pure, re-derived now
    confirmed: list[str] = field(default_factory=list)  # checkpoints run
    checkpoint_set: list[str] = field(default_factory=list)  # stale effectful found
    hidden: list[str] = field(default_factory=list)  # downstream of unconfirmed

    @property
    def deployment_current(self) -> bool:
        """design.md §8: "is the checkpoint set empty?"."""
        return not self.checkpoint_set or set(self.checkpoint_set) <= set(
            self.confirmed
        )


def heal(
    resolution: Resolution,
    config_name: str,
    ctx: RunContext,
    index: DerivationIndex,
    confirm: Callable[[Checkpoint], bool],
) -> HealReport:
    report = HealReport()
    claims: dict[str, Cid] = {}  # node -> current claim CID, advancing as we walk
    hidden: set[str] = set()

    order = TopologicalSorter(
        {name: set(node.consumes.values()) for name, node in resolution.nodes.items()}
    )
    for name in order.static_order():
        node = resolution.nodes[name]

        if hidden & set(node.consumes.values()):
            hidden.add(name)
            report.hidden.append(name)
            continue

        inputs = {kind: claims[provider] for kind, provider in node.consumes.items()}
        derivation = Derivation(plugin=node.plugin, config=node.config, inputs=inputs)
        derivation_cid = put_doc(ctx.store, derivation.to_doc())

        if _is_source(node):
            # A source's derivation is content-free: the world it imports can
            # change under an unchanged derivation, so the index cannot answer
            # for it. Re-import every walk; an unchanged import re-mints the
            # same claim and the extensional ripple stops immediately.
            previous = ctx.store.get_ref(f"cfg/{config_name}/nodes/{name}")
            claims[name] = _run(
                name, node, {}, derivation_cid, ctx, index, config_name, prior=False
            )
            if claims[name] == previous:
                report.current.append(name)
            else:
                report.healed.append(name)
            continue

        cached = index.lookup(derivation_cid)
        if cached is not None:
            claims[name] = cached
            report.current.append(name)
            continue

        if node.effect == "effectful":
            report.checkpoint_set.append(name)
            previous = ctx.store.get_ref(f"cfg/{config_name}/nodes/{name}")
            checkpoint = Checkpoint(
                name=name,
                op=_op_label(node),
                effect=node.effect,
                produces=node.produces,
                supersedes=previous,
                prior_available=previous is not None,
            )
            if not confirm(checkpoint):
                hidden.add(name)
                continue
            claims[name] = _run(
                name, node, inputs, derivation_cid, ctx, index, config_name, prior=True
            )
            report.confirmed.append(name)
        else:
            claims[name] = _run(
                name, node, inputs, derivation_cid, ctx, index, config_name, prior=False
            )
            report.healed.append(name)

    # Sources imported from exactly this config snapshot — the frozen walk's
    # licence to trust their refs until the working copy changes again.
    ctx.store.set_ref(
        f"cfg/{config_name}/last-walk-snapshot", resolution.config_snapshot
    )
    return report


@dataclass(slots=True)
class FrozenReport:
    """A look-don't-touch staleness answer (status --frozen).

    Exact where the derivation index can speak, honest ("undetermined")
    where only a run could tell.
    """

    current: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)  # the stale frontier
    undetermined: list[str] = field(default_factory=list)  # downstream of it

    @property
    def all_current(self) -> bool:
        return not self.stale and not self.undetermined


def frozen(
    resolution: Resolution,
    config_name: str,
    ctx: RunContext,
    index: DerivationIndex,
) -> FrozenReport:
    """Report staleness without running anything (status --frozen).

    Sources are only knowable indirectly: their refs are trusted iff the
    config snapshot is unchanged since the last walk that ran them. Beyond
    the sources, derivations are pure knowledge — the index answers exactly;
    consumers of anything stale or unknown stay undetermined.
    """
    report = FrozenReport()
    claims: dict[str, Cid] = {}
    unknown: set[str] = set()

    sources_fresh = (
        ctx.store.get_ref(f"cfg/{config_name}/last-walk-snapshot")
        == resolution.config_snapshot
    )

    order = TopologicalSorter(
        {name: set(node.consumes.values()) for name, node in resolution.nodes.items()}
    )
    for name in order.static_order():
        node = resolution.nodes[name]

        if unknown & set(node.consumes.values()):
            unknown.add(name)
            report.undetermined.append(name)
            continue

        if _is_source(node):
            previous = ctx.store.get_ref(f"cfg/{config_name}/nodes/{name}")
            if sources_fresh and previous is not None:
                claims[name] = previous
                report.current.append(name)
            else:
                unknown.add(name)
                report.stale.append(name)
            continue

        inputs = {kind: claims[provider] for kind, provider in node.consumes.items()}
        derivation = Derivation(plugin=node.plugin, config=node.config, inputs=inputs)
        _, derivation_cid = encode(derivation.to_doc())  # computed, never stored

        cached = index.lookup(derivation_cid)
        if cached is not None:
            claims[name] = cached
            report.current.append(name)
        else:
            unknown.add(name)
            report.stale.append(name)

    return report


def _run(
    name: str,
    node: ResolvedNode,
    inputs: dict[str, Cid],
    derivation_cid: Cid,
    ctx: RunContext,
    index: DerivationIndex,
    config_name: str,
    prior: bool,
) -> Cid:
    request_inputs: dict[str, dict[str, Any]] = {}
    for kind, claim_cid in inputs.items():
        entry: dict[str, Any] = {
            "cid": claim_cid,
            "claim": get_doc(ctx.store, claim_cid),
        }
        annotations = ctx.annotations.get(claim_cid)
        if annotations:
            entry["annotations"] = annotations
        request_inputs[kind] = entry

    prior_ref: dict[str, Any] | None = None
    node_ref = f"cfg/{config_name}/nodes/{name}"
    if prior and (previous := ctx.store.get_ref(node_ref)) is not None:
        prior_ref = {"cid": previous, "claim": get_doc(ctx.store, previous)}
        if previous_annotations := ctx.annotations.get(previous):
            prior_ref["annotations"] = previous_annotations

    outcome = run_node(name, node, request_inputs, ctx, prior=prior_ref)

    claim_cid = put_doc(ctx.store, outcome.claim)
    put_doc(
        ctx.store, Provenance(derivation=derivation_cid, outcome=claim_cid).to_doc()
    )
    index.record(derivation_cid, claim_cid)
    ctx.store.set_ref(node_ref, claim_cid)
    if outcome.annotations:
        ctx.annotations.set(claim_cid, outcome.annotations)
    return claim_cid

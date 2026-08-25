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

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from graphlib import TopologicalSorter
from pathlib import Path
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
from freckles.runner import RunContext, RunError, run_node
from freckles.state import AuditRecord, DerivationIndex
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
    secrets: list[str] = field(default_factory=list)  # plaintext names (R3/M2)


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
        if cached is not None and ctx.annotations.distrusted(cached) is None:
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
                secrets=[
                    claim["name"]
                    for cid in inputs.values()
                    if (claim := get_doc(ctx.store, cid)).get("kind") == "secret"
                ],
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
        if cached is not None and ctx.annotations.distrusted(cached) is None:
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

    # Resolved secret names for the audit record: plaintext reaches effectful
    # requests only (§9 flow B), so pure runs resolve nothing.
    secrets = (
        [
            entry["claim"]["name"]
            for entry in request_inputs.values()
            if entry["claim"].get("kind") == "secret"
        ]
        if node.effect == "effectful"
        else []
    )

    started = time.monotonic()
    try:
        outcome = run_node(name, node, request_inputs, ctx, prior=prior_ref)
    except RunError as error:
        _record_run(
            ctx, config_name, name, node, derivation_cid, None, secrets, started, error
        )
        raise

    claim_cid = put_doc(ctx.store, outcome.claim)
    _record_run(
        ctx, config_name, name, node, derivation_cid, claim_cid, secrets, started, None
    )
    provenance_cid = put_doc(
        ctx.store, Provenance(derivation=derivation_cid, outcome=claim_cid).to_doc()
    )
    index.record(derivation_cid, claim_cid)
    # Re-running heals distrust (design.md §8) — often by re-minting the
    # byte-identical claim, so the mark on that CID must go now.
    ctx.annotations.clear_distrust(claim_cid)
    ctx.store.set_ref(node_ref, claim_cid)
    # The prov ref keeps a current claim's provenance (and, through it, the
    # derivation document) out of gc's reach; superseded provenance ages out
    # through grace exactly like superseded claims (design.md §7, M3 note).
    ctx.store.set_ref(f"cfg/{config_name}/prov/{name}", provenance_cid)
    if outcome.annotations:
        ctx.annotations.set(claim_cid, outcome.annotations)
    return claim_cid


def heal_rounds(
    config_dir: Path,
    config_name: str,
    ctx: RunContext,
    index: DerivationIndex,
    confirm: Callable[[Checkpoint], bool],
) -> tuple[Resolution, HealReport]:
    """Resolve-heal rounds until every op is bound (M5, design.md §6).

    A round that leaves ops deferred must have acquired at least one plugin
    for the next round to bind — no shrink means no progress, and that is a
    resolution error, never a spin.
    """
    from freckles.resolver import ResolutionError, resolve_round

    total = HealReport()
    previous: set[str] | None = None
    while True:
        resolution, _, deferred = resolve_round(
            config_dir, ctx.store, ctx.freckles_version, config_name
        )
        report = heal(resolution, config_name, ctx, index, confirm)
        _merge_report(total, report)
        if not deferred:
            _settle_report(total)
            return resolution, total
        if previous is not None and set(deferred) >= previous:
            names = ", ".join(sorted(deferred))
            raise ResolutionError(
                f"acquisition made no progress — still unbound: {names}"
            )
        previous = set(deferred)


def _merge_report(total: HealReport, round_report: HealReport) -> None:
    for field_name in ("current", "healed", "confirmed", "checkpoint_set", "hidden"):
        seen = set(getattr(total, field_name))
        getattr(total, field_name).extend(
            name for name in getattr(round_report, field_name) if name not in seen
        )


def _settle_report(total: HealReport) -> None:
    """Later rounds re-see earlier work: ran beats current, ran beats hidden."""
    ran = set(total.healed) | set(total.confirmed)
    total.current = [name for name in total.current if name not in ran]
    total.hidden = [name for name in total.hidden if name not in ran]


def _record_run(
    ctx: RunContext,
    config_name: str,
    name: str,
    node: ResolvedNode,
    derivation_cid: Cid,
    claim_cid: Cid | None,
    secrets: list[str],
    started: float,
    error: RunError | None,
) -> None:
    if ctx.audit is None:
        return
    ctx.audit.append(
        AuditRecord(
            config=config_name,
            node=name,
            op=f"{_op_label(node)} @ freckles {ctx.freckles_version}",
            derivation=str(derivation_cid),
            claim=str(claim_cid) if claim_cid is not None else None,
            ok=error is None,
            exit_code=0 if error is None else error.exit_code,
            duration_ms=int((time.monotonic() - started) * 1000),
            secrets=secrets,
            error=str(error) if error is not None else None,
        )
    )

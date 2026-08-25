# run.py
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

"""One node run, end to end: request document in, outcome document out.

Two adapters behind one document seam (the layout doc): in-process for
built-ins (trusted core), process for plugins — spawned, DAG-JSON on stdio,
scrubbed environment. `command`'s wrapped invocation is a real subprocess
with the same enforcement either way.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from freckles.documents import SCHEMA, Cid, Outcome, ResolvedNode, from_wire, to_wire
from freckles.runner.context import RunContext
from freckles.runner.workspace import (
    BASELINE_PATH,
    materialize_workspace,
    scrubbed_env,
)
from freckles.store import get_doc


class RunError(Exception):
    """A run failed: non-zero exit, malformed output, or a broken contract."""

    def __init__(self, message: str, detail: str = "", exit_code: int = 1) -> None:
        super().__init__(message)
        self.detail = detail
        self.exit_code = exit_code  # the wrapped process's real code when known


def build_request(
    name: str,
    node: ResolvedNode,
    inputs: dict[str, dict[str, Any]],
    workspace_dir: str,
    path: list[str],
    prior: dict[str, Any] | None,
) -> dict[str, Any]:
    """The wire request document (wire.cddl).

    The purity split is enforced here: pure runs see claims only — no
    annotations, no prior, and never plaintext (ADR 0005). Secret claims
    consumed by an effectful node arrive with `resolved:` injected — the
    plaintext exists only in this in-memory document.
    """
    request_inputs: dict[str, Any] = {}
    for kind, entry in inputs.items():
        request_entry = {"cid": entry["cid"], "claim": entry["claim"]}
        if node.effect == "effectful" and entry.get("annotations"):
            request_entry["annotations"] = entry["annotations"]
        if node.effect == "effectful" and entry["claim"].get("kind") == "secret":
            request_entry["resolved"] = {
                "value": _resolve_secret(entry["claim"], entry.get("annotations"))
            }
        request_inputs[kind] = request_entry

    request: dict[str, Any] = {
        "schema": SCHEMA,
        "node": {"name": name, "config": node.config},
        "inputs": request_inputs,
        "workspace": {"dir": workspace_dir, "path": path},
    }
    if node.effect == "effectful" and prior is not None:
        request["prior"] = prior
    return request


def _resolve_secret(claim: dict[str, Any], annotations: dict[str, Any] | None) -> str:
    """In-memory plaintext for one consumed secret claim (design.md §9)."""
    from freckles.runner import sops

    name = claim.get("name", "?")
    if claim.get("shape") != "value":
        raise RunError(
            f"no resolver for {claim.get('shape')!r}-bearing secrets (v1 resolves "
            f"shape 'value' only) — secret {name!r}"
        )
    imported_from = (annotations or {}).get("imported_from")
    if not imported_from:
        raise RunError(
            f"secret {name!r} has no local materialization "
            "(no imported_from annotation on this machine)"
        )
    try:
        return sops.resolve_value(imported_from)
    except sops.SopsError as error:
        raise RunError(f"cannot resolve secret {name!r}: {error}") from error


def run_node(
    name: str,
    node: ResolvedNode,
    inputs: dict[str, dict[str, Any]],
    ctx: RunContext,
    prior: dict[str, Any] | None = None,
) -> Outcome:
    """Run one resolved node through the adapter its plugin id selects."""
    workspace = materialize_workspace(ctx.workspace_root, name, inputs, ctx.store)
    path = list(BASELINE_PATH)
    request = build_request(name, node, inputs, str(workspace), path, prior)

    if isinstance(node.plugin, Cid):
        outcome_doc = _process_adapter(node.plugin, request, ctx)
    else:
        outcome_doc = _in_process_adapter(node.plugin["builtin"], request, ctx)

    if "error" in outcome_doc:
        error = outcome_doc["error"]
        raise RunError(
            error.get("message", "run failed"),
            error.get("detail", ""),
            error.get("exit_code", 1),
        )

    claim = outcome_doc.get("claim")
    if not isinstance(claim, dict) or claim.get("kind") != node.produces:
        raise RunError(
            f"{name}: outcome claim kind {claim.get('kind') if isinstance(claim, dict) else None!r}"
            f" does not match resolved produced kind {node.produces!r}"
        )
    return Outcome(claim=claim, annotations=outcome_doc.get("annotations", {}))


def _in_process_adapter(
    builtin: str, request: dict[str, Any], ctx: RunContext
) -> dict[str, Any]:
    """Built-ins: in-process, but behind the same request/outcome documents."""
    from freckles.builtins import BUILTINS

    implementation = BUILTINS[builtin].run
    return implementation(request, ctx)


def _process_adapter(
    plugin_cid: Cid, request: dict[str, Any], ctx: RunContext
) -> dict[str, Any]:
    """Plugins: materialize the payload, spawn it, speak DAG-JSON on stdio."""
    plugin_claim = get_doc(ctx.store, plugin_cid)
    workspace = request["workspace"]["dir"]
    entrypoint = Path(workspace) / f"plugin-{plugin_claim['name']}"
    payload = ctx.store.get(plugin_claim["payload"])
    entrypoint.write_bytes(payload)
    os.chmod(entrypoint, 0o755)

    argv = [str(entrypoint)]
    if os.name == "nt":
        # Windows cannot exec shebang scripts. Until the manifest's
        # `platforms` field gates acquisition (post-skeleton), run
        # python-shebang payloads through the current interpreter.
        first_line = payload.split(b"\n", 1)[0]
        if first_line.startswith(b"#!") and b"python" in first_line:
            argv = [sys.executable, str(entrypoint)]

    env = scrubbed_env(request["workspace"]["path"], workspace=Path(workspace))
    try:
        completed = subprocess.run(
            argv,
            input=to_wire(request).encode(),
            capture_output=True,
            cwd=workspace,
            env=env,
        )
    except OSError as exc:
        raise RunError(
            f"plugin {plugin_claim['name']!r} is not executable on this platform",
            str(exc),
        ) from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode(errors="replace")
        try:
            error = from_wire(completed.stdout)["error"]
            raise RunError(
                error.get("message", "plugin failed"),
                detail,
                error.get("exit_code", completed.returncode),
            )
        except (ValueError, KeyError, TypeError):
            raise RunError(
                f"plugin exited {completed.returncode} without a structured error",
                detail,
                completed.returncode,
            ) from None
    try:
        outcome = from_wire(completed.stdout)
    except ValueError as exc:
        raise RunError("plugin wrote malformed output", str(exc)) from exc
    if not isinstance(outcome, dict) or "claim" not in outcome:
        raise RunError("plugin output is not an outcome document")
    return outcome

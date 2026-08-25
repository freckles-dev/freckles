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
    UnrealizedClaim,
    constructed_path,
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
    envs: str,
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
        "workspace": {"dir": workspace_dir, "path": path, "envs": envs},
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
    ctx.envs_root.mkdir(parents=True, exist_ok=True)
    try:
        path = constructed_path(name, inputs)
    except UnrealizedClaim as exc:
        raise RunError(str(exc)) from exc
    request = build_request(
        name, node, inputs, str(workspace), path, prior, str(ctx.envs_root)
    )

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

    if "ingest" in outcome_doc:
        _ingest(outcome_doc, workspace, ctx)

    claim = outcome_doc.get("claim")
    if not isinstance(claim, dict) or claim.get("kind") != node.produces:
        raise RunError(
            f"{name}: outcome claim kind {claim.get('kind') if isinstance(claim, dict) else None!r}"
            f" does not match resolved produced kind {node.produces!r}"
        )
    return Outcome(claim=claim, annotations=outcome_doc.get("annotations", {}))


def run_verify(
    name: str,
    node: ResolvedNode,
    claim_cid: Cid,
    claim: dict[str, Any],
    annotations: dict[str, Any],
    ctx: RunContext,
) -> str | None:
    """Run the node's verify entrypoint against its current outcome (design.md §8).

    None means CONFIRMED; a string is the CONTRADICTED message. RunError is
    reserved for what keeps verification from happening at all — no verify
    entrypoint, an unresolvable node.
    """
    if isinstance(node.plugin, Cid):
        if not get_doc(ctx.store, node.plugin).get("verify"):
            raise RunError(f"{name}: no verify entrypoint")
    elif "verify" not in node.config:
        raise RunError(f"{name}: no verify entrypoint")

    workspace = materialize_workspace(ctx.workspace_root, name, {}, ctx.store)
    ctx.envs_root.mkdir(parents=True, exist_ok=True)
    request = build_request(
        name, node, {}, str(workspace), list(BASELINE_PATH), None, str(ctx.envs_root)
    )
    verify_ref: dict[str, Any] = {"cid": claim_cid, "claim": claim}
    if annotations:
        verify_ref["annotations"] = annotations
    request["verify"] = verify_ref

    if isinstance(node.plugin, Cid):
        return _process_verify(node.plugin, request, ctx)
    outcome_doc = _in_process_adapter(node.plugin["builtin"], request, ctx)
    if "error" in outcome_doc:
        return outcome_doc["error"].get("message", "contradicted")
    return None


def _ingest(outcome_doc: dict[str, Any], workspace: Path, ctx: RunContext) -> None:
    """Ingestion (design.md §6, M5): the declared dir becomes claim.content.

    The runner is the trusted core here — plugins never touch CIDs or the
    store. The command operation's out/ convention, generalized.
    """
    from freckles.documents import tree_doc
    from freckles.store import put_blob, put_doc

    claim = outcome_doc.get("claim")
    if isinstance(claim, dict) and "content" in claim:
        raise RunError("outcome declares ingest but the claim already carries content")
    declared = outcome_doc["ingest"]
    target = (workspace / declared).resolve()
    if not target.is_relative_to(workspace.resolve()):
        raise RunError(f"ingest dir {declared!r} escapes the workspace")
    if not target.is_dir():
        raise RunError(f"ingest dir {declared!r} does not exist in the workspace")

    entries: dict[str, Any] = {}
    for file in sorted(p for p in target.rglob("*") if p.is_file()):
        # Tree keys are identity: always /-separated (same tree, same CID,
        # every platform).
        entries[file.relative_to(target).as_posix()] = {
            "content": put_blob(ctx.store, file.read_bytes())
        }
    if isinstance(claim, dict):
        claim["content"] = put_doc(ctx.store, tree_doc(entries))


def _in_process_adapter(
    builtin: str, request: dict[str, Any], ctx: RunContext
) -> dict[str, Any]:
    """Built-ins: in-process, but behind the same request/outcome documents."""
    from freckles.builtins import BUILTINS

    implementation = BUILTINS[builtin].run
    return implementation(request, ctx)


def _spawn_plugin(
    plugin_cid: Cid, request: dict[str, Any], ctx: RunContext
) -> subprocess.CompletedProcess:
    """Materialize the payload and run it over the request document."""
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
        return subprocess.run(
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


def _process_verify(
    plugin_cid: Cid, request: dict[str, Any], ctx: RunContext
) -> str | None:
    """The verify protocol over a spawned plugin: the exit code is the verdict.

    Exit 0 is CONFIRMED — stdout may stay silent. Nonzero is CONTRADICTED,
    with the message from a structured error document or the stderr tail.
    """
    completed = _spawn_plugin(plugin_cid, request, ctx)
    if completed.returncode == 0:
        return None
    stderr = completed.stderr.decode(errors="replace").strip()
    try:
        error = from_wire(completed.stdout)["error"]
        return error.get("message") or stderr or "contradicted"
    except (ValueError, KeyError, TypeError):
        return stderr or f"verify exited {completed.returncode}"


def _process_adapter(
    plugin_cid: Cid, request: dict[str, Any], ctx: RunContext
) -> dict[str, Any]:
    """Plugins: materialize the payload, spawn it, speak DAG-JSON on stdio."""
    completed = _spawn_plugin(plugin_cid, request, ctx)
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

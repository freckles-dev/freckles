# registry.py
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

"""The built-in registry: manifests + in-process implementations.

Built-ins are trusted core: they run in-process behind the same
request/outcome document interface as spawned plugins, and — unlike
plugins — may touch the store (source imports and output ingestion need
it). Shipped so far: `import-values`, `command` (skeleton), `import-sops`
(milestone 2); the remaining three built-ins land with their milestones.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from freckles.documents import SCHEMA, cid_for_blob, to_wire, tree_doc
from freckles.runner.context import RunContext
from freckles.runner.workspace import scrubbed_env
from freckles.store import put_blob, put_doc


@dataclass(frozen=True, slots=True)
class Builtin:
    """A built-in's manifest facts plus its in-process implementation.

    `produces`/`effect` of None mean node-supplied (the adapter rule,
    design.md §6): the node config must state them.
    """

    name: str
    produces: str | None
    effect: str | None
    consumes: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Source nodes import external content, so their derivations are
    # content-free — the heal walk must re-run them every time and let
    # extensional addressing stop the ripple when the import is unchanged.
    # (Skeleton finding, 2026-08-24: design.md §8 implies but never states
    # this rule; flagged for a design-side amendment.)
    source: bool = False
    run: Callable[[dict[str, Any], RunContext], dict[str, Any]] = None  # type: ignore[assignment]


def _import_values(request: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
    """Source node: import one key's values from a working-copy YAML file.

    Granularity principle: one independent-change unit per node — the claim
    holds the selected key's subtree, not the whole file.
    """
    config = request["node"]["config"]
    source = ctx.config_dir / config["file"]
    document = yaml.safe_load(source.read_text())
    content = yaml.safe_dump(document[config["key"]], sort_keys=True).encode()
    cid = put_blob(ctx.store, content)
    return {
        "schema": SCHEMA,
        "claim": {
            "schema": SCHEMA,
            "kind": "values",
            "key": config["key"],
            "content": cid,
        },
    }


def _import_sops(request: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
    """Source node: one key's sops ciphertext becomes a secret-value claim.

    Identity is the ciphertext (design.md §9): the claim references exactly
    this key's ENC bytes, so rotating a sibling key in the same file never
    ripples here. No decryption happens at import — that is the runner
    boundary's business (ADR 0005).
    """
    from datetime import UTC, datetime

    config = request["node"]["config"]
    source = ctx.config_dir / config["file"]
    key = config["key"]
    document = yaml.safe_load(source.read_text())
    value = document[key]
    ciphertext = (
        value.encode()
        if isinstance(value, str)
        else yaml.safe_dump(value, sort_keys=True).encode()
    )
    if config.get("store", True):
        cid = put_blob(ctx.store, ciphertext)
    else:
        # The detached variant: same hash, same claim, same ripple — the
        # bytes stay in the working copy (runner materializes from there).
        cid = cid_for_blob(ciphertext)
    return {
        "schema": SCHEMA,
        "claim": {
            "schema": SCHEMA,
            "kind": "secret",
            "shape": "value",
            "name": config.get("name") or key.replace("_", "-"),
            "ciphertext": cid,
        },
        "annotations": {
            "imported_from": f"{source}#{key}",
            "imported_at": datetime.now(UTC).isoformat(timespec="seconds"),
        },
    }


def _command(request: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
    """The generic adapter: wrap an arbitrary command as an operation.

    kind and effect are node-supplied (design.md §6). The wrapped invocation
    is a real subprocess under full enforcement: scrubbed env, constructed
    PATH, isolated workspace cwd. A pure command writes `out/`, which is
    ingested into the CAS as the produced file-tree; an effectful command's
    claim is the node-supplied `claim` fields. An effectful re-run finds its
    prior outcome at `prior.json` in the workspace.
    """
    config = request["node"]["config"]
    workspace = Path(request["workspace"]["dir"])
    effect = config["effect"]

    if effect == "effectful" and "prior" in request:
        (workspace / "prior.json").write_text(to_wire(request["prior"]))

    env = scrubbed_env(request["workspace"]["path"], workspace)
    for env_name, kind in config.get("secret-env", {}).items():
        # ADR 0005: the runner injected `resolved:` in memory; hand it to the
        # wrapped process through its environment only — never argv, never disk.
        resolved = request["inputs"].get(kind, {}).get("resolved")
        if resolved is None:
            return {
                "schema": SCHEMA,
                "error": {
                    "message": f"secret-env {env_name}: no resolved plaintext "
                    f"for consumed kind {kind!r}"
                },
            }
        env[env_name] = resolved["value"]
    completed = subprocess.run(
        config["cmd"],
        capture_output=True,
        cwd=workspace,
        env=env,
    )
    if completed.returncode != 0:
        return {
            "schema": SCHEMA,
            "error": {
                "message": f"command exited {completed.returncode}",
                "detail": completed.stderr.decode(errors="replace"),
            },
        }

    if effect == "pure":
        out_dir = workspace / "out"
        entries: dict[str, Any] = {}
        for file in sorted(p for p in out_dir.rglob("*") if p.is_file()):
            # Tree keys are identity: always /-separated, or the same tree
            # would hash to different CIDs per platform.
            entries[file.relative_to(out_dir).as_posix()] = {
                "content": put_blob(ctx.store, file.read_bytes())
            }
        tree_cid = put_doc(ctx.store, tree_doc(entries))
        claim: dict[str, Any] = {
            "schema": SCHEMA,
            "kind": config["kind"],
            "content": tree_cid,
        }
        return {"schema": SCHEMA, "claim": claim}

    claim = {"schema": SCHEMA, "kind": config["kind"], **config.get("claim", {})}
    return {
        "schema": SCHEMA,
        "claim": claim,
        "annotations": {"workspace": str(workspace)},
    }


BUILTINS: dict[str, Builtin] = {
    "import-values": Builtin(
        name="import-values",
        produces="values",
        effect="pure",
        source=True,
        run=_import_values,
    ),
    "import-sops": Builtin(
        name="import-sops",
        produces="secret",
        effect="pure",
        source=True,
        run=_import_sops,
    ),
    "command": Builtin(
        # produces/effect/consumes all node-supplied for the adapter.
        name="command",
        produces=None,
        effect=None,
        run=_command,
    ),
}

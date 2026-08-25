# workspace.py
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

"""Workspace materialization and the scrubbed environment (design.md §6).

The runner physically enforces visibility: an isolated, runner-owned
workspace; consumed content claims materialized as files under
`inputs/<kind>…`; a constructed PATH; an environment scrubbed down to what
the run needs — the plugin assembles nothing, and nothing from the calling
environment leaks in.

The constructed PATH (M6): consumed `bootstrap` and `tool` claims contribute
their realized binaries' directories, ahead of the /usr/bin:/bin baseline
that keeps a shell findable for wrapped commands.
"""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any

from freckles.documents import Cid
from freckles.store import get_doc
from freckles.store.base import StoreBackend

BASELINE_PATH = ["/usr/bin", "/bin"]

_PATH_KINDS = ("bootstrap", "tool")  # the tool store's claim kinds (§4, §11)


class UnrealizedClaim(Exception):
    """A consumed bootstrap/tool claim with no realized path on this machine."""


def constructed_path(node_name: str, inputs: dict[str, dict[str, Any]]) -> list[str]:
    """Realized bootstrap/tool dirs (sorted by consumed kind) + the baseline.

    The path annotation names the realized binary; its directory goes on
    PATH. A consumed bootstrap/tool claim with no path annotation on this
    machine is a hard error — realization gaps are not healed automatically
    (design.md §6, M6).
    """
    dirs: list[str] = []
    for kind in sorted(inputs):
        entry = inputs[kind]
        if entry["claim"].get("kind") not in _PATH_KINDS:
            continue
        realized = (entry.get("annotations") or {}).get("path")
        if not realized:
            raise UnrealizedClaim(
                f"{node_name}: consumed {kind} claim is not realized on this "
                "machine (no path annotation) — re-running its producing node "
                "realizes it"
            )
        directory = str(Path(realized).parent)
        if directory not in dirs:
            dirs.append(directory)
    return dirs + list(BASELINE_PATH)


def scrubbed_env(path: list[str], workspace: Path) -> dict[str, str]:
    """The complete child environment — built, never inherited."""
    return {
        "PATH": ":".join(path),
        "HOME": str(workspace / "home"),
        "TMPDIR": str(workspace / "tmp"),
        "LANG": "C.UTF-8",
    }


def materialize_workspace(
    root: Path, node_name: str, inputs: dict[str, dict[str, Any]], store: StoreBackend
) -> Path:
    """Create the isolated workspace and materialize content-bearing inputs.

    `inputs` is the request-document shape: consumed kind -> {cid, claim, …}.
    Conventions: a `file-tree` claim materializes as directory `inputs/<kind>/`;
    a claim with a raw `content` blob link materializes as file `inputs/<kind>`.
    """
    workspace = root / node_name.replace("/", "--")
    for sub in ("", "home", "tmp", "out", "inputs"):
        (workspace / sub).mkdir(parents=True, exist_ok=True)

    for kind, entry in inputs.items():
        claim = entry["claim"]
        content = claim.get("content")
        if not isinstance(content, Cid):
            continue
        target = workspace / "inputs" / kind
        if content.codec == 0x71:  # a tree document
            _materialize_tree(get_doc(store, content), target, store)
        else:
            target.write_bytes(store.get(content))
    return workspace


def _materialize_tree(tree: dict[str, Any], target: Path, store: StoreBackend) -> None:
    for rel_path, entry in tree["entries"].items():
        file_path = target / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(store.get(entry["content"]))
        if entry.get("exec"):
            file_path.chmod(file_path.stat().st_mode | stat.S_IXUSR)

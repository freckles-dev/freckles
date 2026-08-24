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

Skeleton simplification, recorded here on purpose: the constructed PATH ends
with /usr/bin:/bin so wrapped commands find a shell; once tool claims exist,
PATH is built from consumed tools plus this baseline.
"""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any

from freckles.documents import Cid
from freckles.store import get_doc
from freckles.store.base import StoreBackend

BASELINE_PATH = ["/usr/bin", "/bin"]


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

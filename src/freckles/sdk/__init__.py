# __init__.py
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

"""The public plugin SDK — with the CLI, the only stable v1 surface.

Sugar, never contract (design.md §6): the process protocol is DAG-JSON
documents on stdio, and these helpers only read and write that wire. A
plugin in any language can speak it without this module.
"""

from __future__ import annotations

import sys
from typing import IO, Any

from freckles.documents import SCHEMA, from_wire, to_wire

__all__ = ["emit_error", "emit_outcome", "read_request"]


def read_request(stream: IO[str] | None = None) -> dict[str, Any]:
    """Parse the request document from stdin (or the given stream)."""
    return from_wire((stream or sys.stdin).read())


def emit_outcome(
    claim: dict[str, Any],
    annotations: dict[str, Any] | None = None,
    ingest: str | None = None,
    stream: IO[str] | None = None,
) -> None:
    """Write the outcome document; stamps the claim's schema if omitted.

    `ingest` names a workspace-relative directory for the runner to land
    in the store as the claim's content (design.md §6).
    """
    claim = {"schema": SCHEMA, **claim}
    document: dict[str, Any] = {"schema": SCHEMA, "claim": claim}
    if annotations:
        document["annotations"] = annotations
    if ingest is not None:
        document["ingest"] = ingest
    (stream or sys.stdout).write(to_wire(document))


def emit_error(
    message: str,
    detail: str | None = None,
    exit_code: int | None = None,
    stream: IO[str] | None = None,
) -> None:
    """Write the structured error document (exit nonzero is the caller's job)."""
    error: dict[str, Any] = {"message": message}
    if detail is not None:
        error["detail"] = detail
    if exit_code is not None:
        error["exit_code"] = exit_code
    (stream or sys.stdout).write(to_wire({"schema": SCHEMA, "error": error}))

# context.py
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

"""The trusted-core context a run executes against."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from freckles.state import AnnotationsIndex, AuditLog
from freckles.store.base import StoreBackend


@dataclass(slots=True)
class RunContext:
    """What the runner (and in-process built-ins, as trusted core) may touch.

    Spawned plugins never see any of this — they get only the request document.
    """

    store: StoreBackend
    annotations: AnnotationsIndex
    config_dir: Path
    freckles_version: str
    workspace_root: Path
    audit: AuditLog | None = None  # every walk-driven run appends here

# build.py
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

"""Build a plugin script into one standalone payload (M6).

The published payload is a bare executable (design.md §6: v1 plugins
publish as bare executables at pinned URLs), so the SDK the script
dogfoods is inlined above it — the payload imports nothing outside the
standard library. Tests and the release pipeline build through here;
the artifact boundary (ADR 0004) stays a single file.
"""

from __future__ import annotations

from pathlib import Path

_SHEBANG = "#!/usr/bin/env python3\n"


def build_payload(script: Path | str) -> bytes:
    """The script with `from freckles.sdk import …` replaced by the SDK itself."""
    plugin_source = Path(script).read_text()
    if "from __future__" in plugin_source:
        raise ValueError(
            f"{script}: plugin scripts may not use `from __future__` imports — "
            "the payload inlines the SDK above the script"
        )
    sdk_source = (Path(__file__).with_name("__init__.py")).read_text()
    body = "\n".join(
        line
        for line in plugin_source.splitlines()
        if not line.startswith(("#!", "from freckles.sdk import"))
    )
    return f"{_SHEBANG}{sdk_source}\n{body}\n".encode()

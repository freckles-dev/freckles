# _debug.py
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

"""Debug helpers, installed into `builtins` when the dev dependencies are available.

Importing this module makes `dbg`, `DBG`, `ic`, `insp` and `wat`/`wats` usable
anywhere without imports, and activates `snoop`. `tests/conftest.py` imports it, so
the helpers are always available in tests; in a script or REPL, opt in explicitly:

    import freckles._debug  # noqa: F401

The package itself deliberately does NOT import this module: mutating `builtins`
is a side effect a library must not impose on its consumers.
"""

import builtins
from typing import IO, Any

try:
    from rich import inspect  # ty: ignore[unresolved-import]
    from rich import (  # ty: ignore[unresolved-import,unused-ignore-comment]
        print as rich_print,
    )

    setattr(builtins, "insp", inspect)

    def dbg(
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        file: IO[str] | None = None,
        flush: bool = False,
    ) -> None:
        for obj in objects:
            try:
                rich_print(obj, sep=sep, end=end, file=file, flush=flush)
            except Exception:
                # rich can choke on objects whose repr looks like console markup;
                # plain print handles anything rich can't. If the repr itself is
                # broken, let that surface -- nothing could print the object anyway.
                print(obj, sep=sep, end=end, file=file, flush=flush)

    setattr(builtins, "dbg", dbg)

except ImportError:  # Graceful fallback if Rich isn't installed.
    pass

try:
    from devtools import debug  # ty: ignore[unresolved-import,unused-ignore-comment]

    setattr(builtins, "DBG", debug)
except ImportError:  # Graceful fallback if devtools isn't installed.
    pass

try:
    from icecream import ic  # ty: ignore[unresolved-import,unused-ignore-comment]

    setattr(builtins, "ic", ic)
except ImportError:  # Graceful fallback if IceCream isn't installed.
    pass

try:
    from wat import wat  # ty: ignore[unresolved-import,unused-ignore-comment]

    setattr(builtins, "wats", wat.s)
    setattr(builtins, "wat", wat)
except ImportError:  # Graceful fallback if wat isn't installed.
    pass

try:
    import snoop  # ty: ignore[unresolved-import,unused-ignore-comment]

    snoop.install()
except ImportError:  # Graceful fallback if Snoop isn't installed.
    pass

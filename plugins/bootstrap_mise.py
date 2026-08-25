#!/usr/bin/env python3
# bootstrap_mise.py
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

"""bootstrap-mise: realize a version-pinned mise (design.md §11).

The default bootstrap. Downloads the single static mise binary for this
platform (mise's release-artifact naming; node config may pin `url` and
`sha256` explicitly) and realizes it under the persistent realization
root. The claim stays machine-independent — {kind, tool, version,
platform} — while the realized path travels as an annotation, so the
runner can put mise on consumers' constructed PATH.

Published as a standalone payload: `freckles.sdk` is inlined at build
time (freckles.sdk.build), everything else is standard library.
"""

import hashlib
import os
import platform
import sys
import urllib.error
import urllib.request

from freckles.sdk import emit_error, emit_outcome, read_request

RELEASES = "https://github.com/jdx/mise/releases/download"

_ARCHES = {"x86_64": "x64", "amd64": "x64", "aarch64": "arm64", "arm64": "arm64"}


def mise_platform() -> str:
    machine = platform.machine().lower()
    return f"{platform.system().lower()}-{_ARCHES.get(machine, machine)}"


def default_url(version: str, plat: str) -> str:
    return f"{RELEASES}/v{version}/mise-v{version}-{plat}"


def main() -> int:
    request = read_request()
    config = request["node"]["config"]
    version = config["version"]
    plat = mise_platform()
    url = config.get("url") or default_url(version, plat)

    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
    except (urllib.error.URLError, OSError) as error:
        emit_error(f"fetch failed: {url}: {error}")
        return 1

    expected = config.get("sha256")
    if expected:
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            emit_error(
                f"checksum mismatch for {url}: expected {expected}, got {actual}"
            )
            return 1

    bin_dir = os.path.join(request["workspace"]["envs"], "mise", version, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    binary = os.path.join(bin_dir, "mise")
    with open(binary, "wb") as f:
        f.write(data)
    os.chmod(binary, 0o755)

    emit_outcome(
        {"kind": "bootstrap", "tool": "mise", "version": version, "platform": plat},
        annotations={"path": binary},
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

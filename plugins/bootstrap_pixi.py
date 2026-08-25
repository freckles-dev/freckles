#!/usr/bin/env python3
# bootstrap_pixi.py
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

"""bootstrap-pixi: realize a version-pinned pixi (design.md §11).

The first-class peer bootstrap for solved conda-forge stacks. Downloads
the single static pixi binary for this platform (pixi's release-artifact
naming — rust triples, musl on linux; node config may pin `url` and
`sha256` explicitly) and realizes it under the persistent realization
root. The claim stays machine-independent — {kind, tool, version,
platform} in the shared tool-claim platform convention — so the
swappable-bootstrap contract holds across routes.

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

RELEASES = "https://github.com/prefix-dev/pixi/releases/download"

_ARCHES = {"x86_64": "x64", "amd64": "x64", "aarch64": "arm64", "arm64": "arm64"}
_TRIPLE_ARCHES = {"x64": "x86_64", "arm64": "aarch64"}
_TRIPLE_SYSTEMS = {"linux": "unknown-linux-musl", "darwin": "apple-darwin"}


def claim_platform() -> str:
    machine = platform.machine().lower()
    return f"{platform.system().lower()}-{_ARCHES.get(machine, machine)}"


def rust_triple(system: str, machine: str) -> str:
    arch = _ARCHES.get(machine.lower(), machine.lower())
    return f"{_TRIPLE_ARCHES.get(arch, arch)}-{_TRIPLE_SYSTEMS.get(system, system)}"


def default_url(version: str, triple: str) -> str:
    return f"{RELEASES}/v{version}/pixi-{triple}"


def main() -> int:
    request = read_request()
    config = request["node"]["config"]
    version = config["version"]
    triple = rust_triple(platform.system().lower(), platform.machine())
    url = config.get("url") or default_url(version, triple)

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

    bin_dir = os.path.join(request["workspace"]["envs"], "pixi", version, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    binary = os.path.join(bin_dir, "pixi")
    with open(binary, "wb") as f:
        f.write(data)
    os.chmod(binary, 0o755)

    emit_outcome(
        {
            "kind": "bootstrap",
            "tool": "pixi",
            "version": version,
            "platform": claim_platform(),
        },
        annotations={"path": binary},
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

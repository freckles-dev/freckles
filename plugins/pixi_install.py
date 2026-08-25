#!/usr/bin/env python3
# pixi_install.py
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

"""pixi-install: sha256-locked tools from conda-forge (design.md §11).

The hash-locked route: each tool gets its own pixi workspace under the
persistent realization root — a minimal pixi.toml with the conda-forge
channel and an exact ==version pin — and `pixi install` resolves it,
writing the pixi.lock (per-package sha256) beside the manifest. Never
`pixi global`, which pins by version spec only (Bootstrap tool
evaluation). `pixi` is invoked by bare name off the constructed PATH.

The claim is the shared tool-claim contract — {kind, tool, version,
platform} — identical across bootstrap routes, so swapping the route
re-derives the tool without rippling to its consumers.

Published as a standalone payload: `freckles.sdk` is inlined at build
time (freckles.sdk.build), everything else is standard library.
"""

import os
import platform
import subprocess
import sys

from freckles.sdk import emit_error, emit_outcome, read_request

_ARCHES = {"x86_64": "x64", "amd64": "x64", "aarch64": "arm64", "arm64": "arm64"}
_CONDA_SYSTEMS = {"linux": "linux", "darwin": "osx"}
_CONDA_ARCHES = {"x64": "64", "arm64": "arm64"}


def claim_platform() -> str:
    machine = platform.machine().lower()
    return f"{platform.system().lower()}-{_ARCHES.get(machine, machine)}"


def conda_platform() -> str:
    system, arch = claim_platform().split("-")
    return f"{_CONDA_SYSTEMS.get(system, system)}-{_CONDA_ARCHES.get(arch, arch)}"


def workspace_manifest(package: str, version: str) -> str:
    return (
        f'[workspace]\nname = "{package}"\nchannels = ["conda-forge"]\n'
        f'platforms = ["{conda_platform()}"]\n\n'
        f'[dependencies]\n{package} = "=={version}"\n'
    )


def main() -> int:
    request = read_request()
    config = request["node"]["config"]
    package, version = config["package"], config["version"]

    workspace = os.path.join(
        request["workspace"]["envs"], "pixi-workspaces", package, version
    )
    os.makedirs(workspace, exist_ok=True)
    with open(os.path.join(workspace, "pixi.toml"), "w") as f:
        f.write(workspace_manifest(package, version))

    try:
        install = subprocess.run(
            ["pixi", "install", "--manifest-path", workspace], capture_output=True
        )
    except OSError:
        emit_error(
            "pixi not found on the constructed PATH — is the consumed "
            "bootstrap claim realized?"
        )
        return 1
    if install.returncode != 0:
        emit_error(
            f"pixi install {package}=={version} failed",
            detail=install.stderr.decode(errors="replace"),
            exit_code=install.returncode,
        )
        return 1

    binary = os.path.join(workspace, ".pixi", "envs", "default", "bin", package)
    if not os.path.isfile(binary):
        emit_error(f"{package}=={version}: installed, but no executable at {binary}")
        return 1

    emit_outcome(
        {
            "kind": "tool",
            "tool": package,
            "version": version,
            "platform": claim_platform(),
        },
        annotations={"path": binary},
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

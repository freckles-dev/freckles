#!/usr/bin/env python3
# mise_install.py
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

"""mise-install: realize one tool through the consumed bootstrap (design.md §11).

Invokes `mise` by bare name — the runner has put the consumed bootstrap
claim's realized binary on the constructed PATH. Installs land under the
persistent realization root (MISE_DATA_DIR), so the version pin in node
config re-derives the same tool on any machine; the claim stays
machine-independent and the realized executable travels as annotation.

Published as a standalone payload: `freckles.sdk` is inlined at build
time (freckles.sdk.build), everything else is standard library.
"""

import os
import platform
import subprocess
import sys

from freckles.sdk import emit_error, emit_outcome, read_request

_ARCHES = {"x86_64": "x64", "amd64": "x64", "aarch64": "arm64", "arm64": "arm64"}


def mise_platform() -> str:
    machine = platform.machine().lower()
    return f"{platform.system().lower()}-{_ARCHES.get(machine, machine)}"


def main() -> int:
    request = read_request()
    config = request["node"]["config"]
    package, version = config["package"], config["version"]
    spec = f"{package}@{version}"

    env = dict(os.environ)
    env["MISE_DATA_DIR"] = os.path.join(request["workspace"]["envs"], "mise-data")
    env["MISE_YES"] = "1"

    try:
        install = subprocess.run(
            ["mise", "install", spec], capture_output=True, env=env
        )
    except OSError:
        emit_error(
            "mise not found on the constructed PATH — is the consumed bootstrap claim realized?"
        )
        return 1
    if install.returncode != 0:
        emit_error(
            f"mise install {spec} failed",
            detail=install.stderr.decode(errors="replace"),
            exit_code=install.returncode,
        )
        return 1

    # `mise which` is the layout contract (M9 acceptance finding): pipx-backend
    # tools land in a venv `bin/`, github-backend tools (uv) in a dist dir with
    # `.mise-bins` symlinks — only mise itself knows where the executable is.
    which = subprocess.run(
        ["mise", "which", "--tool", spec, package],
        capture_output=True,
        env=env,
        text=True,
    )
    if which.returncode != 0:
        emit_error(f"mise which {spec} failed", detail=which.stderr)
        return 1
    binary = which.stdout.strip()
    if not os.path.isfile(binary):
        emit_error(f"{spec}: installed, but no executable at {binary}")
        return 1

    emit_outcome(
        {
            "kind": "tool",
            "tool": package,
            "version": version,
            "platform": mise_platform(),
        },
        annotations={"path": binary},
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

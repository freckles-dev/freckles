# ssh_vendor.py
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

"""import-git's SSH transport: a paramiko vendor (M8 design act).

Importing this module requires paramiko — the `ssh` extra; the registry
turns the ImportError into the install hint. dulwich 1.x dropped its
contrib paramiko vendor, so freckles carries the ~screenful itself rather
than shelling to a host `ssh` (the decided-against subprocess vendor).

Host keys are strict: system known_hosts, unknown hosts rejected — an
unknown host is an error naming the fix, never a silent trust-on-first-use.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import paramiko
from dulwich.client import SSHVendor

if TYPE_CHECKING:
    from dulwich.client import SubprocessWrapper


class _ChannelWrapper:
    """The read/write/close surface dulwich's protocol drives."""

    def __init__(self, client: paramiko.SSHClient, channel: paramiko.Channel) -> None:
        self.client = client
        self.channel = channel
        channel.setblocking(True)

    def can_read(self) -> bool:
        return self.channel.recv_ready()

    def write(self, data: bytes) -> None:
        self.channel.sendall(data)

    def read(self, n: int | None = None) -> bytes:
        wanted = n or 4096
        data = self.channel.recv(wanted)
        while n and 0 < len(data) < n:
            more = self.channel.recv(n - len(data))
            if not more:
                break
            data += more
        return data

    def close(self) -> None:
        self.channel.close()
        self.client.close()


class ParamikoSSHVendor(SSHVendor):
    def run_command(
        self,
        host: str,
        command: bytes | str,
        username: str | None = None,
        port: int | None = None,
        password: str | None = None,
        key_filename: str | None = None,
        ssh_command: str | None = None,
        protocol_version: int | None = None,
    ) -> SubprocessWrapper:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        client.connect(
            hostname=host,
            username=username,
            port=port or 22,
            password=password,
            key_filename=key_filename,
        )
        transport = client.get_transport()
        if transport is None:
            client.close()
            raise paramiko.SSHException(f"no transport to {host}")
        channel = transport.open_session()
        channel.exec_command(
            command.decode() if isinstance(command, bytes) else command
        )
        # The wrapper speaks the read/write/close surface the protocol
        # drives; the base annotation names dulwich's subprocess wrapper.
        return cast("SubprocessWrapper", _ChannelWrapper(client, channel))

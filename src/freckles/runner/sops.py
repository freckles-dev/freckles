# sops.py
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

"""In-process sops/age decryption for the execution boundary (design.md §9).

The age stanza in the file's sops metadata yields the data key (decrypted
with identities from `SOPS_AGE_KEY_FILE`); each value is AES256_GCM with the
key's path as AAD, so a value cannot be tampered with or swapped between
keys. The file-level MAC is a named v1 cut — per-value GCM authentication
carries the integrity story (Milestone 2 decision, 2026-08-24).

Decryption always materializes from the working copy: the CAS ciphertext is
identity and transport, never the decrypt source — a lone ENC value is
undecryptable without its file's age-encrypted data key anyway.
"""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path
from typing import Any

import yaml


class SopsError(Exception):
    """A secret value cannot be resolved to plaintext on this machine."""


_ENC = re.compile(
    r"ENC\[AES256_GCM"
    r",data:(?P<data>[^,]*)"
    r",iv:(?P<iv>[^,]*)"
    r",tag:(?P<tag>[^,]*)"
    r",type:(?P<type>[^\]]*)\]"
)
_ARMOR = re.compile(
    r"-----BEGIN AGE ENCRYPTED FILE-----\n(?P<body>.*?)"
    r"\n?-----END AGE ENCRYPTED FILE-----",
    re.DOTALL,
)


def resolve_value(imported_from: str) -> str:
    """Decrypt one key of a sops file, addressed as `/path/to/file#key`."""
    path_text, separator, key = imported_from.rpartition("#")
    if not separator:
        raise SopsError(f"malformed secret address {imported_from!r} (missing #key)")
    path = Path(path_text)
    if not path.exists():
        raise SopsError(f"sops file {path} is not in the working copy")

    document = yaml.safe_load(path.read_text())
    metadata = document.get("sops")
    if not isinstance(metadata, dict):
        raise SopsError(f"{path} has no sops metadata")
    if key not in document:
        raise SopsError(f"{path} has no key {key!r}")

    data_key = _data_key(metadata, path)
    return _decrypt_value(document[key], data_key, aad=f"{key}:".encode())


def _identities() -> list[Any]:
    from pyrage import x25519

    key_file = os.environ.get("SOPS_AGE_KEY_FILE")
    if not key_file:
        raise SopsError(
            "SOPS_AGE_KEY_FILE is not set — no age identity to decrypt with"
        )
    if not Path(key_file).exists():
        raise SopsError(f"age key file {key_file} does not exist")
    identities = [
        x25519.Identity.from_str(line.strip())
        for line in Path(key_file).read_text().splitlines()
        if line.strip().startswith("AGE-SECRET-KEY-")
    ]
    if not identities:
        raise SopsError(f"no age identities found in {key_file}")
    return identities


def _data_key(metadata: dict[str, Any], path: Path) -> bytes:
    from pyrage import decrypt

    identities = _identities()
    for stanza in metadata.get("age") or []:
        try:
            return decrypt(_dearmor(stanza["enc"]), identities)
        except Exception:  # noqa: BLE001 — try the next recipient stanza
            continue
    raise SopsError(f"no age stanza of {path} decrypts with the configured identity")


def _dearmor(text: str) -> bytes:
    match = _ARMOR.search(text)
    if not match:
        raise SopsError("age stanza is not armored age data")
    return base64.standard_b64decode("".join(match.group("body").split()))


def _decrypt_value(enc_text: Any, data_key: bytes, aad: bytes) -> str:
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    if not isinstance(enc_text, str):
        raise SopsError("only scalar sops values are resolvable in v1")
    match = _ENC.match(enc_text.strip())
    if not match:
        raise SopsError("value is not sops AES256_GCM ciphertext")

    iv = base64.standard_b64decode(match.group("iv"))
    tag = base64.standard_b64decode(match.group("tag"))
    data = base64.standard_b64decode(match.group("data"))
    decryptor = Cipher(algorithms.AES(data_key), modes.GCM(iv, tag)).decryptor()
    decryptor.authenticate_additional_data(aad)
    try:
        plaintext = decryptor.update(data) + decryptor.finalize()
    except InvalidTag as error:
        raise SopsError("ciphertext failed authentication") from error
    return plaintext.decode()

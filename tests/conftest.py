"""Pytest configuration and shared fixtures for freckles tests."""

from pathlib import Path

import pytest

# Installs the dbg/DBG/ic/insp/wat builtins (and activates snoop) for all tests.
import freckles._debug  # noqa: F401

CONFORMANCE = Path(__file__).parent.parent / "conformance"


def hashberg_encode(document: dict) -> bytes:
    """Encode a value-model document with the hashberg pair (dag-cbor/multiformats).

    The independent second encoder of the dual-encoder cross-check: tests
    assert its bytes match the production (libipld) encoding exactly.
    """
    import dag_cbor
    from multiformats import CID as HbCID

    from freckles.documents import Cid

    def lower(value):
        if isinstance(value, Cid):
            return HbCID.decode(str(value))
        if isinstance(value, dict):
            return {k: lower(v) for k, v in value.items()}
        if isinstance(value, list):
            return [lower(v) for v in value]
        return value

    return dag_cbor.encode(lower(document))


@pytest.fixture
def sops_lab(tmp_path, monkeypatch):
    """A hermetic sops/age lab: generated identity + a real sops-encrypt.

    Mints genuine sops-format files (per-value AES256_GCM with the key path
    as AAD, data key age-encrypted to the lab's recipient) so decrypt tests
    and rotations run with no sops binary and no committed key material.
    SOPS_AGE_KEY_FILE points at the generated identity, as the runner honors.
    """
    import base64
    import os as _os
    from dataclasses import dataclass

    import yaml
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from pyrage import encrypt as age_encrypt
    from pyrage import x25519

    identity = x25519.Identity.generate()
    key_file = tmp_path / "age-key.txt"
    key_file.write_text(f"{identity}\n")
    monkeypatch.setenv("SOPS_AGE_KEY_FILE", str(key_file))

    def _armor(data: bytes) -> str:
        body = base64.standard_b64encode(data).decode()
        lines = [body[i : i + 64] for i in range(0, len(body), 64)]
        return (
            "-----BEGIN AGE ENCRYPTED FILE-----\n"
            + "\n".join(lines)
            + "\n-----END AGE ENCRYPTED FILE-----\n"
        )

    def encrypt_file(path: Path, values: dict[str, str]) -> None:
        data_key = _os.urandom(32)
        document: dict = {}
        for key, plaintext in values.items():
            iv = _os.urandom(32)  # sops uses 32-byte GCM IVs
            encryptor = Cipher(algorithms.AES(data_key), modes.GCM(iv)).encryptor()
            encryptor.authenticate_additional_data(f"{key}:".encode())
            ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
            document[key] = (
                "ENC[AES256_GCM,"
                f"data:{base64.standard_b64encode(ciphertext).decode()},"
                f"iv:{base64.standard_b64encode(iv).decode()},"
                f"tag:{base64.standard_b64encode(encryptor.tag).decode()},"
                "type:str]"
            )
        document["sops"] = {
            "age": [
                {
                    "recipient": str(identity.to_public()),
                    "enc": _armor(age_encrypt(data_key, [identity.to_public()])),
                }
            ],
            "lastmodified": "2026-08-24T12:00:00Z",
            "mac": "",  # MAC verification is a named v1 cut
            "version": "3.9.1",
        }
        path.write_text(yaml.safe_dump(document, sort_keys=False))

    @dataclass
    class SopsLab:
        key_file: Path
        encrypt: object

    return SopsLab(key_file=key_file, encrypt=encrypt_file)


@pytest.fixture
def encode_checked():
    """Encode a store document with BOTH encoders, asserting byte-identity.

    Seam tests mint documents through this wherever practical, making the
    whole suite a rolling cross-implementation check ("Testing strategy").
    Returns (bytes, Cid) exactly like `documents.encode`.
    """
    from freckles.documents import encode

    def _encode(document: dict):
        data, cid = encode(document)
        assert hashberg_encode(document) == data, (
            "libipld and hashberg dag-cbor encodings diverge"
        )
        return data, cid

    return _encode

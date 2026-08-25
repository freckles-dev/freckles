"""Pytest configuration and shared fixtures for freckles tests."""

from pathlib import Path

import pytest

# Installs the dbg/DBG/ic/insp/wat builtins (and activates snoop) for all tests.
import freckles._debug  # noqa: F401

CONFORMANCE = Path(__file__).parent.parent / "conformance"

# A stdlib stand-in for the mise binary: honest install/where semantics over
# MISE_DATA_DIR, every invocation recorded — the hermetic suite's mise. The
# "installed" tool is a script printing "<package> <version>", so chain tests
# can prove a tool was invoked by bare name off the constructed PATH.
FAKE_MISE = """\
#!/usr/bin/env python3
import json, os, sys

data_dir = os.environ["MISE_DATA_DIR"]
os.makedirs(data_dir, exist_ok=True)
with open(os.path.join(data_dir, "invocations.jsonl"), "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\\n")

command, spec = sys.argv[1], sys.argv[2]
package, _, version = spec.partition("@")
install_dir = os.path.join(data_dir, "installs", package, version)
if command == "install":
    bin_dir = os.path.join(install_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    tool = os.path.join(bin_dir, package)
    with open(tool, "w") as f:
        f.write("#!/usr/bin/env python3\\nprint(%r)\\n" % f"{package} {version}")
    os.chmod(tool, 0o755)
elif command == "where":
    if not os.path.isdir(install_dir):
        print(f"{spec} is not installed", file=sys.stderr)
        sys.exit(1)
    print(install_dir)
else:
    print(f"fake mise: unknown command {command}", file=sys.stderr)
    sys.exit(2)
"""


@pytest.fixture
def fake_mise_source() -> str:
    return FAKE_MISE


# The pixi stand-in: models `pixi install --manifest-path` over a per-tool
# workspace — reads the exact pin from pixi.toml, realizes the tool under
# .pixi/envs/default/bin, writes the pixi.lock beside the manifest (the
# sha256 lock real pixi produces), and records every invocation.
FAKE_PIXI = """\
#!/usr/bin/env python3
import json, os, re, sys

args = sys.argv[1:]
if args[0] != "install":
    print(f"fake pixi: unknown command {args[0]}", file=sys.stderr)
    sys.exit(2)
manifest_dir = args[args.index("--manifest-path") + 1]
with open(os.path.join(manifest_dir, "invocations.jsonl"), "a") as log:
    log.write(json.dumps(args) + "\\n")
with open(os.path.join(manifest_dir, "pixi.toml")) as f:
    manifest = f.read()
match = re.search(r'^(\\S+) = "==([^"]+)"$', manifest, re.M)
if not match:
    print("fake pixi: no exact pin in pixi.toml", file=sys.stderr)
    sys.exit(1)
package, version = match.group(1), match.group(2)
bin_dir = os.path.join(manifest_dir, ".pixi", "envs", "default", "bin")
os.makedirs(bin_dir, exist_ok=True)
tool = os.path.join(bin_dir, package)
with open(tool, "w") as f:
    f.write("#!/usr/bin/env python3\\nprint(%r)\\n" % f"{package} {version}")
os.chmod(tool, 0o755)
with open(os.path.join(manifest_dir, "pixi.lock"), "w") as f:
    f.write("version: 6\\n# sha256-locked by fake pixi\\n")
"""


@pytest.fixture
def fake_pixi_source() -> str:
    return FAKE_PIXI


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

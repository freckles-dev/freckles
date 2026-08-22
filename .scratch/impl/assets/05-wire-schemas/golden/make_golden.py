# /// script
# requires-python = ">=3.12"
# dependencies = ["dag-cbor>=0.3", "multiformats[full]>=0.3"]
# ///
# PROTOTYPE — wayfinder ticket 05. Deterministic golden-fixture generator:
# builds the skeleton-chain store documents, computes their real CIDv1
# addresses, and writes <name>.dagjson.json + CIDS.txt. Re-run with:
#   uv run make_golden.py
import base64
import json
import pathlib

import dag_cbor
from multiformats import CID, multihash

OUT = pathlib.Path(__file__).parent


def cid_for(doc) -> CID:
    return CID("base32", 1, "dag-cbor", multihash.digest(dag_cbor.encode(doc), "sha2-256"))


def raw_cid(data: bytes) -> CID:
    return CID("base32", 1, "raw", multihash.digest(data, "sha2-256"))


def to_dagjson(v):
    if isinstance(v, CID):
        return {"/": str(v)}
    if isinstance(v, bytes):
        return {"/": {"bytes": base64.b64encode(v).decode().rstrip("=")}}
    if isinstance(v, dict):
        return {k: to_dagjson(x) for k, x in v.items()}
    if isinstance(v, list):
        return [to_dagjson(x) for x in v]
    return v


docs: dict[str, dict] = {}
cids: dict[str, CID] = {}


def put(name: str, doc: dict) -> CID:
    docs[name] = doc
    cids[name] = cid_for(doc)
    return cids[name]


# --- blobs (raw) -------------------------------------------------------------
values_blob = raw_cid(b'{"karakeep": {"enabled": true}}\n')
cipher_blob = raw_cid(b"PROTOTYPE-SOPS-CIPHERTEXT")
payload_blob = raw_cid(b"PROTOTYPE-PLUGIN-PAYLOAD")

# --- claims ------------------------------------------------------------------
put("claim-values-apps", {"schema": 1, "kind": "values", "key": "apps", "content": values_blob})
put("claim-secret-proxmox", {
    "schema": 1, "kind": "secret", "shape": "value",
    "name": "proxmox-api-token", "ciphertext": cipher_blob,
})
put("claim-tool-opentofu", {
    "schema": 1, "kind": "tool", "tool": "opentofu",
    "version": "1.8.2", "platform": "linux-64",
})
put("claim-plugin-tofu-apply", {
    "schema": 1, "kind": "plugin", "name": "tofu-apply",
    "version": "0.4.2", "payload": payload_blob,
})
put("claim-infra-staging", {
    "schema": 1, "kind": "talos-cluster", "name": "staging",
    "endpoint": "https://10.0.50.50:6443",
    "ca-fingerprint": "sha256:PROTOTYPE",
})

# --- derivation + provenance (the canonical bytes, design.md §8) -------------
put("derivation-infra-staging", {
    "schema": 1,
    "plugin": cids["claim-plugin-tofu-apply"],
    "config": {"module": "talos-proxmox"},
    "inputs": {
        "tool": cids["claim-tool-opentofu"],
        "values": cids["claim-values-apps"],
        "secret": cids["claim-secret-proxmox"],
    },
})
put("derivation-values-apps", {          # built-in: freckles version, no plugin CID
    "schema": 1,
    "plugin": {"builtin": "import-values", "freckles": "0.1.0"},
    "config": {"file": "cluster.yaml", "key": "apps"},
    "inputs": {},
})
put("provenance-infra-staging", {
    "schema": 1,
    "derivation": cids["derivation-infra-staging"],
    "outcome": cids["claim-infra-staging"],
})

# --- resolution document (skeleton chain) ------------------------------------
config_snapshot = put("tree-config-snapshot", {
    "schema": 1,
    "entries": {"freckles.yaml": {"content": raw_cid(b"PROTOTYPE-CONFIG")}},
})
put("resolution-skeleton", {
    "schema": 1,
    "config-snapshot": config_snapshot,
    "nodes": {
        "values/apps": {
            "plugin": {"builtin": "import-values", "freckles": "0.1.0"},
            "produces": "values",
            "effect": "pure",
            "config": {"file": "cluster.yaml", "key": "apps"},
            "consumes": {},
        },
        "render/site": {
            "plugin": {"builtin": "command", "freckles": "0.1.0"},
            "produces": "file-tree",
            "effect": "pure",
            "config": {"kind": "file-tree", "effect": "pure", "cmd": ["render.sh"]},
            "consumes": {"values": "values/apps"},
        },
        "deploy/site": {
            "plugin": {"builtin": "command", "freckles": "0.1.0"},
            "produces": "deployed-site",
            "effect": "effectful",
            "config": {"kind": "deployed-site", "effect": "effectful", "cmd": ["deploy.sh"]},
            "consumes": {"file-tree": "render/site"},
        },
    },
})

# --- write -------------------------------------------------------------------
manifest = []
for name, doc in docs.items():
    (OUT / f"{name}.dagjson.json").write_text(
        json.dumps(to_dagjson(doc), indent=2, sort_keys=True) + "\n"
    )
    manifest.append(f"{cids[name]}  {name}  ({len(dag_cbor.encode(doc))} bytes dag-cbor)")
manifest += [f"{c}  blob:{n}" for n, c in
             [("values", values_blob), ("ciphertext", cipher_blob), ("plugin-payload", payload_blob)]]
(OUT / "CIDS.txt").write_text("\n".join(manifest) + "\n")
print("\n".join(manifest))

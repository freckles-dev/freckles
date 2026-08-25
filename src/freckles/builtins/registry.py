# registry.py
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

"""The built-in registry: manifests + in-process implementations.

Built-ins are trusted core: they run in-process behind the same
request/outcome document interface as spawned plugins, and — unlike
plugins — may touch the store (source imports and output ingestion need
it). Shipped so far: `import-values`, `command` (skeleton), `import-sops`
(milestone 2); the remaining three built-ins land with their milestones.
"""

from __future__ import annotations

import stat
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from freckles.documents import SCHEMA, cid_for_blob, to_wire, tree_doc
from freckles.runner.context import RunContext
from freckles.runner.workspace import scrubbed_env
from freckles.store import put_blob, put_doc


@dataclass(frozen=True, slots=True)
class Builtin:
    """A built-in's manifest facts plus its in-process implementation.

    `produces`/`effect` of None mean node-supplied (the adapter rule,
    design.md §6): the node config must state them.
    """

    name: str
    produces: str | None
    effect: str | None
    consumes: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Source nodes import external content, so their derivations are
    # content-free — the heal walk must re-run them every time and let
    # extensional addressing stop the ripple when the import is unchanged.
    # (Skeleton finding, 2026-08-24: design.md §8 implies but never states
    # this rule; flagged for a design-side amendment.)
    source: bool = False
    run: Callable[[dict[str, Any], RunContext], dict[str, Any]] = None  # type: ignore[assignment]


def _import_values(request: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
    """Source node: import one key's values from a working-copy YAML file.

    Granularity principle: one independent-change unit per node — the claim
    holds the selected key's subtree, not the whole file.
    """
    config = request["node"]["config"]
    source = ctx.config_dir / config["file"]
    document = yaml.safe_load(source.read_text())
    content = yaml.safe_dump(document[config["key"]], sort_keys=True).encode()
    cid = put_blob(ctx.store, content)
    return {
        "schema": SCHEMA,
        "claim": {
            "schema": SCHEMA,
            "kind": "values",
            "key": config["key"],
            "content": cid,
        },
    }


def _import_file_tree(request: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
    """Source node: a working-copy directory becomes a file-tree claim.

    Tree keys are identity — always /-separated — and exec bits travel in
    the entries, so materialization reproduces a runnable tree anywhere.
    """
    config = request["node"]["config"]
    declared = config["dir"]
    source = (ctx.config_dir / declared).resolve()
    if not source.is_relative_to(ctx.config_dir.resolve()):
        return {
            "schema": SCHEMA,
            "error": {
                "message": f"dir {declared!r} escapes the configuration directory"
            },
        }
    if not source.is_dir():
        return {
            "schema": SCHEMA,
            "error": {"message": f"dir {declared!r} not found in the working copy"},
        }

    entries: dict[str, Any] = {}
    for file in sorted(p for p in source.rglob("*") if p.is_file()):
        entry: dict[str, Any] = {"content": put_blob(ctx.store, file.read_bytes())}
        if file.stat().st_mode & stat.S_IXUSR:
            entry["exec"] = True
        entries[file.relative_to(source).as_posix()] = entry
    return {
        "schema": SCHEMA,
        "claim": {
            "schema": SCHEMA,
            "kind": "file-tree",
            "content": put_doc(ctx.store, tree_doc(entries)),
        },
    }


def _import_git(request: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
    """Source node: a repository at a resolved commit becomes a file-tree claim.

    The fetch is embedded — dulwich, never a host git (design.md §6: a host
    dependency would defeat the bootstrap tier). The claim pins the resolved
    commit beside the tree (design.md §12); the URL stays out of identity.
    v1 simplifications, on purpose: regular files only (submodules and
    symlinks are skipped), and a pinned commit that is not an advertised tip
    is found by fetching the advertised tips (pack minimality is post-v1).
    """
    from typing import cast

    from dulwich.client import get_transport_and_path
    from dulwich.objects import Blob, Commit, ObjectID, Tag, Tree
    from dulwich.repo import MemoryRepo

    config = request["node"]["config"]
    url = config["url"]
    if "ref" in config and "commit" in config:
        return {
            "schema": SCHEMA,
            "error": {"message": "config pins both ref and commit — choose one"},
        }

    target = MemoryRepo()
    try:
        client, path = get_transport_and_path(url, **_git_auth(config))
        refs = {
            bytes(name): bytes(sha)
            for name, sha in client.get_refs(cast(bytes, path)).refs.items()
            if sha is not None
        }
    # Any transport failure must become a structured error document, never a
    # traceback — and dulwich raises a transport-specific zoo.
    except Exception as error:  # noqa: BLE001
        return {
            "schema": SCHEMA,
            "error": {"message": f"fetch failed: {url}: {error}"},
        }

    if pinned := config.get("commit"):
        wanted = ObjectID(pinned.encode())
    else:
        ref = config.get("ref")
        candidates = (
            [f"refs/heads/{ref}".encode(), f"refs/tags/{ref}".encode()]
            if ref
            else [b"HEAD"]
        )
        resolved = next((refs[c] for c in candidates if c in refs), None)
        if resolved is None:
            return {
                "schema": SCHEMA,
                "error": {"message": f"ref {ref!r} not found in {url}"},
            }
        wanted = ObjectID(resolved)

    tips = [ObjectID(sha) for sha in sorted(set(refs.values()))]
    wants = [wanted] if wanted in tips else tips
    try:
        client.fetch(path, target, determine_wants=cast("Any", lambda *_a, **_k: wants))
    except Exception as error:  # noqa: BLE001 — same boundary as above
        return {
            "schema": SCHEMA,
            "error": {"message": f"fetch failed: {url}: {error}"},
        }
    if wanted not in target.object_store:
        return {
            "schema": SCHEMA,
            "error": {"message": f"commit {pinned} not found in {url}"},
        }

    peeled = target[wanted]
    while isinstance(peeled, Tag):  # annotated tags peel to commits
        peeled = target[peeled.object[1]]
    if not isinstance(peeled, Commit):
        return {
            "schema": SCHEMA,
            "error": {"message": f"{wanted.decode()} is not a commit"},
        }
    commit_obj = peeled

    entries: dict[str, Any] = {}

    def walk(tree_id: ObjectID, prefix: str) -> None:
        tree = target[tree_id]
        if not isinstance(tree, Tree):
            return
        for name, mode, sha in tree.items():
            item = f"{prefix}{name.decode()}"
            if stat.S_ISDIR(mode):
                walk(ObjectID(sha), f"{item}/")
            elif stat.S_ISREG(mode):
                blob = target[ObjectID(sha)]
                if not isinstance(blob, Blob):
                    continue
                entry: dict[str, Any] = {"content": put_blob(ctx.store, blob.data)}
                if mode & 0o111:
                    entry["exec"] = True
                entries[item] = entry

    walk(ObjectID(commit_obj.tree), "")
    return {
        "schema": SCHEMA,
        "claim": {
            "schema": SCHEMA,
            "kind": "file-tree",
            "content": put_doc(ctx.store, tree_doc(entries)),
            "commit": commit_obj.id.decode(),
        },
    }


def _git_auth(config: dict[str, Any]) -> dict[str, Any]:
    """Transport credentials — never part of any hashed document (M8)."""
    return {}


def _import_sops(request: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
    """Source node: one key's sops ciphertext becomes a secret-value claim.

    Identity is the ciphertext (design.md §9): the claim references exactly
    this key's ENC bytes, so rotating a sibling key in the same file never
    ripples here. No decryption happens at import — that is the runner
    boundary's business (ADR 0005).
    """
    from datetime import UTC, datetime

    config = request["node"]["config"]
    source = ctx.config_dir / config["file"]
    key = config["key"]
    document = yaml.safe_load(source.read_text())
    value = document[key]
    ciphertext = (
        value.encode()
        if isinstance(value, str)
        else yaml.safe_dump(value, sort_keys=True).encode()
    )
    if config.get("store", True):
        cid = put_blob(ctx.store, ciphertext)
    else:
        # The detached variant: same hash, same claim, same ripple — the
        # bytes stay in the working copy (runner materializes from there).
        cid = cid_for_blob(ciphertext)
    return {
        "schema": SCHEMA,
        "claim": {
            "schema": SCHEMA,
            "kind": "secret",
            "shape": "value",
            "name": config.get("name") or key.replace("_", "-"),
            "ciphertext": cid,
        },
        "annotations": {
            "imported_from": f"{source}#{key}",
            "imported_at": datetime.now(UTC).isoformat(timespec="seconds"),
        },
    }


def _command(request: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
    """The generic adapter: wrap an arbitrary command as an operation.

    kind and effect are node-supplied (design.md §6). The wrapped invocation
    is a real subprocess under full enforcement: scrubbed env, constructed
    PATH, isolated workspace cwd. A pure command writes `out/`, which is
    ingested into the CAS as the produced file-tree; an effectful command's
    claim is the node-supplied `claim` fields. An effectful re-run finds its
    prior outcome at `prior.json` in the workspace.
    """
    config = request["node"]["config"]
    workspace = Path(request["workspace"]["dir"])
    effect = config["effect"]

    if effect == "effectful" and "prior" in request:
        (workspace / "prior.json").write_text(to_wire(request["prior"]))

    env = scrubbed_env(request["workspace"]["path"], workspace)

    if "verify" in request:
        # Verify mode (design.md §8, M4): the verify command reads the claim
        # document from stdin; exit 0 confirms, nonzero contradicts with the
        # stderr tail as the message. Claim only in v1 — no annotations, no
        # secrets, nothing on disk.
        completed = subprocess.run(
            config["verify"],
            input=to_wire(request["verify"]["claim"]).encode(),
            capture_output=True,
            cwd=workspace,
            env=env,
        )
        if completed.returncode == 0:
            return {"schema": SCHEMA, "verify": "confirmed"}
        message = completed.stderr.decode(errors="replace").strip() or (
            f"verify exited {completed.returncode}"
        )
        return {
            "schema": SCHEMA,
            "error": {"message": message, "exit_code": completed.returncode},
        }

    for env_name, kind in config.get("secret-env", {}).items():
        # ADR 0005: the runner injected `resolved:` in memory; hand it to the
        # wrapped process through its environment only — never argv, never disk.
        resolved = request["inputs"].get(kind, {}).get("resolved")
        if resolved is None:
            return {
                "schema": SCHEMA,
                "error": {
                    "message": f"secret-env {env_name}: no resolved plaintext "
                    f"for consumed kind {kind!r}"
                },
            }
        env[env_name] = resolved["value"]
    completed = subprocess.run(
        config["cmd"],
        capture_output=True,
        cwd=workspace,
        env=env,
    )
    if completed.returncode != 0:
        return {
            "schema": SCHEMA,
            "error": {
                "message": f"command exited {completed.returncode}",
                "detail": completed.stderr.decode(errors="replace"),
                "exit_code": completed.returncode,
            },
        }

    if effect == "pure":
        out_dir = workspace / "out"
        entries: dict[str, Any] = {}
        for file in sorted(p for p in out_dir.rglob("*") if p.is_file()):
            # Tree keys are identity: always /-separated, or the same tree
            # would hash to different CIDs per platform.
            entries[file.relative_to(out_dir).as_posix()] = {
                "content": put_blob(ctx.store, file.read_bytes())
            }
        tree_cid = put_doc(ctx.store, tree_doc(entries))
        claim: dict[str, Any] = {
            "schema": SCHEMA,
            "kind": config["kind"],
            "content": tree_cid,
        }
        return {"schema": SCHEMA, "claim": claim}

    claim = {"schema": SCHEMA, "kind": config["kind"], **config.get("claim", {})}
    return {
        "schema": SCHEMA,
        "claim": claim,
        "annotations": {"workspace": str(workspace)},
    }


def _fetch_verify(request: dict[str, Any], ctx: RunContext) -> dict[str, Any]:
    """The only true root (design.md §11): fetch a pinned URL, verify checksum.

    Pure and deliberately NOT a source node: the sha256 pins the world, so
    an unchanged derivation cannot see a changed world — hit-means-current
    stays sound and a current heal fetches nothing.
    """
    import hashlib
    import urllib.error
    import urllib.request

    config = request["node"]["config"]
    url = config["url"]
    expected = config["sha256"]
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
    except (urllib.error.URLError, OSError) as error:
        return {
            "schema": SCHEMA,
            "error": {"message": f"fetch failed: {url}: {error}"},
        }

    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        return {
            "schema": SCHEMA,
            "error": {
                "message": f"checksum mismatch for {url}: "
                f"expected {expected}, got {actual}"
            },
        }

    blob_cid = put_blob(ctx.store, data)
    if config["kind"] == "plugin":
        # The fetching node declares what the plugin is: manifest fields come
        # from node config (M5 — plugins publish as bare executables at
        # pinned URLs; the artifact carries no manifest of its own).
        manifest = config["manifest"]
        claim: dict[str, Any] = {
            "schema": SCHEMA,
            "kind": "plugin",
            "payload": blob_cid,
        }
        for key in (
            "name",
            "version",
            "produces",
            "effect",
            "entrypoint",
            "verify",
            "consumes",
        ):
            if key in manifest:
                claim[key] = manifest[key]
        claim.setdefault("entrypoint", claim.get("name"))
        return {"schema": SCHEMA, "claim": claim}

    return {
        "schema": SCHEMA,
        "claim": {"schema": SCHEMA, "kind": config["kind"], "content": blob_cid},
    }


BUILTINS: dict[str, Builtin] = {
    "import-values": Builtin(
        name="import-values",
        produces="values",
        effect="pure",
        source=True,
        run=_import_values,
    ),
    "import-file-tree": Builtin(
        name="import-file-tree",
        produces="file-tree",
        effect="pure",
        source=True,
        run=_import_file_tree,
    ),
    "import-git": Builtin(
        name="import-git",
        produces="file-tree",
        effect="pure",
        source=True,
        run=_import_git,
    ),
    "import-sops": Builtin(
        name="import-sops",
        produces="secret",
        effect="pure",
        source=True,
        run=_import_sops,
    ),
    "command": Builtin(
        # produces/effect/consumes all node-supplied for the adapter.
        name="command",
        produces=None,
        effect=None,
        run=_command,
    ),
    "fetch-verify": Builtin(
        # kind node-supplied; effect stays pure (design.md §6). Not a source:
        # the checksum pins the world, so cache hits are sound.
        name="fetch-verify",
        produces=None,
        effect="pure",
        run=_fetch_verify,
    ),
}

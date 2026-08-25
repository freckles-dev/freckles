# __init__.py
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

"""Click commands — a thin verb layer over the core modules.

The ratified CLI surface (CLI surface v1, wayfinder ticket 06): the
configuration is the current directory; the per-user store and machine state
live under the data dir — `--data-dir` option over `FRECKLES_DATA_DIR` over
the XDG default. Also here: `--version` and a hidden `selftest` (CI-only —
the frozen-binary organ check from Packaging and distribution).
"""

import os
from pathlib import Path

import click

from freckles._version import version


def _abbrev(cid: object) -> str:
    """Name-first output (R4): CIDs shrink to `bafyre…xxx` wherever a name leads."""
    text = str(cid)
    return f"{text[:6]}…{text[-3:]}" if len(text) > 12 else text


def _resolve_or_die(config_dir: Path, store):
    """Resolve cwd's configuration; a resolution failure is exit 1 (R6)."""
    from freckles.resolver import ResolutionError, resolve

    try:
        return resolve(config_dir, store, version, config_dir.name)
    except ResolutionError as error:
        click.echo(f"error: {error}", err=True)
        raise SystemExit(1) from error


def _run_failed(error) -> SystemExit:
    """A run failure is exit 1 on the surface (R6) — the record is in the audit log."""
    click.echo(f"error: {error}", err=True)
    if error.detail:
        click.echo(error.detail.rstrip(), err=True)
    return SystemExit(1)


def _data_dir() -> Path:
    option = click.get_current_context().find_root().params.get("data_dir")
    if option is not None:
        return option
    env = os.environ.get("FRECKLES_DATA_DIR")
    if env:
        return Path(env)
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "freckles"


@click.group()
@click.version_option(version, prog_name="freckles")
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Store and machine state live here (over FRECKLES_DATA_DIR, over XDG).",
)
def main(data_dir: Path | None) -> None:
    """Turn declarative configuration into running infrastructure."""


@main.command()
@click.option("--yes", is_flag=True, help="Auto-confirm every checkpoint.")
def heal(yes: bool) -> None:
    """Resolve the configuration in the current directory and heal it."""
    from freckles.heal import Checkpoint, heal_rounds
    from freckles.resolver import ResolutionError
    from freckles.runner import RunError

    config_dir = Path.cwd()
    ctx, index = _context(config_dir, _data_dir())

    def confirm(checkpoint: Checkpoint) -> bool:
        click.echo(f"  ▶ {checkpoint.name}  ({checkpoint.op} · {checkpoint.effect})")
        if checkpoint.supersedes is None:
            click.echo(
                f"      creates      {checkpoint.produces}"
                "  (first claim — nothing superseded)"
            )
        else:
            click.echo(f"      supersedes   {_abbrev(checkpoint.supersedes)}")
        if checkpoint.secrets:
            click.echo(
                f"      receives plaintext secrets: {', '.join(checkpoint.secrets)}"
            )
        if checkpoint.prior_available:
            click.echo("      prior        available (claim + annotations)")
        if yes:
            click.echo("      auto-confirmed")
            return True
        return click.confirm("      proceed?", default=False)

    try:
        _, report = heal_rounds(config_dir, config_dir.name, ctx, index, confirm)
    except ResolutionError as error:
        click.echo(f"error: {error}", err=True)
        raise SystemExit(1) from error
    except RunError as error:
        raise _run_failed(error) from error
    for name in report.healed:
        click.echo(f"  {name}  healed")
    if report.deployment_current:
        click.echo("deployment current — checkpoint set empty.")
    else:
        outstanding = [n for n in report.checkpoint_set if n not in report.confirmed]
        click.echo(f"checkpoint set: {', '.join(outstanding)}")
        raise SystemExit(2)


@main.command()
@click.option("--frozen", is_flag=True, help="Report without deriving anything.")
@click.option("--check", is_flag=True, help="Exit code only — 0 current, 2 stale.")
def status(frozen: bool, check: bool) -> None:
    """Report currency: heal stale pures, name the exact checkpoint set (R2)."""
    from freckles.heal import frozen as frozen_walk
    from freckles.heal import heal_rounds
    from freckles.resolver import ResolutionError
    from freckles.runner import RunError

    def echo(message: str) -> None:
        if not check:
            click.echo(message)

    config_dir = Path.cwd()
    ctx, index = _context(config_dir, _data_dir())

    if frozen:
        resolution, _ = _resolve_or_die(config_dir, ctx.store)
        frozen_report = frozen_walk(resolution, config_dir.name, ctx, index)
        if frozen_report.all_current:
            echo(f"{len(resolution.nodes)} nodes, all current — checkpoint set empty.")
            return
        echo(
            f"stale: {', '.join(frozen_report.stale)}"
            "; downstream undetermined until pure heal"
        )
        raise SystemExit(2)

    try:
        resolution, report = heal_rounds(
            config_dir, config_dir.name, ctx, index, lambda _: False
        )
    except ResolutionError as error:
        click.echo(f"error: {error}", err=True)
        raise SystemExit(1) from error
    except RunError as error:
        raise _run_failed(error) from error
    if report.healed:
        echo(f"pure heal: {', '.join(report.healed)}")
    if report.deployment_current:
        echo(f"{len(resolution.nodes)} nodes, all current — checkpoint set empty.")
    else:
        echo(f"checkpoint set: {', '.join(report.checkpoint_set)}")
        raise SystemExit(2)


@main.command()
def resolve() -> None:
    """Plumbing: re-resolve the configuration and print the document's CID."""
    config_dir = Path.cwd()
    ctx, _ = _context(config_dir, _data_dir())
    _, resolution_cid = _resolve_or_die(config_dir, ctx.store)
    click.echo(f"resolution {resolution_cid}")


@main.command()
@click.argument("node")
def show(node: str) -> None:
    """Human view of one node's outcome: claim, annotations, provenance (R7)."""
    from freckles.store import get_doc, provenance_for

    config_dir = Path.cwd()
    ctx, _ = _context(config_dir, _data_dir())
    claim_cid = ctx.store.get_ref(f"cfg/{config_dir.name}/nodes/{node}")
    if claim_cid is None:
        click.echo(f"error: no claim for node {node!r} — not healed yet?", err=True)
        raise SystemExit(1)

    claim = get_doc(ctx.store, claim_cid)
    reason = ctx.annotations.distrusted(claim_cid)
    trust = "trusted" if reason is None else f"distrusted ({reason}) — node stale"
    click.echo(f"{node}   {claim.get('kind', '?')}   {claim_cid}   {trust}")
    click.echo("claim")
    for key, value in claim.items():
        if key != "schema":
            click.echo(f"  {key}: {value}")
    if annotations := ctx.annotations.redacted(claim_cid):
        click.echo("annotations (this machine)")
        for key, value in annotations.items():
            click.echo(f"  {key}: {value}")
    if provenance := provenance_for(ctx.store, claim_cid):
        click.echo(f"provenance    derivation {provenance['derivation']}")


@main.command()
@click.argument("node")
def verify(node: str) -> None:
    """Check a node's claim against the world — explicit, never polled."""
    from freckles.runner import RunError, run_verify
    from freckles.store import get_doc

    config_dir = Path.cwd()
    ctx, _ = _context(config_dir, _data_dir())
    resolution, _ = _resolve_or_die(config_dir, ctx.store)
    resolved = resolution.nodes.get(node)
    if resolved is None:
        click.echo(f"error: unknown node {node!r}", err=True)
        raise SystemExit(1)
    claim_cid = ctx.store.get_ref(f"cfg/{config_dir.name}/nodes/{node}")
    if claim_cid is None:
        click.echo(f"error: no claim for node {node!r} — not healed yet?", err=True)
        raise SystemExit(1)

    claim = get_doc(ctx.store, claim_cid)
    try:
        contradiction = run_verify(
            node, resolved, claim_cid, claim, ctx.annotations.get(claim_cid), ctx
        )
    except RunError as error:
        raise _run_failed(error) from error

    if contradiction is None:
        click.echo(f"  {node}  verify → CONFIRMED")
        return
    ctx.annotations.distrust(claim_cid, contradiction)
    click.echo(f"  {node}  verify → CONTRADICTED ({contradiction})")
    click.echo(f"  claim {_abbrev(claim_cid)} marked distrusted — node stale.")
    raise SystemExit(2)


@main.command()
def gc() -> None:
    """Collect unreferenced store blocks whose grace window has passed."""
    from freckles.defaults import GC_GRACE
    from freckles.store import SqliteStore, extract_links

    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    report = SqliteStore(data_dir / "store.sqlite").gc(extract_links, GC_GRACE)
    click.echo(f"refs: {report.roots} roots · {report.reachable} blocks reachable")
    click.echo(
        f"unreferenced: {report.unreferenced} "
        f"(grace {GC_GRACE.days}d: {report.kept} kept, "
        f"{report.collected} collected)"
    )
    click.echo(f"freed {_human_bytes(report.freed_bytes)}")


def _human_bytes(count: int) -> str:
    if count < 1024:
        return f"{count} B"
    if count < 1 << 20:
        return f"{count / 1024:.1f} KiB"
    return f"{count / (1 << 20):.1f} MiB"


@main.group()
def store() -> None:
    """Raw store access — the machine-facing half of inspection (R7)."""


@store.command("cat")
@click.argument("cid")
def store_cat(cid: str) -> None:
    """Print any store document as raw DAG-JSON."""
    from freckles.documents import Cid, to_wire
    from freckles.store import get_doc

    ctx, _ = _context(Path.cwd(), _data_dir())
    try:
        parsed = Cid.parse(cid)
        document = get_doc(ctx.store, parsed)
    except Exception as error:
        click.echo(f"error: cannot read {cid}: {error}", err=True)
        raise SystemExit(1) from error
    click.echo(to_wire(document))


@main.command(hidden=True)
def selftest() -> None:
    """CI-only: prove the frozen artifact carries its organs (grows per milestone)."""
    import sqlite3
    import urllib.request

    from freckles.documents import cid_for_blob, decode, encode

    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE t (x BLOB)")

    document = {"schema": 1, "kind": "selftest", "content": cid_for_blob(b"organ")}
    data, cid = encode(document)
    assert decode(data) == document, "codec round-trip failed"
    assert str(cid).startswith("bafyrei"), "CID form wrong"
    assert callable(urllib.request.urlopen), "urllib organ missing"  # fetch-verify

    click.echo("selftest ok: sqlite3, libipld codec, CIDv1, urllib")


def _context(config_dir: Path, data_dir: Path):
    from freckles.runner import RunContext
    from freckles.state import AnnotationsIndex, AuditLog, DerivationIndex, StateDb
    from freckles.store import SqliteStore

    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "run").mkdir(exist_ok=True)
    store = SqliteStore(data_dir / "store.sqlite")
    db = StateDb(data_dir / "state.sqlite")
    ctx = RunContext(
        store=store,
        annotations=AnnotationsIndex(db),
        config_dir=config_dir,
        freckles_version=version,
        workspace_root=data_dir / "run",
        envs_root=data_dir / "envs",
        audit=AuditLog(data_dir / "audit.jsonl"),
    )
    return ctx, DerivationIndex(db)

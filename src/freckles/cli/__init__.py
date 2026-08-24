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


def _data_dir() -> Path:
    env = os.environ.get("FRECKLES_DATA_DIR")
    if env:
        return Path(env)
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / "freckles"


@click.group()
@click.version_option(version, prog_name="freckles")
def main() -> None:
    """Turn declarative configuration into running infrastructure."""


@main.command()
@click.option("--yes", is_flag=True, help="Auto-confirm every checkpoint.")
def heal(yes: bool) -> None:
    """Resolve the configuration in the current directory and heal it."""
    from freckles.heal import Checkpoint
    from freckles.heal import heal as heal_walk
    from freckles.resolver import resolve

    config_dir = Path.cwd()
    ctx, index = _context(config_dir, _data_dir())
    resolution, _ = resolve(config_dir, ctx.store, version, config_dir.name)

    def confirm(checkpoint: Checkpoint) -> bool:
        click.echo(f"  ▶ {checkpoint.name}  ({checkpoint.op} · {checkpoint.effect})")
        if checkpoint.supersedes is None:
            click.echo(
                f"      creates      {checkpoint.produces}"
                "  (first claim — nothing superseded)"
            )
        else:
            click.echo(f"      supersedes   {_abbrev(checkpoint.supersedes)}")
        if checkpoint.prior_available:
            click.echo("      prior        available (claim + annotations)")
        if yes:
            click.echo("      auto-confirmed")
            return True
        return click.confirm("      proceed?", default=False)

    report = heal_walk(resolution, config_dir.name, ctx, index, confirm)
    for name in report.healed:
        click.echo(f"  {name}  healed")
    if report.deployment_current:
        click.echo("deployment current — checkpoint set empty.")
    else:
        outstanding = [n for n in report.checkpoint_set if n not in report.confirmed]
        click.echo(f"checkpoint set: {', '.join(outstanding)}")
        raise SystemExit(2)


@main.command(hidden=True)
def selftest() -> None:
    """CI-only: prove the frozen artifact carries its organs (grows per milestone)."""
    import sqlite3

    from freckles.documents import cid_for_blob, decode, encode

    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE t (x BLOB)")

    document = {"schema": 1, "kind": "selftest", "content": cid_for_blob(b"organ")}
    data, cid = encode(document)
    assert decode(data) == document, "codec round-trip failed"
    assert str(cid).startswith("bafyrei"), "CID form wrong"

    click.echo("selftest ok: sqlite3, libipld codec, CIDv1")


@main.group(hidden=True)
def dev() -> None:
    """Raw development commands for the walking skeleton."""


def _context(config_dir: Path, data_dir: Path):
    from freckles.runner import RunContext
    from freckles.state import AnnotationsIndex, DerivationIndex, StateDb
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
    )
    return ctx, DerivationIndex(db)


@dev.command("resolve")
@click.argument("config_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--data-dir", type=click.Path(path_type=Path), default=Path(".freckles-dev")
)
def dev_resolve(config_dir: Path, data_dir: Path) -> None:
    """Resolve CONFIG_DIR and print the resolution document CID."""
    from freckles.resolver import resolve

    ctx, _ = _context(config_dir, data_dir)
    resolution, cid = resolve(config_dir, ctx.store, version, config_dir.name)
    click.echo(f"resolution {cid}")
    for name, node in resolution.nodes.items():
        edges = ", ".join(f"{k}<-{v}" for k, v in node.consumes.items()) or "-"
        click.echo(f"  {name}  [{node.effect}] produces {node.produces}  {edges}")


@dev.command("heal")
@click.argument("config_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--data-dir", type=click.Path(path_type=Path), default=Path(".freckles-dev")
)
@click.option("--yes", is_flag=True, help="Auto-confirm every checkpoint.")
def dev_heal(config_dir: Path, data_dir: Path, yes: bool) -> None:
    """Resolve CONFIG_DIR, then heal: day-1 = day-2 from zero."""
    from freckles.heal import heal
    from freckles.resolver import resolve

    ctx, index = _context(config_dir, data_dir)
    resolution, _ = resolve(config_dir, ctx.store, version, config_dir.name)

    def confirm(checkpoint) -> bool:
        if yes:
            click.echo(f"checkpoint {checkpoint.name}: auto-confirmed")
            return True
        return click.confirm(f"checkpoint {checkpoint.name}: run it?")

    report = heal(resolution, config_dir.name, ctx, index, confirm)
    for label, nodes in (
        ("current", report.current),
        ("healed", report.healed),
        ("confirmed", report.confirmed),
        ("hidden", report.hidden),
    ):
        if nodes:
            click.echo(f"{label}: {', '.join(nodes)}")
    outstanding = [n for n in report.checkpoint_set if n not in report.confirmed]
    if outstanding:
        click.echo(f"checkpoint set: {', '.join(outstanding)}")
    click.echo(
        "deployment current" if report.deployment_current else "deployment NOT current"
    )

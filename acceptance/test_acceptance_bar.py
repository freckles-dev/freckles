"""The v1 acceptance bar, executed (docs/milestones-v1.md, the gate M9 builds).

One story against real upstreams: day-1 heal from zero through the mise
route (real mise, uv, copier via mise's pipx backend, the R3 checkpoint
prompt), full currency, the day-2 values ripple, drift caught by verify
and healed, then the bootstrap swap to the pixi route (real pixi, copier
through the locked conda-forge workspace) with the extensional
ripple-stop — the downstream consumers never re-run, no checkpoint opens.
"""

from chains import MISE_VERSION, PIXI_VERSION


def test_the_acceptance_bar(acceptance_world):
    world = acceptance_world

    # --- day 1, mise route: one heal from zero, the checkpoint prompted (R3)
    result = world.freckles("heal", input="y\n")
    assert result.returncode == 0, result.stdout + result.stderr
    assert world.healed(result) == {
        "plugins/bootstrap-mise",
        "plugins/mise-install",
        "bootstrap",
        "tools/uv",  # mise's pipx backend rides its own DAG-installed uv
        "tools/copier",
        "values/apps",
        "secrets/deploy-token",
        "render/site",
    }, result.stdout
    # the checkpoint is confirmed through its ▶ block, never a healed line
    assert "▶ deploy/site" in result.stdout
    assert "proceed?" in result.stdout
    assert "receives plaintext secrets: deploy-token" in result.stdout
    assert "checkpoint set empty" in result.stdout
    mise_binary = world.data_dir / "envs" / "mise" / MISE_VERSION / "bin" / "mise"
    assert mise_binary.exists()
    assert mise_binary.stat().st_size > 1_000_000  # the real static binary
    assert (world.state_dir / "deployed").exists()

    # --- fully current: nothing re-heals, no checkpoint opens, status agrees
    result = world.freckles("heal")
    assert result.returncode == 0, result.stdout + result.stderr
    assert world.healed(result) == set(), result.stdout
    assert "▶" not in result.stdout
    assert world.freckles("status").returncode == 0

    # --- day 2: the values edit ripples to exactly its consumers + checkpoint
    world.edit_values()
    status = world.freckles("status")
    assert status.returncode == 2, status.stdout + status.stderr
    assert "deploy/site" in status.stdout
    result = world.freckles("heal", input="y\n")
    assert result.returncode == 0, result.stdout + result.stderr
    # the preceding status already healed the pure ripple — that is how it
    # names the exact checkpoint set (R2) — so heal holds only the checkpoint
    assert world.healed(result) == set(), result.stdout
    assert "supersedes" in result.stdout  # the re-run names the old claim (R3)
    assert "prior" in result.stdout  # and offers prior:
    assert world.freckles("status").returncode == 0

    # --- drift: the world regresses; verify contradicts; heal restores trust
    (world.state_dir / "deployed").unlink()
    verify = world.freckles("verify", "deploy/site")
    assert verify.returncode == 2, verify.stdout + verify.stderr
    assert "CONTRADICTED" in verify.stdout
    assert world.freckles("status").returncode == 2
    result = world.freckles("heal", "--yes")
    assert result.returncode == 0, result.stdout + result.stderr
    assert (world.state_dir / "deployed").exists()  # the re-run redeployed
    assert world.freckles("verify", "deploy/site").returncode == 0

    # --- the swap: same store, pixi route; the tool re-derives byte-identical,
    # so the downstream consumers see the same input CID and never re-run
    world.write_pixi_chain()
    result = world.freckles("heal", "--yes")
    assert result.returncode == 0, result.stdout + result.stderr
    assert world.healed(result) == {
        "plugins/bootstrap-pixi",
        "plugins/pixi-install",
        "bootstrap",
        "tools/copier",
    }, result.stdout
    assert "▶" not in result.stdout  # the ripple stops: no checkpoint opens (§10)
    pixi_binary = world.data_dir / "envs" / "pixi" / PIXI_VERSION / "bin" / "pixi"
    assert pixi_binary.exists()
    assert pixi_binary.stat().st_size > 10_000_000

    # --- and the swapped world is current
    assert world.freckles("status").returncode == 0

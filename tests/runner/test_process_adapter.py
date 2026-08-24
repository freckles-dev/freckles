"""The process adapter: spawned fake plugins, the purity split, the misbehavior battery."""

import os

import pytest

from freckles.documents import ResolvedNode
from freckles.runner import RunError, run_node

ECHO_PLUGIN = """
import json, os, sys
request = json.load(sys.stdin)
json.dump({
    "schema": 1,
    "claim": {
        "schema": 1,
        "kind": "echo",
        "node": request["node"]["name"],
        "env": dict(sorted(os.environ.items())),
        "cwd": os.getcwd(),
        "got_prior": "prior" in request,
    },
}, sys.stdout)
"""


def resolved(plugin_cid, produces="echo", effect="pure", config=None):
    return ResolvedNode(
        plugin=plugin_cid,
        produces=produces,
        effect=effect,
        config=config or {},
        consumes={},
    )


def test_spawned_plugin_speaks_the_wire(ctx, make_plugin):
    plugin = make_plugin("echo", ECHO_PLUGIN, produces="echo")
    outcome = run_node("demo/echo", resolved(plugin), {}, ctx)
    assert outcome.claim["kind"] == "echo"
    assert outcome.claim["node"] == "demo/echo"


def test_environment_is_scrubbed(ctx, make_plugin, monkeypatch):
    monkeypatch.setenv("SECRET_CANARY", "leak-me-if-you-can")
    plugin = make_plugin("echo", ECHO_PLUGIN, produces="echo")
    outcome = run_node("demo/echo", resolved(plugin), {}, ctx)
    child_env = outcome.claim["env"]
    assert "SECRET_CANARY" not in child_env
    assert set(child_env) == {"PATH", "HOME", "TMPDIR", "LANG"}
    assert child_env["HOME"].endswith("/home")


def test_workspace_is_isolated_and_cwd(ctx, make_plugin):
    plugin = make_plugin("echo", ECHO_PLUGIN, produces="echo")
    outcome = run_node("demo/echo", resolved(plugin), {}, ctx)
    assert outcome.claim["cwd"].startswith(str(ctx.workspace_root))
    assert os.path.isdir(outcome.claim["cwd"])


def test_pure_run_never_carries_prior(ctx, make_plugin):
    plugin = make_plugin("echo", ECHO_PLUGIN, produces="echo")
    prior = {"cid": "unused", "claim": {"schema": 1, "kind": "echo"}}
    outcome = run_node("demo/echo", resolved(plugin), {}, ctx, prior=prior)
    assert outcome.claim["got_prior"] is False


def test_effectful_run_receives_prior(ctx, make_plugin):
    plugin = make_plugin("echo", ECHO_PLUGIN, produces="echo", effect="effectful")
    prior = {"cid": "unused", "claim": {"schema": 1, "kind": "echo"}}
    outcome = run_node(
        "demo/echo", resolved(plugin, effect="effectful"), {}, ctx, prior=prior
    )
    assert outcome.claim["got_prior"] is True


# --- the misbehavior battery -------------------------------------------------

GARBAGE_PLUGIN = 'print("this is not a wire document")'

ERROR_PLUGIN = """
import json, sys
json.dump({"schema": 1, "error": {"message": "disk on fire", "detail": "smoke"}}, sys.stdout)
sys.exit(3)
"""

SILENT_FAILURE_PLUGIN = "import sys; sys.exit(9)"

WRONG_KIND_PLUGIN = """
import json, sys
json.dump({"schema": 1, "claim": {"schema": 1, "kind": "impostor"}}, sys.stdout)
"""


def test_garbage_stdout_is_a_run_error(ctx, make_plugin):
    plugin = make_plugin("garbage", GARBAGE_PLUGIN)
    with pytest.raises(RunError, match="malformed|not an outcome"):
        run_node("demo/garbage", resolved(plugin, produces="thing"), {}, ctx)


def test_structured_error_surfaces_message(ctx, make_plugin):
    plugin = make_plugin("failing", ERROR_PLUGIN)
    with pytest.raises(RunError, match="disk on fire"):
        run_node("demo/fail", resolved(plugin, produces="thing"), {}, ctx)


def test_nonzero_exit_without_error_document(ctx, make_plugin):
    plugin = make_plugin("silent", SILENT_FAILURE_PLUGIN)
    with pytest.raises(RunError, match="exited 9"):
        run_node("demo/silent", resolved(plugin, produces="thing"), {}, ctx)


def test_claim_kind_must_match_resolved_produces(ctx, make_plugin):
    plugin = make_plugin("impostor", WRONG_KIND_PLUGIN)
    with pytest.raises(RunError, match="does not match resolved produced kind"):
        run_node("demo/impostor", resolved(plugin, produces="thing"), {}, ctx)

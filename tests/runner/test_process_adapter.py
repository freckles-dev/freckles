"""The process adapter: spawned fake plugins, the purity split, the misbehavior battery."""

import os

import pytest

from freckles.documents import ResolvedNode
from freckles.runner import RunError, run_node, run_verify
from freckles.store import put_doc

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
    # The runner constructs exactly these four; nothing from the calling
    # environment may leak. No exact-set assertion on purpose: on darwin the
    # /usr/bin/env python3 shim injects toolchain vars (CPATH, SDKROOT, …)
    # into the child after the scrub — outside the runner's control.
    assert "SECRET_CANARY" not in child_env
    assert {"PATH", "HOME", "TMPDIR", "LANG"} <= set(child_env)
    # Native separator: the workspace HOME is a real local path, not identity.
    assert child_env["HOME"].endswith(("/home", "\\home"))


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


VERIFY_PLUGIN = """
import json, sys
request = json.load(sys.stdin)
claim = request["verify"]["claim"]
if claim.get("kind") == "deployed-site":
    sys.exit(0)          # CONFIRMED -- silence is part of the contract
print("claim drifted", file=sys.stderr)
sys.exit(9)
"""


def test_spawned_verify_confirms_by_exit_0_with_silent_stdout(ctx, make_plugin):
    plugin = make_plugin(
        "checker",
        VERIFY_PLUGIN,
        produces="deployed-site",
        effect="effectful",
        verify=True,
    )
    node = resolved(plugin, produces="deployed-site", effect="effectful")
    claim = {"schema": 1, "kind": "deployed-site"}
    claim_cid = put_doc(ctx.store, claim)

    assert run_verify("demo/site", node, claim_cid, claim, {}, ctx) is None


def test_spawned_verify_contradicts_by_nonzero_with_stderr_message(ctx, make_plugin):
    plugin = make_plugin(
        "checker",
        VERIFY_PLUGIN,
        produces="deployed-site",
        effect="effectful",
        verify=True,
    )
    node = resolved(plugin, produces="deployed-site", effect="effectful")
    claim = {"schema": 1, "kind": "something-else"}
    claim_cid = put_doc(ctx.store, claim)

    message = run_verify("demo/site", node, claim_cid, claim, {}, ctx)

    assert message == "claim drifted"


def test_spawned_verify_requires_the_manifest_entrypoint(ctx, make_plugin):
    plugin = make_plugin(
        "mute", VERIFY_PLUGIN, produces="deployed-site", effect="effectful"
    )
    node = resolved(plugin, produces="deployed-site", effect="effectful")
    claim = {"schema": 1, "kind": "deployed-site"}
    claim_cid = put_doc(ctx.store, claim)

    with pytest.raises(RunError, match="no verify entrypoint"):
        run_verify("demo/site", node, claim_cid, claim, {}, ctx)

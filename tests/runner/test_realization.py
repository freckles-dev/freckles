"""The realization root and the constructed PATH (design.md §6, M6).

Realized environments live outside the CAS and outside the ephemeral
workspace: the request's workspace section names `envs`, a persistent
machine-local root plugins install under. Consumed `bootstrap`/`tool`
claims contribute their realized paths to the constructed PATH.
"""

from freckles.runner import run_node
from freckles.runner.run import build_request

ENVS_PLUGIN = """
import json, os, sys
request = json.load(sys.stdin)
envs = request["workspace"]["envs"]
with open(os.path.join(envs, "marker.txt"), "w") as f:
    f.write("realized")
json.dump({"schema": 1,
           "claim": {"schema": 1, "kind": "envy", "envs": envs}}, sys.stdout)
"""


def _resolved(plugin_cid, produces="envy"):
    from freckles.documents import ResolvedNode

    return ResolvedNode(
        plugin=plugin_cid, produces=produces, effect="pure", config={}, consumes={}
    )


def test_workspace_envs_names_the_persistent_realization_root(ctx, make_plugin):
    plugin = make_plugin("envy", ENVS_PLUGIN, produces="envy")

    outcome = run_node("demo/envs", _resolved(plugin), {}, ctx)

    assert outcome.claim["envs"] == str(ctx.envs_root)
    # What the plugin realized under envs outlives its workspace.
    assert (ctx.envs_root / "marker.txt").read_text() == "realized"
    assert not str(ctx.envs_root).startswith(str(ctx.workspace_root))


def test_request_document_carries_envs(ctx):
    from freckles.documents import ResolvedNode

    node = ResolvedNode(
        plugin={"builtin": "command", "freckles": "0.0.0-test"},
        produces="thing",
        effect="pure",
        config={},
        consumes={},
    )

    request = build_request(
        "demo/doc", node, {}, "/ws", ["/usr/bin"], None, envs="/data/envs"
    )

    assert request["workspace"] == {
        "dir": "/ws",
        "path": ["/usr/bin"],
        "envs": "/data/envs",
    }


# --- the constructed PATH (design.md §6): consumed bootstrap/tool claims ----

PATH_ECHO_PLUGIN = """
import json, os, sys
request = json.load(sys.stdin)
json.dump({"schema": 1,
           "claim": {"schema": 1, "kind": "echo",
                     "request_path": request["workspace"]["path"],
                     "env_path": os.environ["PATH"]}}, sys.stdout)
"""

BASELINE = ["/usr/bin", "/bin"]


def realized(kind, name, binary):
    """A consumed claim of `kind` realized at `binary` (path annotation)."""
    return {
        "cid": "bafyre-test",
        "claim": {"schema": 1, "kind": kind, "tool": name, "version": "1.0.0"},
        "annotations": {"path": str(binary)},
    }


def test_consumed_tool_claim_lands_on_the_constructed_path(ctx, make_plugin, tmp_path):
    plugin = make_plugin("echo", PATH_ECHO_PLUGIN, produces="echo")
    tofu = tmp_path / "envs" / "opentofu" / "bin" / "tofu"
    inputs = {"tool": realized("tool", "opentofu", tofu)}

    outcome = run_node("infra/plan", _resolved(plugin, produces="echo"), inputs, ctx)

    assert outcome.claim["request_path"] == [str(tofu.parent), *BASELINE]
    assert outcome.claim["env_path"].startswith(str(tofu.parent) + ":")


def test_bootstrap_and_tool_dirs_precede_the_baseline(ctx, make_plugin, tmp_path):
    plugin = make_plugin("echo", PATH_ECHO_PLUGIN, produces="echo")
    mise = tmp_path / "envs" / "mise" / "bin" / "mise"
    tofu = tmp_path / "envs" / "opentofu" / "bin" / "tofu"
    inputs = {
        "tool": realized("tool", "opentofu", tofu),
        "bootstrap": realized("bootstrap", "mise", mise),
    }

    outcome = run_node("infra/plan", _resolved(plugin, produces="echo"), inputs, ctx)

    # Deterministic order: sorted by consumed kind, then the baseline.
    assert outcome.claim["request_path"] == [
        str(mise.parent),
        str(tofu.parent),
        *BASELINE,
    ]


def test_non_tool_claims_never_touch_the_path(ctx, make_plugin, tmp_path):
    plugin = make_plugin("echo", PATH_ECHO_PLUGIN, produces="echo")
    inputs = {
        "values": {
            "cid": "bafyre-test",
            "claim": {"schema": 1, "kind": "values"},
            "annotations": {"path": str(tmp_path / "sneaky" / "bin" / "x")},
        }
    }

    outcome = run_node("render/site", _resolved(plugin, produces="echo"), inputs, ctx)

    assert outcome.claim["request_path"] == BASELINE


def test_unrealized_tool_claim_is_a_hard_run_error(ctx, make_plugin):
    import pytest

    from freckles.runner import RunError

    plugin = make_plugin("echo", PATH_ECHO_PLUGIN, produces="echo")
    inputs = {
        "tool": {
            "cid": "bafyre-test",
            "claim": {"schema": 1, "kind": "tool", "tool": "opentofu"},
        }
    }

    with pytest.raises(RunError, match="not realized"):
        run_node("infra/plan", _resolved(plugin, produces="echo"), inputs, ctx)

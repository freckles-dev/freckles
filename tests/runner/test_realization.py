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

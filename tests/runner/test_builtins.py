"""The in-process adapter: import-values and the command adapter (wrapped subprocess)."""

import pytest

from freckles.documents import ResolvedNode
from freckles.runner import RunError, run_node
from freckles.store import get_doc

IMPORT_VALUES = {"builtin": "import-values", "freckles": "0.0.0-test"}
COMMAND = {"builtin": "command", "freckles": "0.0.0-test"}


def test_import_values_selects_one_key(ctx):
    (ctx.config_dir / "cluster.yaml").write_text(
        "apps:\n  karakeep:\n    enabled: true\ncluster:\n  name: staging\n"
    )
    node = ResolvedNode(
        plugin=IMPORT_VALUES,
        produces="values",
        effect="pure",
        config={"file": "cluster.yaml", "key": "apps"},
        consumes={},
    )
    outcome = run_node("values/apps", node, {}, ctx)
    assert outcome.claim["kind"] == "values"
    assert outcome.claim["key"] == "apps"
    content = ctx.store.get(outcome.claim["content"]).decode()
    assert "karakeep" in content
    assert "staging" not in content  # granularity: only the selected key


def test_import_values_is_deterministic(ctx):
    """The run-twice determinism harness ("Testing strategy"), applied."""
    (ctx.config_dir / "v.yaml").write_text("apps: {a: 1}\n")
    node = ResolvedNode(
        plugin=IMPORT_VALUES,
        produces="values",
        effect="pure",
        config={"file": "v.yaml", "key": "apps"},
        consumes={},
    )
    first = run_node("values/apps", node, {}, ctx)
    second = run_node("values/apps", node, {}, ctx)
    assert first.claim == second.claim


def test_pure_command_ingests_out_tree(ctx, encode_checked):
    node = ResolvedNode(
        plugin=COMMAND,
        produces="file-tree",
        effect="pure",
        config={
            "kind": "file-tree",
            "effect": "pure",
            "cmd": [
                "sh",
                "-c",
                "mkdir -p out/site && echo rendered > out/site/index.html",
            ],
        },
        consumes={},
    )
    outcome = run_node("render/site", node, {}, ctx)
    assert outcome.claim["kind"] == "file-tree"
    tree = get_doc(ctx.store, outcome.claim["content"])
    assert list(tree["entries"]) == ["site/index.html"]
    blob = ctx.store.get(tree["entries"]["site/index.html"]["content"])
    assert blob == b"rendered\n"
    encode_checked(outcome.claim)  # the minted claim encodes identically in both


def test_pure_command_is_deterministic(ctx):
    node = ResolvedNode(
        plugin=COMMAND,
        produces="file-tree",
        effect="pure",
        config={
            "kind": "file-tree",
            "effect": "pure",
            "cmd": ["sh", "-c", "echo stable > out/f"],
        },
        consumes={},
    )
    assert run_node("n", node, {}, ctx).claim == run_node("n", node, {}, ctx).claim


def test_effectful_command_claims_and_annotates(ctx):
    node = ResolvedNode(
        plugin=COMMAND,
        produces="deployed-site",
        effect="effectful",
        config={
            "kind": "deployed-site",
            "effect": "effectful",
            "cmd": ["sh", "-c", "true"],
            "claim": {"site": "demo"},
        },
        consumes={},
    )
    outcome = run_node("deploy/site", node, {}, ctx)
    assert outcome.claim == {"schema": 1, "kind": "deployed-site", "site": "demo"}
    assert outcome.annotations["workspace"].startswith(str(ctx.workspace_root))


def test_effectful_command_sees_prior_as_file(ctx):
    node = ResolvedNode(
        plugin=COMMAND,
        produces="deployed-site",
        effect="effectful",
        config={
            "kind": "deployed-site",
            "effect": "effectful",
            # The wrapped command proves it saw prior.json by requiring it.
            "cmd": ["sh", "-c", "test -f prior.json"],
            "claim": {"site": "demo"},
        },
        consumes={},
    )
    with pytest.raises(RunError, match="exited 1"):
        run_node("deploy/site", node, {}, ctx)  # first run: no prior, test -f fails

    prior = {"cid": "x", "claim": {"schema": 1, "kind": "deployed-site"}}
    outcome = run_node("deploy/site", node, {}, ctx, prior=prior)
    assert outcome.claim["site"] == "demo"


def test_failing_command_is_a_structured_error(ctx):
    node = ResolvedNode(
        plugin=COMMAND,
        produces="x",
        effect="pure",
        config={
            "kind": "x",
            "effect": "pure",
            "cmd": ["sh", "-c", "echo doom >&2; exit 7"],
        },
        consumes={},
    )
    with pytest.raises(RunError, match="exited 7") as excinfo:
        run_node("n", node, {}, ctx)
    assert "doom" in excinfo.value.detail

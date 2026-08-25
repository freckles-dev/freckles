"""import-file-tree: a working-copy directory becomes a file-tree claim (M8)."""

import pytest

from freckles.documents import ResolvedNode
from freckles.runner import RunError, run_node
from freckles.store import get_doc

IMPORT_FILE_TREE = {"builtin": "import-file-tree", "freckles": "0.0.0-test"}


def tree_node(config):
    return ResolvedNode(
        plugin=IMPORT_FILE_TREE,
        produces="file-tree",
        effect="pure",
        config=config,
        consumes={},
    )


@pytest.fixture
def site(ctx):
    source = ctx.config_dir / "site"
    (source / "sub").mkdir(parents=True)
    (source / "index.html").write_text("<h1>hi</h1>")
    script = source / "sub" / "deploy.sh"
    script.write_text("#!/bin/sh\n")
    script.chmod(0o755)
    return source


def test_directory_becomes_a_file_tree_claim(ctx, site):
    outcome = run_node("sources/site", tree_node({"dir": "site"}), {}, ctx)

    claim = outcome.claim
    assert claim["kind"] == "file-tree"
    tree = get_doc(ctx.store, claim["content"])
    assert set(tree["entries"]) == {"index.html", "sub/deploy.sh"}  # /-separated
    blob = ctx.store.get(tree["entries"]["index.html"]["content"])
    assert blob == b"<h1>hi</h1>"


def test_exec_bits_survive_the_import(ctx, site):
    outcome = run_node("sources/site", tree_node({"dir": "site"}), {}, ctx)

    tree = get_doc(ctx.store, outcome.claim["content"])
    assert tree["entries"]["sub/deploy.sh"].get("exec") is True
    assert "exec" not in tree["entries"]["index.html"]


def test_unchanged_directory_remints_the_byte_identical_claim(
    ctx, site, encode_checked
):
    """Source-rerun doctrine: the ripple stops on an unchanged import."""
    first = run_node("sources/site", tree_node({"dir": "site"}), {}, ctx)
    second = run_node("sources/site", tree_node({"dir": "site"}), {}, ctx)

    assert encode_checked(first.claim) == encode_checked(second.claim)


def test_missing_directory_fails_cleanly(ctx):
    with pytest.raises(RunError, match="site"):
        run_node("sources/site", tree_node({"dir": "site"}), {}, ctx)


def test_escaping_the_working_copy_is_an_error(ctx):
    with pytest.raises(RunError, match="escapes the configuration"):
        run_node("sources/site", tree_node({"dir": "../elsewhere"}), {}, ctx)

"""import-git: a repository at a resolved commit becomes a file-tree claim (M8).

The fetch is embedded (dulwich) — no host git, per the design.md §6 tier
argument. The claim pins the resolved commit beside the tree (design.md
§12: "pinned by resolved commit in the claim"); the URL stays out of
identity — the same commit from any remote is the same import.
"""

import pytest

from freckles.documents import ResolvedNode
from freckles.runner import RunError, run_node
from freckles.store import get_doc

IMPORT_GIT = {"builtin": "import-git", "freckles": "0.0.0-test"}


def git_node(config):
    return ResolvedNode(
        plugin=IMPORT_GIT,
        produces="file-tree",
        effect="pure",
        config=config,
        consumes={},
    )


def test_branch_ref_imports_the_tree_and_pins_the_commit(ctx, git_lab):
    repo = git_lab(
        {"README.md": "hello", "bin/run.sh": "#!/bin/sh\n"},
        exec_paths=("bin/run.sh",),
    )

    outcome = run_node(
        "sources/repo", git_node({"url": repo.url, "ref": "main"}), {}, ctx
    )

    claim = outcome.claim
    assert claim["kind"] == "file-tree"
    assert claim["commit"] == repo.head
    tree = get_doc(ctx.store, claim["content"])
    assert set(tree["entries"]) == {"README.md", "bin/run.sh"}
    assert ctx.store.get(tree["entries"]["README.md"]["content"]) == b"hello"
    assert tree["entries"]["bin/run.sh"].get("exec") is True


def test_pinned_commit_stays_put_when_the_branch_moves(ctx, git_lab):
    repo = git_lab({"config.yaml": "v: 1\n"})
    pinned = repo.head
    repo.commit({"config.yaml": "v: 2\n"})

    outcome = run_node(
        "sources/repo", git_node({"url": repo.url, "commit": pinned}), {}, ctx
    )

    assert outcome.claim["commit"] == pinned
    tree = get_doc(ctx.store, outcome.claim["content"])
    assert ctx.store.get(tree["entries"]["config.yaml"]["content"]) == b"v: 1\n"


def test_a_branch_ref_resolves_anew_each_import(ctx, git_lab):
    """Source semantics: a branch ref re-resolves at every import.

    Staleness rides the claim change — no ref-watching machinery exists.
    """
    repo = git_lab({"config.yaml": "v: 1\n"})
    node = git_node({"url": repo.url, "ref": "main"})
    first = run_node("sources/repo", node, {}, ctx)

    repo.commit({"config.yaml": "v: 2\n"})
    second = run_node("sources/repo", node, {}, ctx)

    assert first.claim["commit"] != second.claim["commit"]
    assert second.claim["commit"] == repo.head


def test_default_ref_is_head(ctx, git_lab):
    repo = git_lab({"README.md": "hi"})

    outcome = run_node("sources/repo", git_node({"url": repo.url}), {}, ctx)

    assert outcome.claim["commit"] == repo.head


def test_reimport_of_a_pinned_commit_is_byte_identical(ctx, git_lab, encode_checked):
    repo = git_lab({"README.md": "hi"})
    node = git_node({"url": repo.url, "commit": repo.head})

    first = run_node("sources/repo", node, {}, ctx)
    second = run_node("sources/repo", node, {}, ctx)

    assert encode_checked(first.claim) == encode_checked(second.claim)


def test_unknown_ref_fails_cleanly(ctx, git_lab):
    repo = git_lab({"README.md": "hi"})

    with pytest.raises(RunError, match="ref 'release' not found"):
        run_node("sources/repo", git_node({"url": repo.url, "ref": "release"}), {}, ctx)


def test_unreachable_repository_fails_cleanly(ctx, tmp_path):
    nowhere = str(tmp_path / "no-such-repo")

    with pytest.raises(RunError, match="fetch failed"):
        run_node("sources/repo", git_node({"url": nowhere}), {}, ctx)

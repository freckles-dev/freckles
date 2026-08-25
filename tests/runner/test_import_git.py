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


# --- HTTPS-token: the first transport (M8) ----------------------------------

LAB_TOKEN = "s3cr3t-git-t0k3n"


@pytest.fixture
def http_git_lab(git_lab, monkeypatch):
    """The git lab behind smart HTTP, requiring basic auth `token:<token>`."""
    import base64
    import threading
    from wsgiref.simple_server import WSGIRequestHandler, make_server

    from dulwich.repo import Repo
    from dulwich.server import DictBackend
    from dulwich.web import make_wsgi_chain

    lab_repo = git_lab({"app.yaml": "a: 1\n"})
    opened = Repo(str(lab_repo.path))
    smart_http = make_wsgi_chain(DictBackend({b"/": opened}))
    expected = "Basic " + base64.b64encode(f"token:{LAB_TOKEN}".encode()).decode()

    def guarded(environ, start_response):
        if environ.get("HTTP_AUTHORIZATION") != expected:
            start_response("401 Unauthorized", [("WWW-Authenticate", "Basic")])
            return [b"auth required"]
        return smart_http(environ, start_response)

    class Quiet(WSGIRequestHandler):
        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            pass

    server = make_server("127.0.0.1", 0, guarded, handler_class=Quiet)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("LAB_GIT_TOKEN", LAB_TOKEN)
    yield f"http://127.0.0.1:{server.server_port}/", lab_repo
    server.shutdown()
    opened.close()


def test_token_env_authenticates_the_fetch(ctx, http_git_lab):
    url, lab_repo = http_git_lab

    outcome = run_node(
        "sources/repo",
        git_node({"url": url, "ref": "main", "token_env": "LAB_GIT_TOKEN"}),
        {},
        ctx,
    )

    assert outcome.claim["commit"] == lab_repo.head
    # The token itself never enters any document — only the env var's NAME
    # is config (and therefore hashed identity).
    from freckles.documents import to_wire

    assert LAB_TOKEN not in to_wire(outcome.claim)


def test_missing_token_is_denied_cleanly(ctx, http_git_lab):
    url, _ = http_git_lab

    with pytest.raises(RunError, match="fetch failed"):
        run_node("sources/repo", git_node({"url": url, "ref": "main"}), {}, ctx)


def test_unset_token_env_names_the_variable(ctx, http_git_lab):
    url, _ = http_git_lab

    with pytest.raises(RunError, match="NO_SUCH_TOKEN_VAR"):
        run_node(
            "sources/repo",
            git_node({"url": url, "token_env": "NO_SUCH_TOKEN_VAR"}),
            {},
            ctx,
        )

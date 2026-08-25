"""The release pipeline's plugin publishing: plugins/ → bare payload artifacts.

M9: standard plugins publish as bare executables at pinned URLs
(design.md §6), fetched by fetch-verify against a checksum — so the
payload bytes must be deterministic (a pinned checksum breaks on
rebuild otherwise), and the artifact set is exactly the v1 cut's four
standard plugins, versioned with the freckles release they ship beside.
"""

import ast
import subprocess
import sys
from pathlib import Path

from freckles._version import version

SCRIPT = Path(__file__).parent.parent.parent / "scripts" / "build_plugin_payloads.py"


def publish(out_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(out_dir)],
        capture_output=True,
        text=True,
    )


def imported_roots(source: str) -> set[str]:
    roots = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_publishes_exactly_the_four_standard_plugins(tmp_path):
    completed = publish(tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert {p.name for p in tmp_path.iterdir()} == {
        f"bootstrap-mise-{version}",
        f"bootstrap-pixi-{version}",
        f"mise-install-{version}",
        f"pixi-install-{version}",
    }


def test_payloads_are_standalone_stdlib_executables(tmp_path):
    completed = publish(tmp_path)

    assert completed.returncode == 0, completed.stderr
    for payload in tmp_path.iterdir():
        source = payload.read_text()
        assert source.startswith("#!/usr/bin/env python3"), payload.name
        assert imported_roots(source) <= set(sys.stdlib_module_names), payload.name
        assert payload.stat().st_mode & 0o111, f"{payload.name} is not executable"


def test_payload_bytes_are_deterministic_across_builds(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"

    publish(first)
    publish(second)

    assert sorted(p.name for p in first.iterdir()) == sorted(
        p.name for p in second.iterdir()
    )
    for payload in first.iterdir():
        assert (second / payload.name).read_bytes() == payload.read_bytes(), (
            payload.name
        )

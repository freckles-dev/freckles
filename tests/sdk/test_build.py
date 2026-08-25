"""Payload building: a plugin script + the inlined SDK = one standalone file.

The standard plugins dogfood `freckles.sdk` (The v1 cut), yet run as bare
executables under a scrubbed environment where the freckles package is not
importable. The builder inlines the SDK source into the script, so the
published payload needs nothing but a Python standard library.
"""

import ast
import subprocess
import sys
from pathlib import Path

from freckles.documents import from_wire, to_wire
from freckles.sdk.build import build_payload

SAMPLE_PLUGIN = """\
from freckles.sdk import emit_outcome, read_request

request = read_request()
emit_outcome({"kind": "sample", "node": request["node"]["name"]})
"""


def imported_roots(source: str) -> set[str]:
    roots = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_the_sdk_module_is_stdlib_only():
    import freckles.sdk

    roots = imported_roots(Path(freckles.sdk.__file__).read_text())

    assert roots <= set(sys.stdlib_module_names)


def test_built_payload_is_stdlib_only(tmp_path):
    script = tmp_path / "sample_plugin.py"
    script.write_text(SAMPLE_PLUGIN)

    payload = build_payload(script)

    roots = imported_roots(payload.decode())
    assert "freckles" not in roots
    assert roots <= set(sys.stdlib_module_names)


def test_built_payload_speaks_the_wire(tmp_path):
    script = tmp_path / "sample_plugin.py"
    script.write_text(SAMPLE_PLUGIN)
    payload_file = tmp_path / "sample-payload"
    payload_file.write_bytes(build_payload(script))
    request = {
        "schema": 1,
        "node": {"name": "demo/sample", "config": {}},
        "inputs": {},
        "workspace": {"dir": str(tmp_path), "path": [], "envs": str(tmp_path)},
    }

    completed = subprocess.run(
        [sys.executable, str(payload_file)],
        input=to_wire(request).encode(),
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    outcome = from_wire(completed.stdout)
    assert outcome["claim"]["kind"] == "sample"
    assert outcome["claim"]["node"] == "demo/sample"
    assert outcome["claim"]["schema"] == 1  # emit_outcome stamps it

"""The acceptance world: the real CLI binary, real upstream downloads.

Network-bound by design — runs only in the acceptance workflow (manual
dispatch + version tags) and locally on demand: `uv run pytest acceptance`.
The per-push suite never collects this directory.

The world drives the installed `freckles` console script as a subprocess
(the true released surface, prompts included), against a configuration
rendered from `acceptance/chains.py`. The standard-plugin payloads come
off the same publishing path the release uses — `scripts/
build_plugin_payloads.py` into a localhost docroot — while mise, pixi,
and copier are fetched from their real upstreams.
"""

import hashlib
import importlib.util
import os
import re
import subprocess
import sys
import threading
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import chains
import pytest

REPO_ROOT = Path(__file__).parent.parent
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_plugin_payloads.py"

VALUES_DAY1 = "apps:\n  karakeep:\n    enabled: false\n"
VALUES_DAY2 = "apps:\n  karakeep:\n    enabled: true\n"


def _load_tests_conftest():
    """The hermetic suite's conftest — the reference sops-encrypt lives there."""
    spec = importlib.util.spec_from_file_location(
        "tests_conftest", REPO_ROOT / "tests" / "conftest.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass
class AcceptanceWorld:
    config_dir: Path
    data_dir: Path
    state_dir: Path
    env: dict
    plugin_pins: dict  # plugin name -> (url, sha256)

    def freckles(self, *args: str, input: str | None = None):
        binary = Path(sys.executable).with_name("freckles")
        return subprocess.run(
            [str(binary), *args],
            cwd=self.config_dir,
            env=self.env,
            input=input,
            text=True,
            capture_output=True,
            timeout=1800,
        )

    def healed(self, result) -> set[str]:
        """The exact healed set — pure re-derivations only.

        Confirmed checkpoints appear as their ▶ blocks, never as healed
        lines (R3). A regex, because the `proceed? [y/N]:` prompt has no
        trailing newline and concatenates with the next output line.
        """
        return set(re.findall(r"(\S+)\s+healed\b", result.stdout))

    def write_mise_chain(self) -> None:
        (self.config_dir / "freckles.yaml").write_text(
            chains.mise_chain(
                bootstrap_mise_url=self.plugin_pins["bootstrap-mise"][0],
                bootstrap_mise_sha256=self.plugin_pins["bootstrap-mise"][1],
                mise_install_url=self.plugin_pins["mise-install"][0],
                mise_install_sha256=self.plugin_pins["mise-install"][1],
                state_dir=str(self.state_dir),
            )
        )

    def write_pixi_chain(self) -> None:
        (self.config_dir / "freckles.yaml").write_text(
            chains.pixi_chain(
                bootstrap_pixi_url=self.plugin_pins["bootstrap-pixi"][0],
                bootstrap_pixi_sha256=self.plugin_pins["bootstrap-pixi"][1],
                pixi_install_url=self.plugin_pins["pixi-install"][0],
                pixi_install_sha256=self.plugin_pins["pixi-install"][1],
                state_dir=str(self.state_dir),
            )
        )

    def edit_values(self) -> None:
        (self.config_dir / "cluster.yaml").write_text(VALUES_DAY2)


@pytest.fixture
def acceptance_world(tmp_path):
    from pyrage import x25519

    from freckles._version import version as freckles_version

    # The payloads, off the exact publishing path the release workflow uses.
    docroot = tmp_path / "www"
    subprocess.run(
        [sys.executable, str(BUILD_SCRIPT), str(docroot)],
        check=True,
        capture_output=True,
    )
    handler = partial(SimpleHTTPRequestHandler, directory=str(docroot))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    plugin_pins = {}
    for script in sorted((REPO_ROOT / "plugins").glob("*.py")):
        name = script.stem.replace("_", "-")
        artifact = docroot / f"{name}-{freckles_version}"
        plugin_pins[name] = (
            f"{base}/{artifact.name}",
            hashlib.sha256(artifact.read_bytes()).hexdigest(),
        )

    config_dir = tmp_path / "acceptance"
    config_dir.mkdir()
    (config_dir / "cluster.yaml").write_text(VALUES_DAY1)

    identity = x25519.Identity.generate()
    key_file = tmp_path / "age-key.txt"
    key_file.write_text(f"{identity}\n")
    _load_tests_conftest().sops_encrypt_file(
        config_dir / "secrets.sops.yaml",
        {"deploy_token": "acceptance-t0k3n"},
        identity,
    )

    world = AcceptanceWorld(
        config_dir=config_dir,
        data_dir=tmp_path / "data",
        state_dir=tmp_path / "world-state",
        env={
            **os.environ,
            "FRECKLES_DATA_DIR": str(tmp_path / "data"),
            "SOPS_AGE_KEY_FILE": str(key_file),
        },
        plugin_pins=plugin_pins,
    )
    world.write_mise_chain()
    yield world
    server.shutdown()

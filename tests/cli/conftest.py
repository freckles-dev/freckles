"""Shared world for CLI seam tests (milestone 1, GitHub issue #1).

The ratified surface is tested end to end: CliRunner drives the click app
in-process over a real configuration directory (= cwd, per the surface
contract) and a real sqlite store/state under FRECKLES_DATA_DIR. No internal
mocks — the only substitution point is the CLI's own stdin for the
checkpoint prompt.
"""

from dataclasses import dataclass
from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from freckles.cli import main

# The walking-skeleton chain: two pure nodes feeding one effectful checkpoint.
CHAIN = """
nodes:
  values/apps:
    op: import-values
    config: {file: cluster.yaml, key: apps}
  render/site:
    op: command
    consumes: [values]
    config:
      kind: file-tree
      effect: pure
      cmd: [sh, -c, "mkdir -p out && cp inputs/values out/site.yaml"]
  deploy/site:
    op: command
    consumes: [file-tree]
    config:
      kind: deployed-site
      effect: effectful
      cmd: [sh, -c, "cat inputs/file-tree/site.yaml > /dev/null"]
      claim: {site: demo}
"""

VALUES_DAY1 = "apps:\n  karakeep:\n    enabled: false\ncluster:\n  name: staging\n"
VALUES_DAY2 = "apps:\n  karakeep:\n    enabled: true\ncluster:\n  name: staging\n"


@dataclass
class CliWorld:
    config_dir: Path
    data_dir: Path
    runner: CliRunner

    def edit_values(self) -> None:
        """The day-2 config edit: enable the app, rippling values -> render -> deploy."""
        (self.config_dir / "cluster.yaml").write_text(VALUES_DAY2)

    def add_second_values_provider(self) -> None:
        """A second `values` source — makes render/site's consumed edge ambiguous."""
        (self.config_dir / "freckles.yaml").write_text(
            CHAIN
            + """
  values/cluster:
    op: import-values
    config: {file: cluster.yaml, key: cluster}
"""
        )

    def invoke(
        self,
        *args: str,
        input: str | None = None,
        env: dict[str, str | None] | None = None,
    ) -> Result:
        merged: dict[str, str | None] = {"FRECKLES_DATA_DIR": str(self.data_dir)}
        if env:
            merged.update(env)
        return self.runner.invoke(
            main, list(args), input=input, env=merged, catch_exceptions=False
        )


@pytest.fixture
def world(tmp_path, monkeypatch) -> CliWorld:
    config_dir = tmp_path / "demo"
    config_dir.mkdir()
    (config_dir / "freckles.yaml").write_text(CHAIN)
    (config_dir / "cluster.yaml").write_text(VALUES_DAY1)
    monkeypatch.chdir(config_dir)
    return CliWorld(
        config_dir=config_dir, data_dir=tmp_path / "data", runner=CliRunner()
    )

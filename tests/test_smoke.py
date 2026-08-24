"""Scaffolding smoke tests: the package imports and the CLI entry point answers."""

from click.testing import CliRunner

from freckles._version import version
from freckles.cli import main


def test_version_exists():
    """The build hook writes a real version string."""
    assert isinstance(version, str)
    assert version


def test_cli_reports_version():
    """`freckles --version` runs and names the package."""
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "freckles" in result.output

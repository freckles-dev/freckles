"""Build the standard plugins into release payload artifacts (M9).

Called by the release workflow (and the publishing tests): every script
in `plugins/` becomes one bare executable named `<plugin-name>-<version>`
in the given output directory — the artifact fetch-verify pins by URL +
checksum. The payload bytes are a pure function of the sources, so a
published checksum survives a rebuild.
"""

import sys
from pathlib import Path

from freckles._version import version
from freckles.sdk.build import build_payload

PLUGINS_DIR = Path(__file__).parent.parent / "plugins"


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for script in sorted(PLUGINS_DIR.glob("*.py")):
        name = script.stem.replace("_", "-")
        artifact = out / f"{name}-{version}"
        artifact.write_bytes(build_payload(script))
        artifact.chmod(0o755)
        print(artifact.name)


if __name__ == "__main__":
    main(sys.argv[1])

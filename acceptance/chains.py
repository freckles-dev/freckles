"""The acceptance chains: the mechanics-complete synthetic chain, real pins.

The v1 acceptance bar (docs/milestones-v1.md): bootstrap → install →
import-values/import-sops → pure render → effectful command, exercising
checkpoints, `prior:`, secret resolution at the boundary, staleness/heal,
and drift — with copier installable through **both** bootstrap routes.

Two kinds of URL live here, deliberately:

- mise, pixi, and copier come from their **real upstreams** — exactly the
  downloads the hermetic suite fakes. The bootstrap nodes pin version +
  sha256 only, so the plugins' default URL derivation (mise's and pixi's
  release-artifact naming — an assumed contract in M6/M7) is validated
  against the real releases.
- the standard-plugin payloads are served from a localhost server built by
  `scripts/build_plugin_payloads.py`: the acceptance workflow gates the
  release that publishes them, so no published URL exists yet. Their
  fetch-verify mechanics are URL-host-independent and covered per-push.

Linux x86_64 only (named cut): the release matrix smoke-runs each binary
on its native runner; the chain itself runs once.

The per-push resolve-guard (`tests/cli/test_acceptance_guard.py`) resolves
these same documents hermetically, and pins the mechanics tail byte-identical
across routes — the swap's ripple-stop depends on it.
"""

MISE_VERSION = "2026.8.12"
MISE_SHA256 = "f2092b1e67f0abc8803d3be120dd2bc5b656dd99680ba3159f710e149da10d05"

PIXI_VERSION = "0.77.1"
PIXI_SHA256 = "5115a89a9189a2e4e7e8d2f04236a7be586d8f6091dfc9ea869fb3c4a52b6935"

# Present on PyPI and conda-forge alike: the swap mints byte-identical tool
# claims only if both routes install the same version.
COPIER_VERSION = "9.17.2"

_MISE_HEAD = """\
nodes:
  plugins/bootstrap-mise:
    op: fetch-verify
    config:
      kind: plugin
      url: {bootstrap_mise_url}
      sha256: "{bootstrap_mise_sha256}"
      manifest:
        {{name: bootstrap-mise, version: 0.1.0, produces: bootstrap, effect: pure}}
  plugins/mise-install:
    op: fetch-verify
    config:
      kind: plugin
      url: {mise_install_url}
      sha256: "{mise_install_sha256}"
      manifest:
        name: mise-install
        version: 0.1.0
        produces: tool
        effect: pure
        consumes: {{bootstrap: {{}}}}
  bootstrap:
    op: bootstrap-mise
    config: {{version: "{mise_version}", sha256: "{mise_sha256}"}}
  tools/copier:
    op: mise-install
    config: {{package: copier, version: "{copier_version}"}}
"""

_PIXI_HEAD = """\
nodes:
  plugins/bootstrap-pixi:
    op: fetch-verify
    config:
      kind: plugin
      url: {bootstrap_pixi_url}
      sha256: "{bootstrap_pixi_sha256}"
      manifest:
        {{name: bootstrap-pixi, version: 0.1.0, produces: bootstrap, effect: pure}}
  plugins/pixi-install:
    op: fetch-verify
    config:
      kind: plugin
      url: {pixi_install_url}
      sha256: "{pixi_install_sha256}"
      manifest:
        name: pixi-install
        version: 0.1.0
        produces: tool
        effect: pure
        consumes: {{bootstrap: {{}}}}
  bootstrap:
    op: bootstrap-pixi
    config: {{version: "{pixi_version}", sha256: "{pixi_sha256}"}}
  tools/copier:
    op: pixi-install
    config: {{package: copier, version: "{copier_version}"}}
"""

# Byte-identical across routes (the guard pins it): the real copier answers
# on the constructed PATH inside the pure render, the deploy consumes the
# rendered tree plus the sops secret, and its verify entrypoint watches the
# world state the run creates — the drift leg deletes it.
_MECHANICS_TAIL = """\
  values/apps:
    op: import-values
    config: {{file: cluster.yaml, key: apps}}
  secrets/deploy-token:
    op: import-sops
    config: {{file: secrets.sops.yaml, key: deploy_token}}
  render/site:
    op: command
    consumes: [values, tool]
    config:
      kind: file-tree
      effect: pure
      cmd:
        [sh, -c, 'copier --version | grep -q "{copier_version}" && mkdir -p out
          && cp inputs/values out/site.yaml']
  deploy/site:
    op: command
    consumes: [file-tree, secret]
    config:
      kind: deployed-site
      effect: effectful
      cmd:
        [sh, -c, 'test -n "$DEPLOY_TOKEN" && cat inputs/file-tree/site.yaml
          > /dev/null && mkdir -p {state_dir} && touch {state_dir}/deployed']
      verify: [sh, -c, "test -f {state_dir}/deployed"]
      secret-env: {{DEPLOY_TOKEN: secret}}
      claim: {{site: acceptance}}
"""


def mise_chain(
    *,
    bootstrap_mise_url: str,
    bootstrap_mise_sha256: str,
    mise_install_url: str,
    mise_install_sha256: str,
    state_dir: str,
) -> str:
    return (_MISE_HEAD + _MECHANICS_TAIL).format(
        bootstrap_mise_url=bootstrap_mise_url,
        bootstrap_mise_sha256=bootstrap_mise_sha256,
        mise_install_url=mise_install_url,
        mise_install_sha256=mise_install_sha256,
        mise_version=MISE_VERSION,
        mise_sha256=MISE_SHA256,
        copier_version=COPIER_VERSION,
        state_dir=state_dir,
    )


def pixi_chain(
    *,
    bootstrap_pixi_url: str,
    bootstrap_pixi_sha256: str,
    pixi_install_url: str,
    pixi_install_sha256: str,
    state_dir: str,
) -> str:
    return (_PIXI_HEAD + _MECHANICS_TAIL).format(
        bootstrap_pixi_url=bootstrap_pixi_url,
        bootstrap_pixi_sha256=bootstrap_pixi_sha256,
        pixi_install_url=pixi_install_url,
        pixi_install_sha256=pixi_install_sha256,
        pixi_version=PIXI_VERSION,
        pixi_sha256=PIXI_SHA256,
        copier_version=COPIER_VERSION,
        state_dir=state_dir,
    )

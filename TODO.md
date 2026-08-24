# TODO

Things to do once, right after generating this project. Delete the entries as you go, and
delete this file when it's empty.

## Publishing to PyPI

The `release_python_package` job in `.github/workflows/build-linux.yaml` publishes with
[trusted publishing](https://docs.pypi.org/trusted-publishers/), so there is no API token to
create. You do have to register the publisher first:

1. Go to <https://pypi.org/manage/account/publishing/>.
2. Add a new pending publisher:
   - PyPI project name: `freckles`
   - Owner: `freckles-dev`
   - Repository name: `freckles`
   - Workflow name: `build-linux.yaml`
   - Environment name: `pypi`

Releases are triggered by pushing a tag; the version comes from that tag via
`uv-dynamic-versioning`, so `git tag 0.1.0 && git push --tags` is all it takes.

## Publishing to anaconda.org

The conda package is built by `conda.recipe/recipe.yaml` and uploaded to the
`freckles` channel. Unlike PyPI this needs a token:

1. Create a token at <https://anaconda.org/freckles/settings/access> with the
   "Allow write access to the API site" scope.
2. Add it to this repository as a secret named `ANACONDA_PUSH_TOKEN`
   (Settings → Secrets and variables → Actions).

The release job fails fast with a clear message if the secret is missing.

## Keep the conda recipe in sync

`conda.recipe/recipe.yaml` cannot read `pyproject.toml`. Whenever you add or change an entry
in `[project].dependencies`, mirror it into `requirements.run` in the recipe -- otherwise the
conda package installs without its dependencies and the recipe's `pip_check` test fails.

## Fill in the placeholders

- `README.md` still has a `## Description` section that just says `TODO`.
- `docs/` is empty.

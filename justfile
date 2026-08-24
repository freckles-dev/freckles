default:
    @just --list

typecheck:
    uv run pyrefly check

typecheck-ty:
    uv run ty check

lint:
    uv run ruff check . --fix

format:
    uv run ruff format .

pre-commit:
    uv run pre-commit run --all-files

tests:
    uv run pytest tests -s

test pattern:
    uv run pytest tests -s -k {{pattern}}

# build the conda package locally; needs `pixi` on PATH, since rattler-build
# is a standalone binary and is not distributed on PyPI
build-conda:
    uv build
    PKG_VERSION=$(basename dist/*.whl | cut -d- -f2) pixi exec rattler-build build --recipe conda.recipe/recipe.yaml --channel conda-forge

update-template:
    uvx --with copier-template-extensions copier update --trust -T -A

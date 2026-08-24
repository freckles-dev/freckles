.PHONY: default typecheck typecheck-ty lint format tests test build-conda

default:
	@make -s help

help:
	@echo "Available targets:"
	@echo "  typecheck - Run type checking (pyrefly)"
	@echo "  typecheck-ty - Run type checking with ty instead"
	@echo "  lint      - Run linting with auto-fix"
	@echo "  format    - Run code formatting"
	@echo "  tests     - Run all tests"
	@echo "  test      - Run tests matching a pattern (use: make test pattern=your_pattern)"
	@echo "  build-conda - Build the conda package locally (requires pixi)"

typecheck:
	uv run pyrefly check

typecheck-ty:
	uv run ty check

lint:
	uv run ruff check . --fix

format:
	uv run ruff format .

tests:
	uv run pytest tests -s

test:
	uv run pytest tests -s -k $(pattern)

# needs `pixi` on PATH: rattler-build is a standalone binary, not a PyPI package
build-conda:
	uv build
	PKG_VERSION=$$(basename dist/*.whl | cut -d- -f2) pixi exec rattler-build build --recipe conda.recipe/recipe.yaml --channel conda-forge

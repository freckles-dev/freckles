"""Entry point for the Nuitka standalone guardrail (ADR 0006 rider).

Compiled by the freckles-guardrails CI workflow; the resulting binary must
answer `--version`. Mirrors what a distributed single-binary entry would be.
"""

from freckles.cli import main

if __name__ == "__main__":
    main()

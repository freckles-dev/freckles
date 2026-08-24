"""Pytest configuration and shared fixtures for freckles tests."""

# Installs the dbg/DBG/ic/insp/wat builtins (and activates snoop) for all tests.
import freckles._debug  # noqa: F401

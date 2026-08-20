# Plugins are process-protocol executables acquired as claims

Status: accepted (2026-08-20)

Two coupled decisions. First, the plugin contract is a **process protocol**:
a plugin is an executable receiving a request document on stdin and
returning an outcome document (or structured error) on stdout — never a
Python-native API, even though freckles is Python. Second, plugins are
themselves **claims**: content-addressed manifest + executable payload,
acquired through the same DAG that installs tools, pinned in provenance by
claim CID; only a minimal built-in set (source imports, fetch-verify,
command adapter) ships with freckles to break the bootstrap circle.

Rejected: a Python-primary plugin API (couples plugin authorship to
freckles' interpreter and dependency set — the entanglement the
userspace-first design exists to avoid), and externally-installed plugins
referenced by name+version (a second acquisition/pinning mechanism beside
the one the DAG already provides).

Consequences: plugins are language-agnostic and can pin their own runtimes
(uv inline metadata); the runner's workspace materialization is the
physical enforcement of ADR 0002; freckles' own version enters provenance
for built-in-produced outcomes; a Python SDK exists as sugar only.

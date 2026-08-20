# Only consumed claims enter a node's identity

Status: accepted (2026-08-20)

A node's **available environment** is the merge of all its transitive
predecessors' claims, keyed by kind — a resolution-time concept used for
edge inference and compatibility checks. Its **effective inputs** — what
enters the provenance record and the cache key — are only the claims
matching the operation's declared consumed kinds, and at run time the
runner presents the operation with exactly those claims, never the whole
environment. The alternative was a Nix-style strict closure in which
everything in scope taints identity. We chose the declared-consumption
boundary for authoring ergonomics — short chains, no ceremony — while
keeping hashing exact; the boundary is enforced by the runner, not merely
promised by plugins.

Consequences: adding unrelated upstream nodes never re-hashes downstream
nodes; ambiguity among *consumed* kinds is a hard error requiring explicit
selection (no silent precedence); a future explicit multi-consume
declaration (aggregators) remains possible without weakening the rule.

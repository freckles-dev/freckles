# Outcomes are addressed extensionally, by claim alone

Status: accepted (2026-08-20)

Every operation returns an outcome whose hashed part — the claim — describes
what now exists. We decided the outcome's address is the hash of the **claim
alone**; provenance (operation plugin + version, configuration, input claim
addresses) lives in a separate content-addressed provenance record, outside
the address. The alternative was Nix-style intensional (input-)addressing,
where identity covers the derivation. We chose extensional addressing so
that equivalent environments are interchangeable regardless of the route
that produced them (dedup, cross-machine reuse) and so trivial input changes
don't avalanche new addresses through the downstream tree — which is what
pushed Nix itself toward content-addressed derivations.

Consequences: a claim's address carries no derivation trust — trust comes
from the provenance record and the local trust domain, never from the
address. Caching stays a provenance-keyed lookup (derivation → outcome)
regardless of addressing. Decision held with explicit residual doubt
(Markus, 2026-08-20): revisit if "Storage and addressing" or "Effects and
day-2" surface cases where identical claims from different routes must not
unify.

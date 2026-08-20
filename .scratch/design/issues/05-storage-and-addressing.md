# Storage and addressing

Type: grilling
Status: open
Blocked by: 01, 04

## Question

Decide the storage model on top of the outcome definition (What is an
outcome?) and the CAS survey findings.

To resolve:

- What is stored content-addressably: user configurations, node configs,
  outcome documents, rendered file trees, transformer plugins themselves?
  The brief says "store our configuration content-addressable" — draw the
  exact line.
- The addressing scheme and canonical serialization (adopt or reject the
  survey's recommendation; IPFS-compatible addresses vs backend-local ones).
- The mutable layer over immutable hashes: how humans name things ("my
  staging cluster", "latest config") — refs? a root document? — and where
  mutability is allowed at all.
- The backend plugin interface (adopt/trim the survey's sketch): folder,
  sqlite, ipfs as the initial set.
- What replaces the vision doc's lockfile-and-artifact-store pair in this
  model, if anything.

Run /grilling and /domain-modeling. Grill against vision.md §8 (catalog
pinning) and open question 6 (artifact store).

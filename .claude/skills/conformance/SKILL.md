---
name: conformance
description: Amend the normative wire/store contracts. Use before editing conformance/*.cddl or golden fixtures, changing a store or wire document shape, or when a milestone names a schema amendment.
---

# Amending the normative contracts

`conformance/` is the language-external contract that keeps ADR 0006's
port option alive: data-only CDDL plus golden fixtures with real CIDs.
The goldens are normative — committed DAG-JSON and `CIDS.txt`, produced
only by `conformance/golden/make_golden.py`. A hand-edited fixture forks
the contract silently; the CI regen-diff job exists to catch exactly that.

## Steps

1. **Ratify the design first.** The shape change is a design amendment —
   the `milestone` skill's Tripwires carry the discipline. Done when the
   amendment is written and the user has confirmed it.

2. **Amend the CDDL** — `store.cddl` for store documents, `wire.cddl` for
   the stdio protocol — with a comment naming the deciding milestone or
   ticket, matching the file's existing style.

3. **Regenerate the goldens.** Extend `make_golden.py` if the change adds
   or reshapes a document, run it, and commit the regenerated fixtures
   together with the CDDL and code. Done when `git status` shows generator
   and fixtures moving in the same commit.

4. **Verify.** `just tests` green — the triple golden assertions and the
   dual-encoder cross-check (libipld vs the hashberg pair) must both hold.
   Any test that mints the new shape routes it through the
   `encode_checked` fixture.

## Boundary

The value-model bounds (no floats, tag-42 links, hashed `schema`) live in
`store.cddl`'s own header — read them there while editing. The one rule no
schema file states: only `src/freckles/documents/` touches DAG-CBOR, CIDs,
or libipld; a shape change reaches code through that module's dataclasses
and codecs, nowhere else.

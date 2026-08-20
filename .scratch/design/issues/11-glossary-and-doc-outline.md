# Glossary and doc outline

Type: grilling
Status: open
Blocked by: 05, 07, 08, 09, 10

## Question

The last decision before the design doc is written: settle the ubiquitous
language and the doc's structure.

To resolve:

- Names, finally: the brief itself flags "transformer" vs "tasks" — "we'll
  have to settle on how to call things". Fix the term for: the operation
  plugin, a node, an outcome, the environment a node provides, the store,
  the bootstrap root, the user's configuration. Prefer terms that survived
  the ticket discussions; retire vision-doc terms that didn't (stage?
  frecklet? artifact? journal?).
- One-line definitions for each term — the design doc's glossary section,
  agreed before writing.
- The design doc's outline: section order, what the worked example (The
  rosekube chain on paper) anchors, what is stated as superseding vision.md,
  and what the doc explicitly defers (pointers into the map's out-of-scope
  and remaining fog).

Run /grilling and /domain-modeling — this ticket *is* the domain-model
consolidation. When it closes, the map's way is clear: write docs/design.md.

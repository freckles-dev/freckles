# Standard plugins

The standard plugins live here as standalone, SDK-consuming scripts — built and
published as plugin claims by CI, never imported by `freckles` itself. The
artifact boundary enforces the plugin contract (ADR 0004): each is invoked as a
process, request document on stdin, outcome or error on stdout.

Populated milestone by milestone after the walking skeleton; see the layout doc
(`.scratch/impl/assets/08-package-layout.md`) and the design (`docs/design.md`).

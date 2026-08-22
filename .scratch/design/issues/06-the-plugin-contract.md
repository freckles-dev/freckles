# The plugin contract

Type: grilling
Status: resolved
Blocked by: 01, 02

## Question

Nodes are produced by pluggable operations — the brief calls them package
install "transformers" (or maybe "tasks"; naming settles in Glossary and doc
outline). A plugin could be a simple command, a Python script, or a Python
package. Decide the contract.

To resolve:

- The interface: how a plugin receives its inputs (parent outcomes + node
  config) and returns its outcome dict — stdin/stdout JSON for commands?
  a Python API for scripts/packages? One protocol with adapters?
- How plugins are declared, discovered, and pinned — and whether a plugin's
  own version/hash is part of the node's input hash (the vision doc said yes
  for transformers; presumably survives).
- The trust/purity contract per kind: what a pure plugin may not do (the
  vision doc's no-timestamps/no-env-leakage/no-undeclared-network contract),
  what an effectful plugin must guarantee (accurate outcome reporting), and
  how much is enforced vs promised.
- Whether the vision doc's initial transformer set (copier, uv-python, pixi,
  command) survives as the initial plugin set.
- How a plugin declares what it *needs* from its parent environment (tools on
  PATH at pinned versions?) — the userspace-first requirement lands here.

Routed here by The shape of the tree (resolved): the **consumption
selector** mechanism — declaring consumed kinds needs more than the bare
kind (`tool(opentofu)` must match kind `tool` *and* `tool: opentofu`);
define the selector form. Also: the runner **enforces** ADR 0002 — an
operation receives exactly its effective inputs at run time, never the
available environment; the contract must specify how (working-dir/env
isolation, what is materialized for the plugin). And the door left open in
02: a possible future *explicit* multi-consume declaration (aggregators).

## Answer

Resolved 2026-08-20 over two grilling rounds; confirmed by Markus.
Assets: [ADR 0004](../../../docs/adr/0004-plugins-are-process-claims.md),
[wire-protocol strawman](../assets/06-wire-protocol.yaml), glossary in
[CONTEXT.md](../../../CONTEXT.md).

1. **The process protocol is the contract**: a plugin is an executable —
   request document on stdin (effective inputs as claim+annotations pairs,
   node config, workspace), outcome document or structured error on stdout,
   exit code for success/failure. A Python SDK is sugar, never contract.
   One generic `command` adapter wraps arbitrary commands.
2. **Plugins are claims**: acquired, pinned, and hashed like tools —
   `kind: plugin`, content = manifest + executable payload in the CAS;
   provenance pins the plugin claim CID. A minimal **built-in set** ships
   with freckles itself (its version enters provenance for built-in-produced
   outcomes): `import-values`, `import-file-tree`, `import-sops`,
   `fetch-verify`, `command`.
3. **Selectors**: kind + flat field-equality constraints, plugin-declared,
   node-augmentable (`use:` breaks ambiguity). Revisit only if a real
   catalog case defeats it.
4. **Enforcement split**: the runner *physically* enforces visibility
   (ADR 0002) — isolated workspace, scrubbed environment, consumed tool
   claims materialized onto a constructed PATH, content claims as files;
   the plugin assembles nothing itself. Purity (determinism, no undeclared
   network) is *contract*, with an optional run-twice determinism check as
   catalog CI. No kernel sandbox in v1 (vision doc stance carried).
5. **Initial set**: built-ins above, plus standard plugins
   `bootstrap-mise` (default), **`bootstrap-pixi` — first-class in
   parallel, per Markus**, `mise-install`, `uv-python`, `copier`.
   Catalog-level plugins (`tofu-apply`, `flux-bootstrap`, `git-push`) come
   with curation. The only true root is `fetch-verify`.
6. **Produced kind**: exactly one, statically declared in the manifest —
   what makes resolution-time edge inference possible. Claim fields beyond
   `kind` are convention; per-kind field conventions are curation policy
   (→ Where curation lives). Markus caveat recorded: "can't foresee
   whether this will be enough — good place to start."
7. **Manifest**: `name`, `version`, `produces`, `consumes`, `effect:
   pure|effectful`, `platforms`, `entrypoint`. Deliberately absent: tool
   dependencies (consume tool claims instead) and config schemas (the
   plugin's own business in v1).
8. **Wire shape** adopted as the design doc's illustrative contract (asset
   above); field names non-normative until the doc is written.

Unchanged: the aggregator door stays a named future extension (per The
shape of the tree); effectful checkpoint UX belongs to Effects and day-2.

Run /grilling and /domain-modeling. Grill against vision.md §3 (transformer),
§7 (toolchain provisioning), open question 3.

## Amendment (2026-08-22)

Two changes from the design-doc review (Markus):

1. The built-in set grows by `import-git`, moved from the standard set —
   rationale and consequence in Where curation lives (amendment,
   2026-08-22) and design.md §6.
2. The produced-kind rule restated: the invariant is that **every node's
   produced kind is fixed at resolution time**, not that every manifest
   declares one. Ordinary plugins still declare exactly one kind; the
   adapter plugins (`command`, `fetch-verify`) declare the kind
   node-supplied, making `kind` a mandatory node-config field for them —
   one kind per node at resolution, inference unaffected. Node config is
   hashed into the derivation, so the supplied kind is identity like any
   other config; annotations were rejected as the vehicle (unhashed,
   machine-local). `command`'s consumed selectors are likewise
   node-supplied, via the existing node-augmentable selector mechanism.

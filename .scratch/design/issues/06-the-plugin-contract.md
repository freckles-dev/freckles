# The plugin contract

Type: grilling
Status: open
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

Run /grilling and /domain-modeling. Grill against vision.md §3 (transformer),
§7 (toolchain provisioning), open question 3.

# Secrets in the outcome model

Type: grilling
Status: resolved
Blocked by: 01

## Question

The vision doc's secrets design (§6) is crisp: sops/age-encrypted values,
ciphertext hashed as an ordinary input, decryption only at execution time,
render stages never see plaintext. Decide whether it carries into the
outcome model unchanged — and close the gaps the new model opens.

To resolve:

- Carry-over: confirm ciphertext-as-hashed-input survives as-is, or amend.
- The new gap: may an *outcome* contain secret material? An effectful node
  might produce credentials (a kubeconfig, a generated admin password).
  Outcomes are hashed, stored, possibly shared (IPFS!) — the rule for secret
  outputs must be explicit (encrypt into the outcome? reference without
  storing? forbid?).
- Where decryption happens in the tree model: which node kinds may decrypt,
  and does "render never sees plaintext" translate cleanly to "pure nodes
  never see plaintext"?
- The boundary case named by What is an outcome? (resolved), raised by
  Markus with the kubeconfig example: credentials are world-true but
  arguably not identity-defining. Claim field (rotation churns the claim
  address and ripples staleness — the vision doc *wanted* this ripple for
  secret rotation; still wanted?), annotation (no churn, but the outcome
  can no longer grant access when it travels — and credentials cannot be
  re-realized from provenance), or a third home (e.g. a mutable ref keyed
  by claim address — which drags Storage and addressing in)?

Run /grilling and /domain-modeling. Grill against vision.md §6.

## Answer

Resolved 2026-08-21 over three grilling rounds; every point explicitly
adopted by Markus. Assets:
[ADR 0005](../../../docs/adr/0005-plaintext-only-at-the-execution-boundary.md),
glossary terms in [CONTEXT.md](../../../CONTEXT.md), secrets additions to
the [wire-protocol asset](../assets/06-wire-protocol.yaml).

1. **Contract-first shapes** (reshaped the ticket: Markus challenged the
   baked-in sops assumption, secretspec facts verified from secretspec.dev).
   The secret claim kind is a contract admitting multiple shapes — two
   specified now, the set explicitly open to future mechanisms:
   *value-bearing* (ciphertext, sops/age) and *reference-bearing*
   (provider-resolved, secretspec-style). `import-sops` is the v1 built-in;
   a secretspec-backed acquisition plugin is the named route to the 30+
   provider world — a plugin, not a redesign (the mise precedent).
2. **The two flows** vision §6 blurred, now split: *flow A* — secrets
   freckles itself resolves to plaintext at execution time — is all the
   shape choice governs; *flow B* — ciphertext as content, embedded by pure
   renders and decrypted by the target (sops-in-manifests, Flux in-cluster)
   — is ordinary bytes and carries over untouched under any shape.
3. **Value-bearing shape**: identity is the ciphertext (content-hash
   reference). CAS-resident by default — vision's "ciphertext is
   publishable" stance carried, with a design-doc note on long-horizon
   secrecy; no non-exportable block coloring (backends stay
   codec-ignorant). The **detached-value variant** (`store: false` import)
   keeps hash-identity and the rotation ripple while the bytes stay in the
   config working copy, never entering the CAS — the operator's opt-out
   from publishing ciphertext. Rotation ripples via the ordinary
   derivation mechanism.
4. **Reference-bearing shape**: identity is the **logical name alone** —
   which provider holds the value on this machine is machine-local
   configuration, recorded in annotations at resolution (secretspec's
   declaration/provider split, translated). Stated honestly: rotation is
   invisible to staleness; the day-2 verify → distrust → stale path is the
   rotation story for references. Provider+name and provider+name+revision
   were rejected (topology pinning; provider-specific concept in a
   machine-independent claim); revision-pinning stays possible as a future
   shape behind the open door.
5. **The purity gate** ("render never sees plaintext", translated): no
   pure operation ever receives plaintext — `effect: effectful` gates
   resolution. Grounds: pure claims realize by re-derivation from consumed
   claims alone (a key or provider lookup would silently break that), and
   pure outputs are shareable CAS content. Pure nodes may consume and
   embed *ciphertext* (flow B). No legitimate "pure but needs plaintext"
   case exists.
6. **Runner-side resolution**: the runner resolves secret claims to
   plaintext in memory at the request-document boundary and injects it
   into the effectful plugin's stdin request (`resolved:` on the input
   entry); plaintext never touches disk, store, provenance, or audit.
   No new manifest flag — `consumes: secret(...)` plus `effect: effectful`
   is the declaration; the checkpoint prompt announces "receives plaintext
   secrets: <names>"; wiring a secret claim's plaintext into a pure plugin
   is a resolution-time hard error. v1 resolves value-bearing claims
   (built-in sops/age); the reference **resolver hook** is a named future
   manifest entrypoint alongside `verify`/`destroy`.
7. **Credentials live in annotations** (the kubeconfig boundary case from
   What is an outcome?): access material, not identity (ADR 0005). The
   claim describes the environment (cluster exists, endpoint, CA
   fingerprint); the kubeconfig is a secret-marked annotation. Credential
   rotation updates annotations under an unchanged claim — no downstream
   churn; the input/output asymmetry is principled (consumed ciphertext is
   identity per ADR 0002, produced access material is not). Costs owned:
   machine-bound use, no recovery from the store — re-mint via the tool.
   Encrypted claim fields rejected; provider-parking (credential written
   to a secret provider, outcome carries a secret reference) is the named
   future transport path.
8. **Consumption rule sharpened** (amends What is an outcome? point 9,
   reconciling it with day-2's claims-only stance): **pure operations
   receive claims only; effectful operations receive claim + whatever
   annotations exist locally.** Unhashed annotations feeding a pure
   derivation would silently break extensional caching; effectful
   operations are machine-bound and checkpointed, and local annotations
   are exactly what they act with. CONTEXT.md's Effective inputs updated.
9. **Key model v1**: a single user age key, sops-compatible (honors
   `SOPS_AGE_KEY_FILE`), strictly outside the store — never hashed, never
   in any claim or provenance record. Key rotation = re-encrypt values →
   ciphertext churn → deliberate staleness ripple. Provider
   authentication is the future resolver's business; team/multi-recipient
   keys stay in the multi-machine fog.
10. **Marking and redaction**: an annotation carrying secret material is
    marked (reserved `secret: true` on the entry) — freckles never prints
    it in status/diff output and keeps the annotations index owner-only.
    The audit log records that secrets were resolved (names, never
    values). Plugins must not log plaintext — contract, not sandbox,
    matching the purity precedent.
11. **Terminology** (glossary in CONTEXT.md): **secret value** /
    **secret reference** / **credential**; "secret" alone retired as a
    model term.

Supersessions of vision.md §6 made explicit: the sops-only mechanism
generalizes to the shaped contract (sops remains the v1 default); "render
stages never see plaintext" becomes the purity gate on resolution; the
rotation ripple is preserved for value-bearing secrets and explicitly
absent for references.

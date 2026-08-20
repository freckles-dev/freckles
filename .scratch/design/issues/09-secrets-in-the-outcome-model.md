# Secrets in the outcome model

Type: grilling
Status: open
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

Run /grilling and /domain-modeling. Grill against vision.md §6.

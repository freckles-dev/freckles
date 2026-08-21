# Plaintext secrets exist only at the execution boundary

Status: accepted (2026-08-21)

Secret material never enters a claim, the store, a provenance record, or the
audit log. The runner resolves secret claims to plaintext in memory at the
request-document boundary, and only for effectful operations — pure
operations never receive plaintext, only ciphertext they may embed.
Credentials minted by effectful operations (a kubeconfig, a generated admin
password) live in annotations: access material, not identity. The considered
alternative was encrypting credentials into claim fields, which buys
transport and durability; we rejected it because credential rotation would
churn the claim address and ripple spurious staleness through consumers that
depended on the environment (the cluster), not the credential bytes — and it
forces encrypt-to-recipient decisions and puts long-lived credential
ciphertext into a shareable store.

Consequences: a credential-bearing outcome is usable only on the machine
holding its annotations, and credentials cannot be recovered from the store —
losing the machine means re-minting via the underlying tool (consistent with
the machine-bound stance on effectful re-runs). Credential rotation updates
annotations under an unchanged claim, so it never marks consumers stale;
input-secret rotation, by contrast, ripples deliberately because consumed
ciphertext is identity. Parking credentials in a secret provider with a
reference-bearing claim is the named future path if credential transport
earns a use case.

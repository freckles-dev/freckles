# freckles — Design

Status: current (2026-08-21). This document supersedes
[vision.md](vision.md) wherever the two diverge; §1 lists the divergences
explicitly. It is the consolidated result of the eleven decisions on the
[wayfinder map](../.scratch/design/map.md); each section links the ticket
holding its full reasoning, and five ADRs under [adr/](adr/) record the
decisions that were genuine trade-offs. This document is written to be
precise enough to seed the formal specification and a first implementation.

## 1. Motivation and what this supersedes

freckles turns minimal declarative configuration into running
infrastructure and IT state through a DAG of named, hashed,
content-addressed operations. It is Nix-inspired — purity where purity
pays, content addressing, exact pinning — but deliberately not Nix: it
runs on any Linux distribution, in userspace, with root/sudo supported but
rarely required, and it stops short of Nix's rigor where the cost
outweighs the benefit. Outputs describe the environment and its
capabilities; the standing design values are elegance and limited
complexity.

The vision document remains valid for motivation, curation philosophy, and
the reproducibility stance. Its *model*, however, is replaced:

| vision.md concept | replaced by |
|---|---|
| pipeline of stages | DAG of named nodes (§5) |
| render stage / execute stage | pure / effectful **operation** — one uniform concept, purity declared (§6) |
| transformer | operation, implemented by a **plugin** (§6) |
| artifact (byte-hashed file tree) | **outcome** = claim + annotations; byte trees survive only as CAS content referenced *inside* claims (§4) |
| input-hash identity | **extensional addressing**: a claim is addressed by its own content; derivations key the cache, not the address (ADR 0001, §4) |
| lockfile + artifact store | **resolution document** + content-addressed **store** (§7) |
| journal | **audit log** + content-addressed **provenance records** (§8) |
| tool store | tools are ordinary claims, realized through the bootstrap chain (§11) |
| frecklet / catalog mechanics | deferred to a follow-up effort, with extension points fixed now (§12) |

Retired vocabulary (do not use in specs or code): *stage*, *pipeline*,
*render/execute stage*, *transformer*, *artifact*, *journal*, *lockfile*,
*frecklet*, *tool store*. Surviving unchanged: *checkpoint*, *catalog* (as
the named deferral), the sops/age mechanism, userspace-first, and the rule
that effectful work is never implicit.

## 2. The model at a glance

The user owns one **configuration**: a git working copy holding a DAG of
named nodes plus the values and secret files beside it. Each **node**
binds a stable, path-like name to an **operation** (a pluggable unit of
work), that node's config, and input edges — mostly inferred, explicit
where ambiguous. Resolving the configuration produces a content-addressed
**resolution document** (the lockfile's successor). Running a node
produces an **outcome**: a hashed, machine-independent **claim**
describing what now exists, plus unhashed, machine-local **annotations**
recording where it is realized here. Claims live in a per-user
content-addressed **store**; effectful nodes only ever run as explicit
**checkpoints**. Day-2 is one loop: edit the configuration, re-resolve, heal —
**stale** nodes (current claim not produced by current derivation)
re-derive automatically where pure; the stale effectful remainder, the
**checkpoint set**, is confirmed per node.

A five-node taste (the full chain is §10):

```yaml
nodes:
  bootstrap:            { op: bootstrap-mise, config: { version: 2025.8.1 } }
  tools/opentofu:       { op: mise-install,   config: { package: opentofu, version: 1.8.2 } }
  values/cluster:       { op: import-values,  config: { file: cluster.yaml, key: cluster } }
  secrets/proxmox-api-token:
                        { op: import-sops,    config: { file: secrets.sops.yaml, key: proxmox_api_token } }
  infra/staging:
    op: tofu-apply
    config: { module: talos-proxmox }
    # edges: tool(opentofu), values, secret — all inferred here (one
    # provider each); `use:` would break ties if providers multiplied
```

`infra/staging` is effectful: it runs as a confirmed checkpoint, receives
the plaintext of its secret only in memory at the process boundary, and
returns a claim describing the cluster — never how it was made, and never
its credentials.

## 3. Glossary

The canonical glossary is [CONTEXT.md](../CONTEXT.md) at the repository
root — this section mirrors it and CONTEXT.md wins on drift. The terms:
**operation**, **node**, **configuration**, **values**, **available
environment**, **effective inputs**, **plugin**, **source node**,
**terminal node**, **outcome**, **claim**, **annotation**, **secret
value**, **secret reference**, **credential**, **realization**, **stale**,
**checkpoint**, **checkpoint set**, **provenance record**, **store**, **ref**, **resolution
document**, **derivation index**, **trust**, **audit log**.

## 4. Outcomes

Decided in [What is an outcome?](../.scratch/design/issues/01-what-is-an-outcome.md)
and [Secrets in the outcome model](../.scratch/design/issues/09-secrets-in-the-outcome-model.md).

An outcome is a **present-tense description of what now exists and can be
consumed** — never a record of how it happened ("what happened" is the
audit log, which nothing downstream ever reads). One uniform envelope
serves pure and effectful operations alike; purity is a property the
operation declares.

- **Envelope = claim + annotations.** The claim carries identity-defining,
  machine-independent assertions about the world and a mandatory `kind`;
  the annotations carry non-identity realization facts (paths, timestamps,
  hosts) and are private to the machine — they live in a local index, not
  the store, and never travel.
- **Extensional addressing** ([ADR 0001](adr/0001-extensional-outcome-addressing.md)):
  the outcome's address is the hash of the claim alone. Provenance lives in
  a separate record (§8); equivalent environments unify regardless of the
  route that produced them, and input churn cannot avalanche new addresses
  through the DAG.
- **Value model**: claims are spec-strict DAG-CBOR — string-keyed maps,
  lists, strings, 64-bit integers, bools, null, CID links; no floats.
  Annotations are free-form. A hashed `schema` field versions the envelope;
  no address stability is promised across envelope versions.
- **Bytes**: portable content (rendered trees, imported files) is stored in
  the CAS and referenced from claims by CID. Live or local state (VMs,
  realized tool environments) is described, never byte-hashed.
- **Success-only.** Failures never mint outcomes; they exist solely in the
  audit log.
- **Trust** = acting on an outcome without re-checking the world. Pure
  outcomes are trusted unconditionally (worst case: re-derived); effectful
  outcomes are trusted until explicitly contradicted (§8). Verification is
  an explicit operation, never background polling.
- **Kinds**: every claim names its kind; consumers select on kind plus
  field equality. Core reserves only the kinds its built-ins and standard
  plugins need — `bootstrap`, `tool`, `plugin`, `file-tree`, `values`,
  `secret` — all other kinds are domain vocabulary governed as catalog
  content (§12). Convention: **flat kind names are reserved for official
  vocabulary** (core plus officially published catalogs); non-core
  publishers are advised to namespace-prefix (`acme/thing`). This is
  curation governance, never syntax enforcement.

## 5. The DAG

Decided in [The shape of the tree](../.scratch/design/issues/02-the-shape-of-the-tree.md),
pressure-tested in [The rosekube chain on paper](../.scratch/design/issues/10-the-rosekube-chain-on-paper.md).

The base structure is a **DAG of named nodes** — configurations stay mostly
chain-shaped in practice, but no distinguished parent edge exists. Names
(`infra/staging`) are the stable identity across config edits; derivation
hashes and claim addresses are the versioned identity beneath. Day-2
output speaks names.

- **Available environment**: the merged claims of a node's transitive
  predecessors, keyed by kind. A resolution-time concept only — used for
  edge inference and compatibility checks, never visible at run time.
- **Effective inputs** ([ADR 0002](adr/0002-consumed-claims-are-identity.md)):
  only the claims matching the operation's declared consumed kinds enter
  the provenance record and cache key, and the runner presents the
  operation with exactly those claims. Availability is ergonomics;
  consumption is identity; the runner enforces the boundary physically
  (§6). Pure operations receive claims only; effectful operations also
  receive whatever annotations exist locally.
- **Hybrid edges**: explicit edges are always allowed and always win;
  inference wires unambiguous consumed kinds automatically; ambiguity
  among consumed kinds is a **hard error** resolved by explicit selection
  (`use: { <kind>: <node> }`). Resolved edges land in the resolution
  document and provenance, so authoring mode never affects identity.
- **Selectors**: kind plus flat field-equality constraints
  (`tool(tool=opentofu)`), declared by the plugin, augmentable by the node.
- **The granularity principle**: *import at the granularity of independent
  change.* Because consumed claims are identity, import granularity sets
  the blast radius of every change — one secret value per source node, app
  values split from cluster values. A coarse import silently re-runs
  consumers that never depended on what changed.
- **Everything is a node.** Sources — imports of values, file trees, sops
  values, git content — are pure operations whose claims reference CAS
  content; roots are simply nodes with zero inputs. The bootstrap root is
  structurally unspecial.
- **Terminal nodes** — nodes no other node consumes — are legitimate,
  never a warning: their realization is the point (a tool on PATH for
  manual use); a sink consumed by humans rather than by the DAG.
- **Aggregators stay future.** A consumer takes exactly one claim per
  consumed selector; an explicit multi-consume declaration ("all claims of
  kind X") is a named, deliberately unopened door. Its first concrete
  knock is already known: the moment the flux-tree render needs cluster
  values *in addition to* app values, it needs two claims of one kind —
  that example, verbatim, is the trigger for reopening the discussion.

## 6. Operations and plugins

Decided in [The plugin contract](../.scratch/design/issues/06-the-plugin-contract.md),
[ADR 0004](adr/0004-plugins-are-process-claims.md). Illustrative wire
shape: [the request/outcome document asset](../.scratch/design/assets/06-wire-protocol.yaml)
(field names non-normative).

An **operation** is the unit of work a node binds; a **plugin** is the
content-addressed implementation it runs.

- **The process protocol is the contract**: a plugin is an executable —
  request document on stdin (effective inputs as claim+annotation pairs,
  node config, workspace, `prior:` where applicable, runner-resolved
  secret plaintext where declared), outcome document or structured error
  on stdout, exit code for success/failure. Never a Python-native API; a
  Python SDK is sugar. Plugins are language-agnostic and may pin their own
  runtimes (uv inline metadata). One generic `command` adapter wraps
  arbitrary commands.
- **Plugins are claims**: `kind: plugin`, content = manifest + executable
  payload in the CAS, acquired through the same DAG that installs tools,
  pinned in provenance by claim CID. Only a minimal built-in set ships
  with freckles itself to break the bootstrap circle; the freckles version
  enters provenance for built-in-produced outcomes.
- **Manifest**: `name`, `version`, `produces`, `consumes` (selectors),
  `effect: pure | effectful`, `platforms`, `entrypoint`; optional
  `requires_privilege`, `verify`; named future entrypoints `destroy` and
  `resolve` (secret references, §9). The produced-kind rule: **every
  node's produced kind is fixed at resolution time** — that is what makes
  edge inference possible. Ordinarily the manifest declares exactly one
  kind; the adapter plugins (`command`, `fetch-verify`) declare the kind
  node-supplied instead, making `kind` a mandatory field of their node
  config — still exactly one kind per node at resolution, so inference is
  unaffected. The same rule extends to `effect` for `command`
  (wire-schema ticket, 2026-08-22): an adapter wrapping an arbitrary
  script may be pure or effectful, so its node config states `effect`,
  fixed at resolution — where the purity gate needs it; `fetch-verify`
  stays pure. Node config is hashed into the derivation, so a supplied
  kind is identity like any other config — an annotation (unhashed,
  machine-local) could never carry it. For `command`, consumed selectors
  are likewise node-supplied, via the node-augmentable selector mechanism
  (§5). Claim fields beyond `kind` are convention; per-kind conventions
  are curation policy (§12). Deliberately absent: tool dependencies
  (consume tool claims instead) and config schemas (the plugin's business
  in v1).
- **Enforcement split**: the runner *physically* enforces visibility —
  isolated workspace, scrubbed environment, consumed tool claims
  materialized onto a constructed PATH, content claims as files; the
  plugin assembles nothing. Purity (determinism, no undeclared network) is
  *contract*, with an optional run-twice determinism check as catalog CI.
  No kernel sandbox in v1.
- **The sets**: built-ins — `import-values`, `import-file-tree`,
  `import-sops`, `import-git`, `fetch-verify`, `command`. Standard
  plugins — `bootstrap-mise` (default), `bootstrap-pixi` (first-class
  peer), `mise-install`, `pixi-install` (its peer — a bootstrap without
  an install analog delivers no tools), `uv-python`, `copier`.
  Catalog-level plugins
  (`tofu-apply`, `flux-bootstrap`, `git-push`, …) come with curation. The
  only true root is `fetch-verify` (§11). `import-git` is deliberately
  built-in rather than standard — a recorded amendment (2026-08-22) of
  [Where curation lives](../.scratch/design/issues/08-where-curation-lives.md),
  which first placed it standard: it lets a configuration bootstrap from
  a bare git repository, which may itself carry a bootstrap binary,
  before any plugin can be acquired. Consequence: the git fetch ships
  inside freckles itself — a host `git` dependency would defeat the tier
  (and is avoidable: pinned-commit fetch needs no full libgit2;
  pure-Python implementations cover it).

## 7. Storage and addressing

Decided in [Storage and addressing](../.scratch/design/issues/05-storage-and-addressing.md)
on the [CAS survey](../.scratch/design/issues/04-content-addressable-store-survey.md)'s
findings; [ADR 0003](adr/0003-cidv1-addressing.md).

- **Addressing**: CIDv1 + sha2-256 in every backend; spec-strict DAG-CBOR
  (codec 0x71) for documents, `raw` (0x55) for blobs capped at 1 MiB
  (larger content becomes a list-of-blocks document); base32 string form.
  Addresses are byte-identical to what Kubo assigns via `block/put`, so
  IPFS export needs no translation — though freckles never requires IPFS.
  A file tree's identity is a freckles document of (name → CID) pairs —
  deliberately no `ipfs add`/UnixFS compatibility.
- **The in/out line** — in the CAS: claims, provenance records,
  source-imported content, resolution documents. Out: annotations (local
  index keyed by claim CID), the audit log (local, append-only), the
  working-copy configuration, realized environments and other local
  state.
- **Refs are the only mutable state** and double as GC roots:
  `cfg/<config>/current` → resolution document,
  `cfg/<config>/nodes/<node>` → the node's current claim CID, and
  `cfg/<config>/prov/<node>` → the node's current provenance record
  (amendment 2026-08-25, M3: nothing else links provenance, so without
  this ref gc would collect a current claim's provenance record and
  derivation document after grace; superseded provenance loses the ref
  and ages out through grace exactly like superseded claims). The
  **derivation index** (derivation hash → claim CID) is a separate,
  prunable, rebuildable local cache — deliberately not refs, so cache
  entries never pin outcomes forever.
- **The resolution document** replaces the lockfile: a content-addressed
  snapshot of one resolved run — configuration snapshot CID, nodes with
  resolved post-inference edges, plugin + version per node, consumed-claim
  wiring. Unchanged inputs re-resolve to the same CID; day-2 diffs compare
  two resolution documents.
- **Backend interface**: `put/get/has/cids`, `set_ref/get_ref/refs`,
  `gc(extract_links, grace≈14d)`; backends are codec-ignorant. Initial
  backends: sqlite (default), folder (inspection), ipfs (thin Kubo-RPC
  adapter; refs become pins).
- **Scope**: one per-user store, refs namespaced per configuration —
  claims and the derivation cache dedup across configurations. Revisit
  per-configuration stores only if a use case earns it; the interface
  keeps that cheap.

## 8. Effects and day-2

Decided in [Effects and day-2](../.scratch/design/issues/07-effects-and-day-2.md).

- **The loop**: edit configuration → re-resolve (pure, cheap, new
  resolution document) → heal, walking the DAG in topological order: each
  node's new derivation is computed from its current input claims and
  looked up in the derivation index — a hit means current (unless the
  claim is locally distrusted — see drift below). **Source nodes are
  exempt from hit-means-current**: their derivations are content-free
  (config only, zero inputs), so the world they import can change under
  an unchanged derivation — the walk re-runs them unconditionally;
  re-import is pure and cheap, and an unchanged import re-mints the same
  claim, so the ripple stops immediately (amendment 2026-08-24, from the
  walking skeleton). A miss on a pure node
  re-derives automatically on the spot, often re-minting the same claim,
  which stops the ripple; a miss on an effectful node marks it **stale**
  and puts it in the **checkpoint set** — the stale effectful nodes, the
  only thing day-2 ever surfaces for confirmation, presented by node
  name. A stale effectful node hides its downstream until its checkpoint
  runs; the walk resumes past it afterwards (§10's delta B is the ripple
  stopping exactly there). Refs advance as nodes heal; superseded claims
  become GC-fodder after grace. "Is the deployment current?" means "is
  the checkpoint set empty?".
- **Checkpoints**: effectful nodes never run implicitly. The confirmation
  prompt names the node, the claim being superseded, plaintext secret
  names (§9), and privilege needs (`requires_privilege`) — never a silent
  sudo. Auto-confirmation is a deliberate opt-in for automation.
- **`prior:`**: an effectful re-run receives the node's previous outcome
  (claim + annotations); pure plugins never see it. Idempotency contract:
  re-running with identical effective inputs and prior must be
  side-effect-safe and should be a no-op. Convergence with the world is
  the tool's business; freckles delivers continuity.
- **Provenance and caching**: each derivation — plugin (or freckles
  version for built-ins), node config, input claim CIDs; node names
  excluded — is recorded as a content-addressed provenance record and
  keyed in the derivation index. Caching is always a provenance-keyed
  lookup; trust comes from provenance and the local trust domain, never
  from a claim's address.
- **Drift**: optional `verify` manifest entrypoint; `freckles verify` is
  explicit, never polled. Contradiction marks the claim **distrusted** in
  the local annotations index (claims stay immutable), which makes the
  node stale through the one existing staleness mechanism; re-running
  heals.
- **Teardown, v1**: removing a node orphans its effectful claim; freckles
  *reports* orphans, cleanup belongs to the operator and the underlying
  tools. An optional `destroy` entrypoint is the named future extension.
- **The audit log** succeeds the journal: local, append-only, records
  every run with derivation and claim CIDs, logs, exit codes, durations,
  failures, and resolved secret *names* — so "what was deployed when"
  stays answerable even after blocks are GC'd. Never consumed downstream.
  No history refs in v1; bounded history refs are a named cheap later
  option.
- **Machine-boundedness, stated honestly**: consuming any claim requires
  only the claim, but a node's annotations are private to the machine that
  runs it — so re-running an effectful node is bound to the machine
  holding its annotations. Moving that seat means moving tool state:
  deferred with multi-machine sharing (§12).

## 9. Secrets

Decided in [Secrets in the outcome model](../.scratch/design/issues/09-secrets-in-the-outcome-model.md);
[ADR 0005](adr/0005-plaintext-only-at-the-execution-boundary.md).

Two distinct flows, which the vision blurred into one:

- **Flow A — secrets freckles resolves**: plaintext an operation needs at
  execution time (a Proxmox API token for `tofu apply`).
- **Flow B — ciphertext as content**: sops-encrypted values embedded in
  rendered trees and decrypted by the *target* system (Flux in-cluster).
  These are ordinary bytes flowing through pure nodes; freckles never
  decrypts them, under any shape below.

The **secret claim kind is a contract admitting multiple shapes** — two
specified, the set explicitly open:

- **Value-bearing** (*secret value*; v1, via built-in `import-sops`):
  identity is the ciphertext, referenced by content hash; CAS-resident by
  default (ciphertext is publishable, per the vision's stance — with the
  note that long-horizon secrecy means keeping the store off shared
  backends). The **detached variant** (`store: false`) keeps the hash and
  therefore the rotation ripple, but the bytes never enter the CAS — the
  runner materializes them from the working copy. Rotation changes the
  ciphertext and ripples staleness to consumers — deliberately.
- **Reference-bearing** (*secret reference*; specified now, resolver
  future): identity is the **logical name alone**; which provider holds
  the value on this machine (keyring, Vault, 1Password, … — the
  secretspec model) is machine-local configuration recorded in
  annotations at resolution. Rotation is invisible to staleness; the
  verify → distrust path is the rotation story. A secretspec-backed
  acquisition plugin is the named route — a plugin, not a redesign.

Rules, independent of shape:

- **Plaintext exists only at the execution boundary** (ADR 0005): the
  runner resolves secret claims in memory and injects plaintext into the
  effectful plugin's request document; plaintext never touches disk, the
  store, provenance, or the audit log. No pure operation ever receives
  plaintext — `effect: effectful` is the gate; wiring a secret's plaintext
  into a pure plugin is a resolution-time hard error. Pure operations may
  consume and embed *ciphertext* (flow B).
- **Credentials** — access material minted by effectful operations (a
  kubeconfig, a generated password) — are never identity: they live in
  **secret-marked annotations** (`secret: true`), which freckles never
  prints and keeps owner-only. Credential rotation updates annotations
  under an unchanged claim: no downstream churn. Costs owned: credentials
  are machine-bound and unrecoverable from the store — lose the machine,
  re-mint with the underlying tool. Parking credentials in a secret
  provider (the outcome carrying a secret reference) is the named future
  transport path.
- **Key model, v1**: a single user age key, sops-compatible (honors
  `SOPS_AGE_KEY_FILE`), strictly outside the store. Key rotation
  re-encrypts values → ciphertext churn → the deliberate staleness ripple.
  Team keys and provider authentication are deferred with multi-machine
  sharing (§12).
- Plugins must not log plaintext — contract, not sandbox, matching the
  purity precedent. The audit log records resolved secret names, never
  values.

## 10. The rosekube chain, worked

The full-fidelity documents live in
[the prototype](../.scratch/design/prototype/README.md) (hand-written,
confirmed 2026-08-21; it predates the `config` → `values` kind rename
applied here). The chain that motivated the design, as nodes:

| node | operation | effect | consumes | produces (kind) |
|---|---|---|---|---|
| `bootstrap` | bootstrap-mise | pure | — | `bootstrap` |
| `tools/opentofu`, `tools/talosctl`, `tools/flux` | mise-install | pure | bootstrap | `tool` |
| `sources/values/cluster`, `sources/values/apps` | import-values | pure | — | `values` |
| `sources/secrets/proxmox-api-token`, `…/tailscale-oauth`, `…/cluster-age-key` | import-sops | pure | — | `secret` |
| `infra/staging` | tofu-apply | effectful | tool(opentofu), values *(use: cluster)*, secret *(use: proxmox)* | `talos-cluster` |
| `render/flux-tree` | render-flux-tree | pure | values *(use: apps)*, secret *(use: tailscale — ciphertext embedded)* | `file-tree` |
| `k8s/flux-bootstrap` | flux-bootstrap | effectful | talos-cluster, tool(flux), values *(use: cluster)*, secret *(use: age-key)* | `gitops` |
| `k8s/push-config` | git-push | effectful | file-tree, gitops | `gitops-synced` |

Everything the model claims shows up here concretely: the granularity
principle (three secret nodes, split values), both secret flows, the
kubeconfig as a secret-marked annotation on the `talos-cluster` claim
(reaching `flux-bootstrap` because effectful consumers receive local
annotations), `tools/talosctl` as a legitimate terminal node, and
`use:` breaking every multi-provider tie.

Two day-2 deltas, verified on paper
([full walkthrough](../.scratch/design/prototype/day2.md)):

- **Enable an app** (`karakeep: enabled`): checkpoint set = exactly
  `{k8s/push-config}`. The apps values claim and the rendered tree go
  stale too but re-derive automatically (pure); infra and flux-bootstrap
  are untouched because they never consumed the apps values — the vision's "only push is stale"
  promise, preserved *by* the granularity principle.
- **Rotate the Proxmox token**: checkpoint set = exactly
  `{infra/staging}` — the secret import re-derives automatically first.
  The checkpoint re-runs `tofu apply` with `prior:`; the cluster is unchanged,
  so the plugin returns the *same* claim — and because addressing is
  extensional (ADR 0001), downstream derivations see identical input CIDs
  and the ripple stops dead. A new provenance record simply records that
  the new derivation also produces the old claim.

## 11. Bootstrap

Decided in [Bootstrap tool evaluation](../.scratch/design/issues/03-bootstrap-tool-evaluation.md)
(research findings: `docs/research/bootstrap-tools.md` on branch
`research/bootstrap-tools`) and
[The plugin contract](../.scratch/design/issues/06-the-plugin-contract.md).

The only privileged root concept is **`fetch-verify`**: fetch a pinned URL,
verify its checksum. Its produced kind is node-supplied (§6): the
fetching node declares what the verified artifact is — a `tool`, a
`plugin`, plain content. It installs whichever bootstrap plugin a
configuration declares; everything else — including every other plugin —
arrives through the DAG itself.

The bootstrap operation is **swappable behind a common contract**:
**`bootstrap-mise` is the default** (aqua backend: upstream official
binaries, mandatory checksums, cosign/SLSA verification; covers the
devops eight — opentofu, talosctl, flux, sops, age, kubectl, helm,
copier); **`bootstrap-pixi` is a first-class peer** for solved
conda-forge library/Python stacks; `uv-python` drives the Python slice.
All are single userspace binaries, version-pinned at install, drivable
non-interactively.

## 12. Deferred

Exactly these, nothing silently:

- **Curation and catalogs** ([Where curation lives](../.scratch/design/issues/08-where-curation-lives.md)):
  the core above is complete and standalone; full catalog design —
  layering, the template format, policy composition — is its own
  follow-up effort, paired with the rosekube migration. The extension
  points are fixed now: catalog content arrives as claims via `import-git`
  (pinned by resolved commit in the claim, like all claim mechanics);
  domain kinds and per-kind field conventions live in a conventions
  document that is itself catalog content (core stays domain-agnostic);
  templates **expand** into ordinary explicit nodes at
  authoring/resolution time, so the resolution document always holds the
  expanded, inspectable DAG — dynamic DAGs (nodes producing nodes) are
  explicitly rejected. External generation (copier rendering a freckles
  configuration) is the zero-cost interim that works today.
- **Multi-machine sharing**: store sync, the IPFS backend's actual purpose
  (publication? distribution? backup?), moving an effectful node's seat
  (its annotations and tool state), team key distribution /
  multi-recipient encryption, and secret provider authentication. One
  future effort.
- **The formal specification set** (vision.md §13): follows this document
  as its own effort.
- **Implementing freckles**: this document ends at the design.

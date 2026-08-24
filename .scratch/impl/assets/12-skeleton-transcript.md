# Walking skeleton — by-hand transcript

Wayfinder ticket 12, recorded 2026-08-24. The committed example
(`examples/skeleton/`) run by hand through the hidden dev commands
(`freckles dev …` — raw dev commands, deliberately not the ratified CLI
surface). The same loop runs under the test suite in
`tests/e2e/test_skeleton_chain.py`.

```
$ freckles dev resolve examples/skeleton
resolution bafyreiabosqm7fzg2adhr6kq77css3sp2h2tr2krwqlt4hqcbq6cvr7emm
  values/apps  [pure] produces values  -
  render/site  [pure] produces file-tree  values<-values/apps
  deploy/site  [effectful] produces deployed-site  file-tree<-render/site

$ freckles dev heal examples/skeleton --yes        # day 1
checkpoint deploy/site: auto-confirmed
healed: values/apps, render/site
confirmed: deploy/site
deployment current

$ freckles dev heal examples/skeleton --yes        # steady state
current: values/apps, render/site, deploy/site
deployment current

$ sed -i "s/enabled: false/enabled: true/" examples/skeleton/cluster.yaml   # day 2

$ echo n | freckles dev heal examples/skeleton     # decline the checkpoint
checkpoint deploy/site: run it? [y/N]: healed: values/apps, render/site
checkpoint set: deploy/site
deployment NOT current

$ echo y | freckles dev heal examples/skeleton     # confirm it
checkpoint deploy/site: run it? [y/N]: current: values/apps, render/site
confirmed: deploy/site
deployment current
```

What the transcript shows, mapped to the design:

- **Day-1 = day-2 from zero** (§8): the first heal derives everything;
  the effectful node runs only as a confirmed checkpoint.
- **Steady state**: an unchanged configuration is fully current — every
  derivation hits the index (the source re-import re-mints the same
  claim, so it reports current too).
- **The checkpoint set** after the config edit is exactly
  `{deploy/site}`: the pures healed automatically, and the deployment is
  honestly "NOT current" until the checkpoint is confirmed.
- **The declined checkpoint** left the walk resumable: the next heal
  found the pures current and only the checkpoint outstanding.
- **`prior:`** reached the re-run (asserted in the E2E test: the deploy
  workspace holds `prior.json` on the re-run, not on day 1), and the
  re-run re-minted the same claim — the extensional ripple-stop, so the
  deploy ref never moved.

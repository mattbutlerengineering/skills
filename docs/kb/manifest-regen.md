---
summary: update-manifest hashes every file under factory/templates/; delete stray .orig/.rej first or they get checksum-pinned.
sources: gates.py, factory_init.py
verified: 6aacc5cde45558eacc6d8281fdef6da6ac839bb2
related: gates-scan-every-doc
---

# Regenerating the template manifest

`gates.manifest_files` is the one walk both sides use: `factory_init.py
update-manifest` writes its result to `factory/manifest.json` and
detector E diffs the manifest against it. It hashes **every** file under
`factory/templates/` except `__pycache__/`.

So a stray patch leftover — `protocol.py.orig`, `gates.py.rej` from a
`patch` or a conflicted apply — is pinned into the manifest as if it were
payload. Untracked, it is invisible to `git status` noise filters you
might rely on, and the manifest then verifies only in the checkout that
wrote it. Delete the leftovers **before** running update-manifest, not
after.

The regen is owed after any edit under `factory/templates/` and after
any edit to a root file `factory_init.MIRRORS` copies there (for example
`protocol.py`, whose `UTILITY_SKILLS` every new utility skill touches).
The manifest also records the plugin version from
`.claude-plugin/plugin.json` at regen time; nothing gates that field, so
a version bump without a regen leaves it behind silently.

---
summary: update-manifest hashes every file under factory/templates/; delete stray .orig/.rej first or they get checksum-pinned.
sources: gates.py, factory_init.py
verified: 3fe622bcf4bf2d9a53dc52fd31f59816ec8439f6
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
a version bump without a regen leaves it behind silently — and since
ADR-0099 a stamped repo reads it back (`conductor.py --version`, and the
tail of `plan`/`open`), so a stale field now misreports the payload
rather than sitting unread.

The one manifest `update-manifest` never writes is a tools-only target's
(ADR-0099): `factory_init.tools_only_manifest` derives it from the
plugin's as the subset of keys the stamp lands, marked
`"install": "tools-only"`, and `update` rewrites it. Detector E's mirror
half (`gates.mirror_problems`) stands down for that marker because no
`factory/templates/` exists there; its stamped half still checks every
listed tool in use.

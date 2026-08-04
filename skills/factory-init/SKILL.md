---
name: factory-init
description: Use when a repo needs the factory tooling stamped in or the template checksum manifest regenerated — setting up a product repo to take factory work orders (Makefile check target, gate detectors, factory config), or refreshing the manifest after any edit under the factory templates so detector E passes. Not for starting a pipeline run (that's idea or capture) and not general project scaffolding.
---

# Factory Init

Stamp the factory template payload into a product repo, or regenerate the
checksum manifest that pins the payload. The manifest is the anti-drift
anchor: detector E fails any tree whose stamped files disagree with it, so
mirrors are never hand-edited — they are re-stamped or re-generated.

## Stamp a product repo

1. From the factory repo checkout:

       python3 factory_init.py stamp <path-to-product-repo>

2. The stamp is all-or-nothing. It refuses a drifted source payload, a
   malformed manifest key, a destination resolving outside the target,
   and any existing file in the target, printing one problem line per
   refusal; resolve and re-run.
3. What lands in the target:
   - `factory/` — the pristine mirror (manifest + templates) that the
     stamped detector suite checks itself against.
   - `Makefile` — `make check` runs the detectors, their selftest, and
     the test suite; it is exactly what CI must run.
   - `.github/factory.json` — budgets, routing, WIP cap, monthly cap.
   - `tools/factory/gates.py` + `tools/factory/protocol.py` — the
     detector suite and the frontmatter seam it imports.
4. Commit the stamped files in the product repo, then run `make check`
   there and confirm it exits clean.

## Regenerate the manifest (factory repo)

After editing anything under `factory/templates/`, or changing `gates.py`
or `protocol.py` (both are mirrored into the payload):

    python3 factory_init.py update-manifest

This refreshes the tool mirrors from the repo root, recomputes every
template checksum, and rewrites `factory/manifest.json` with the plugin
name and version. Commit the manifest together with the template change —
detector E gates both locally and in CI.

## Rules

- Never hand-edit files under `factory/templates/tools/` — they are
  machine-copied from the repo root by update-manifest.
- Never hand-edit a stamped file in a product repo to "fix" drift; change
  the template at the source and re-stamp.
- The stamp never overwrites: re-initializing an already-stamped repo is
  a deliberate operation (remove the stamped files first, or reconcile by
  hand and re-run update-manifest in the factory repo).

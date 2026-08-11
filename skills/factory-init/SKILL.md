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
3. What lands in the target — `factory/manifest.json` is the authority;
   the groups are:
   - `factory/` — the pristine mirror (manifest + templates) that the
     stamped detector suite checks itself against.
   - `Makefile` — `make check` runs the detectors, their selftest, and
     the test suite; it is exactly what CI must run.
   - `.github/factory.json` — budgets, routing, WIP cap, monthly cap.
   - `.github/workflows/` — the validator, assembler, design,
     cost-report, and gate-digest workflows.
   - `.github/labels.json` + `.github/CODEOWNERS` — the label taxonomy
     and the code-owner gate.
   - `tools/factory/` — the detector suite and the tools the workflows
     call through `make`.
   - `docs/adr/` — the seeded ADR set recording what stamping decided for
     the repo, plus the ADR convention and template.
   - `docs/design/` — the design-system seed and its template.
4. Commit the stamped files in the product repo, then run `make check`
   there and confirm it exits clean. Two things to fix first, or the
   first run is confusing:
   - the target needs a `tests/` directory — `make check` runs
     `unittest discover -q tests` and errors without one;
   - `.github/CODEOWNERS` ships a placeholder owner handle. If it is not
     a collaborator on the target, GitHub ignores the entry and the
     code-owner gate goes inert.

## Refresh an already-stamped repo

A stamp is a snapshot. When the factory gains a fix — a new detector, a new
lifecycle target — an already-stamped repo needs it too, and `stamp` refuses
every existing file:

    python3 factory_init.py update <path-to-product-repo>

It splits the payload where detector E does:

- **Overwritten** — `tools/factory/`, `.github/workflows/`, and the
  `factory/` mirror. Never meant to be hand-edited; detector E fails the
  build if they are, so restoring them from the payload is the remedy, not
  a loss.
- **Created only when absent** — the `Makefile`, `.github/factory.json`,
  `.github/labels.json`, `.github/CODEOWNERS`, and the `docs/` seeds. A seed
  the repo does not have yet lands; one it has is the repo's. Each kept file
  that differs from the payload is reported so you can reconcile it
  deliberately.

It refuses a tree that was never stamped rather than quietly becoming a first
stamp.

**Read the make-target report.** The workflows are overwritten and they call
only `make` targets, so a factory change that adds a target leaves a repo
whose refreshed workflow calls one its Makefile has never heard of. `update`
reports exactly that, and it is the one thing to fix before the next CI run:

    factory-init: workflows call `make wo-failed` but the Makefile has no
    wo-failed target (add it, or re-stamp the Makefile)

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
  the template at the source and re-stamp. Detector E fails the build on a
  hand-edited executable payload, and `update` is how you put it back.
- The stamp never overwrites. Refreshing an already-stamped repo is
  `update`, not a second `stamp`.

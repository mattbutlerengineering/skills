---
stage: ship
run: maintenance:a-config-the-gate-cannot-read
date: 2026-08-27
assumptions: ["the autorun brief carries no release authorization, so
  ship prepares and stops"]
---

# Release: a config the gate cannot read

**Prepared, not executed.** No release authorization exists for this
run. No pull request was opened; nothing merged, tagged or published.

## Pre-flight

- Verification green, five criteria — four PASS and one recorded as an
  open, unfixed finding rather than verified away.
- No unfixed CRITICAL findings. `review.md` carries one major, open,
  with its blocker (PR #320) named.
- No secrets in the diff; no configuration added; no network call.
- No migration. No config file is rewritten; the change only alters what
  happens when one cannot be read.
- Both edited modules are mirrored, so `update-manifest` ran and
  `factory/manifest.json` is committed with the change.

## Rollback

```
git revert <sha> && python3 factory_init.py update-manifest
```

Or before merge:

```
git push origin --delete agent/a-config-the-gate-cannot-read
```

## Blocking condition

ADR-0036 clause 2: a non-authoring reviewer must re-execute the
verification and record it on the pull request.

## Remaining steps for a human

1. Open a pull request from `agent/a-config-the-gate-cannot-read`.
2. Non-authoring reviewer re-runs the battery and records it on the PR.
3. Merge; resolve any `factory/manifest.json` conflict by re-running
   update-manifest, never by hand.
4. Separately: schedule the detector-F half once PR #320 lands.

Held out of the 17-PR queue for the same reason as the previous five.

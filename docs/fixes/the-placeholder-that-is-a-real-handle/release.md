---
stage: ship
run: maintenance:the-placeholder-that-is-a-real-handle
date: 2026-08-28
assumptions: []
---

# Release

**Prepared, not executed.** The brief authorises no release. This artifact
records readiness and the exact remaining steps.

## Scale

Scoped fix (protocol Run scale): one transform, its payload twin, one
manifest checksum, ten tests, one backlog seed claimed. Full pre-flight
was run anyway because the change alters what every future stamped repo
is handed.

## Pre-flight

| Check | Result |
|---|---|
| Verification green | `verification.md`, nine criteria, no failures |
| Full battery | 1354 tests OK; `lint: 0`; `gates: 0`; `selftest: ok` |
| Free pre-pass | `one-owner: 9 problem(s)` — unchanged from `origin/main` |
| Secrets in the diff | none; the change *removes* a real GitHub handle from a distributed artifact |
| Configuration in the target environment | none required; no workflow, secret, variable or label is added or read |
| Migrations / data changes | none |
| Manifest regenerated | `python3 factory_init.py update-manifest`, one checksum moved |
| Stamped-repo smoke check | fresh stamp → `gates: 0 problem(s)`, no owner leak anywhere in the tree |
| Unfixed critical review findings | none (Finding 1 fixed in-run; 4 and 5 deferred with reasons) |

## Rollback plan

The change is one commit on one branch, not yet on `main`.

- Before merge: nothing to undo. Close the PR and delete the branch.
- After merge: `git revert <merge-sha>` on `main`, then
  `python3 factory_init.py update-manifest` to confirm the payload
  regenerates to the pre-change bytes (it will — the transform is the only
  input that changed), and commit if the manifest moves.
- Already-stamped repos need nothing either way: `update` never overwrites
  an existing `.github/CODEOWNERS`, so no stamped repo's file is touched
  by landing or reverting this.

## Remaining steps (not executed)

1. Push `agent/the-placeholder-that-is-a-real-handle`; open a PR citing
   the claimed backlog seed.
2. **Blocked on ADR-0036 clause 2** — an independent, non-authoring
   reviewer must re-execute this run's verification and record it on the
   PR. This run authored the change and may not review it.
3. Merge is the human's. The PR does not touch `docs/adr/**`, so it is
   not itself a gate change; the clause-2 requirement is what holds it.
4. Follow-up, separate PR, human gate 2: an amending ADR for ADR-0050,
   whose Decision text still lists `.github/CODEOWNERS` among the
   `identity` mirrors (review Finding 4).

## Post-release

Not applicable — nothing was released. The stamped-repo smoke check in
pre-flight is the evidence that would otherwise be gathered here: a fresh
stamp from this commit produces a target whose own detectors pass and
whose CODEOWNERS names no real account.

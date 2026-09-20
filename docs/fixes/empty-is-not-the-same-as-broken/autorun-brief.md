---
run: maintenance:empty-is-not-the-same-as-broken
date: 2026-08-25
origin: docs/backlog.md seed 40 (from: maintenance:toolsmith-mine-pr-permissions)
---

# Autorun brief

## What and why

The toolsmith queue issue renders **byte-identically** whether the
change-request stream was read and found empty or the listing failed. The
failure is recorded — in the CLI's problem list, which reaches the workflow
log — but the artifact a human actually reads says nothing. That shape is
what hid the mine's permission defect for its whole life, and the grant was
fixed without fixing the tell.

## Run scale

Maintenance, scoped fix. `re-entry: architect` — the change is small but it
decides what the queue body is *for* (a harvest, or a harvest plus its
provenance), so the architecture and breakdown legs run.

## Scope

**In:** what `compose_queue` says about the streams it was given, and the
wiring that tells it. Both streams, not only the one the seed names — the
timeline harvest is blind in exactly the same way and the mechanism is
shared. Widening is recorded as a deliberate scope call in
`architecture.md`, not smuggled.

**Out:** the permission grant itself (already fixed), the mine's schedule,
the queue's ranking, and every other "0 things happened" line in the repo —
`sweeps: 0 issue(s) filed` is the same class and belongs to its own run.

## Success criteria

- A failed change-request listing and an empty one produce **different**
  queue bodies, and the difference names the stream that failed.
- A reader of the queue issue can tell a healthy empty harvest from a
  partial one without opening the workflow log.
- The problem list is unchanged: the CLI still reports the failure exactly
  as it does today. The body gains a statement; it does not become a second
  owner of the problem strings.
- The battery stays green: unittest, `lint.py`, `gates.py`, `--selftest`.

## Constraints already decided

- **Stdlib only.**
- `rejection_mining.py` **is** in `factory_init.MIRRORS`: the payload copy
  and `factory/manifest.json` move in the same commit
  (`python3 factory_init.py update-manifest`).
- **No stage may run `python3 rejection_mining.py mine`**, or any mode that
  creates, edits, or pins a live issue. Read-only `gh` reads and offline
  fixtures only. Issue #294 is permanent marker-bearing state.
- Never fabricate run, eval or ledger evidence.
- Work in an isolated worktree: another session is driving the primary
  checkout on a different branch.

## Release authorization

**None.** Prepare-and-stop: pre-flight, open the PR, write `release.md`,
stop. No merge, no tag, no publish. ADR-0036 clause 2 independently forbids
the author merging.

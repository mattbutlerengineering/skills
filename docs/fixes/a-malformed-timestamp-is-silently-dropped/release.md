---
stage: ship
run: maintenance:a-malformed-timestamp-is-silently-dropped
date: 2026-09-20
---

# Release: PR opened, merge left to the human gate

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, six PASS sections plus a disclosed not-fixed row and a not-verified section |
| Full suite | `Ran 1626 tests` OK (1617 on `origin/main` + 9 new) |
| `lint.py` | `lint: 0 problem(s) across 24 skills` |
| `gates.py` | `gates: 0 problem(s)`; `--selftest: ok` |
| `one_owner.py` | 7 problems, identical to `main` |
| Regression reproduced red-then-green | Yes — 9 new tests confirmed failing against `8e074d0` before the fix, passing after (`verification.md` §2–3) |
| Change size | one private walk + one public function in `human_gates.py`, one conditional `problems.append` in each of `gate_digest.py`'s `_timelines` and `dashboard.py`'s `_timeline`, no signature or return-shape change for any existing caller |
| Mirrored files touched | `human_gates.py`, `gate_digest.py` — `update-manifest` ran (`factory-init: 0 problem(s)`), payload copies and `factory/manifest.json` committed |
| Rollback plan | Below |

## Blockers on merge

1. **ADR-0036 clause 2** — the review is self-authored.
2. **Merge is gate 3** (ADR-0033), the repo owner's call. Not taken here.

## Behavior change to flag at merge

A `gate-digest.yml` run that hits a refused timestamp now exits nonzero
(`cli.report` returns 1 whenever `problems` is non-empty) where it
previously exited 0 with an empty `problems` list — see `review.md`,
Residual risk. The digest still posts either way; only the workflow
step's pass/fail state moves. This is the fix issue #491 asked for, not
a side effect, but it means a stamped repo's `gate-digest` job can go
from green to red the first time this fires, the same way it already
does for a failed per-issue timeline fetch.

## Contention

`factory/manifest.json` is touched, so this conflicts with any other run
that regenerates the manifest. Resolution is the standard one: take both
branch sides for the source files, then re-run
`python3 factory_init.py update-manifest` and commit the regenerated
manifest rather than hand-merging its hashes.

PR #490 (open, docs-only, no code changes) touches no file this run
touches — it lands `docs/fixes/a-timestamp-the-digest-cannot-parse/*.md`
only. No other open PR touches `human_gates.py`, `gate_digest.py` or
`dashboard.py`.

## Rollback

Revert the single commit and re-run `update-manifest`. Every change is
additive (a new function, two new conditional problem-string appends);
reverting restores exactly #326's shipped behavior — the silent drop
issue #491 reports — and the 9 new tests fail again. Nothing else depends
on the new problem strings or the new nonzero exit path.

## Follow-up recorded, not actioned

1. **`rejection_mining.py`** stays silent about a refused timestamp the
   same way (`verification.md`, *Not fixed*). Not costing it anything
   observable today (it never reaches `waited_seconds`); the same
   `refused_timestamps` call is one line to add there if a future caller
   of `gate_rejections` starts to need it.
2. **No live occurrence has ever been observed** against real GitHub
   data (`verification.md`, *Not verified*), matching #326's own
   defect.md. Nothing in this run changes that risk profile; it only
   changes what happens the day it does occur.

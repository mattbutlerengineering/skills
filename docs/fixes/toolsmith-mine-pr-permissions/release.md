---
stage: ship
run: maintenance:toolsmith-mine-pr-permissions
date: 2026-08-18
assumptions:
  - "This artifact was written by the orchestrator, not by the Ship subagent. That agent pushed, opened PR #303, merged it, closed #297 and dispatched the workflow, then died to an API error before writing release.md. Every fact below was re-derived from git, gh and the run logs after the fact rather than taken from the agent's narration, and the two things only it could have known — whether it retried anything, and what it read before acting — are recorded as unknown rather than guessed."
  - "'production' for this repo is main: the plugin is vended from the repo and the factory payload is stamped into product repos from factory/templates. There is no deploy step and no version tag — the project has never tagged a release, so shipping is a squash merge to main. Same reading as the deepening-cli-seams and deepening-tool-seams runs."
  - "CI is recorded as green on the pre-merge check and RED on the post-merge merged-label job. The brief made green CI non-waivable, which taken literally would block a merge that had already happened; the merged-label failure is shown below to be pre-existing and to affect every non-work-order PR this repo merges, so it is recorded as an inherited condition and seeded, not as this run's failure. That reading is mine."
  - "PR #298 was left open and untouched. It is a duplicate of this fix, opened by the daily improvement routine two days before this run started, and closing it is an outward-facing action on a PR this run did not open — the operator's call, surfaced rather than taken."
---

# Release: the toolsmith-mine-pr-permissions maintenance run (PR #303)

## Pre-flight

- [x] **Verification green.** `verification.md` records 7 PASS, 0 FAIL,
      2 NOT RUN. The two NOT RUN are the live check and the standing
      "defect resolved" criterion — both of which this stage's dispatch
      settles, below.
- [x] **Review has no unfixed critical.** `review.md` records 1 critical,
      0 major, 2 minor. The critical — `verification.md` tripping
      detector H three times, so the branch did not pass its own battery
      — was fixed in `a69b370` along with one minor; two minors were
      deferred with reasons.
- [x] **No secrets in the diff.** The change grants a token *scope*; no
      credential value appears anywhere in `git diff`.
- [x] **Payload mirror coherent.** Root and payload workflows are
      byte-identical (`cmp` silent), and `factory/manifest.json` carries
      the regenerated checksum.
- [x] **No migrations, and the ledger is untouched.**
      `git log 1573285..73b9d05 -- docs/factory/costs.jsonl` returns no
      commits.
- [x] **Rollback plan.** One squash commit on main:

      git revert 73b9d05 && git push

      That undoes the grant, the payload twin, the manifest checksum and
      the regression test together — the tree returns to `1573285`'s
      behavior and the harvest goes back to failing its `gh pr list`
      call. It does **not** undo the dispatched run's tracker side
      effects: issue #294's body was rewritten by the 2026-08-19 harvest
      and stays rewritten. Nothing about that needs undoing — it is the
      workflow doing its job — but a revert is not a time machine for it.

## Release

| Step | Result |
|---|---|
| Push | branch `toolsmith-mine-pr-permissions`, 4 commits |
| PR | **#303** — https://github.com/mattbutlerengineering/skills/pull/303, `Closes #297` |
| Pre-merge CI | `check` **pass**, 22s, run `32219001427` |
| Merge | squash, **`73b9d05`**, 2026-08-19T05:21Z |
| Intake issue | **#297 CLOSED** at 2026-08-19T05:21:30Z by the merge |
| Post-merge CI | `merged-label` **fail** — see below |

### The post-merge job that failed, and why it is not this run's

The validator's `merged-label` job (run `32219119693`) failed:

```
python3 validator.py lifecycle --label wo:merged
V: PR body cites no work-order id
validator: 1 problem(s)
make: *** [Makefile:40: wo-merged] Error 1
```

That job exists to flip a mirrored work order to `wo:merged`. This PR is
not a work order — it is a maintenance run's PR, and it cites no
`WO-####` id because no such id exists for it.

**It is pre-existing and it is not rare.** The identical failure occurred
on PR #302's merge yesterday (run `32212716025`, `merged-label`
failure), a different run touching entirely different files. Every
non-work-order PR this repo merges trips it. Yesterday's release record
called CI "green on the first run", which was true of the pre-merge
`check` and missed this job — so this is also a correction to that
record, not only an observation about this one.

Seeded rather than fixed here: the run's brief forbids widening, and the
fix is a design question (should `lifecycle --label` treat "no work
order cited" as a no-op rather than a problem, or should the job's `if:`
condition exclude PRs with no `wo:` label?).

## Post-release — the check that actually proves the fix

The whole point of this run. `gh workflow run toolsmith-mine.yml` against
the merged commit:

- Run **`32219180419`**, event `workflow_dispatch`, head `73b9d05`,
  concluded **success** in 40 seconds (05:22:32 → 05:23:12Z).

The full output of the mine step:

```
python3 rejection_mining.py mine
rm: 32 candidate WO(s), 32 correction(s) mined
rejection_mining: 0 problem(s)
```

**The criterion is met.** `rm: gh pr list failed:` does not appear. The
2026-08-17 run printed it; this one does not, and the only change
between them is the grant.

### Every problem that remains, and whose it is

**None.** `rejection_mining: 0 problem(s)`, down from `2 problem(s)` on
2026-08-17. Both of that run's problems are gone:

1. `rm: gh pr list failed: …` — **this run's fix.**
2. `rm: gh issue pin failed: Maximum 3 pinned issues …` — gone for a
   different reason, exactly as predicted below.

### The two competing predictions — `defect.md` was right

`autorun-brief.md` predicted the pin error would recur, taking the run
from 2 problems to 1 and leaving it red. `defect.md` disagreed:
`_post_queue`'s **edit** path swallows a pin refusal
(`rejection_mining.py:176-180`, `except GH_FAILURES: pass`) where the
**create** path reports it, and issue #294 now exists with a
marker-headed body, so `run_mine`'s lookup takes the edit path.

`defect.md` held. The run took the edit path, updated #294 in place
(body timestamped `2026-08-19`, updated 05:23:06Z), reported no pin
problem, and concluded green.

**The pin cap is unchanged and still the operator's call.** #294 is
still not pinned; #172, #178 and #181 still hold the three slots. The
harvest now fails to pin *silently* every week, which is the honest
reading of "0 problems" and the reason this stays surfaced rather than
closed.

### What green does not prove

`review.md` established, read-only, that there are currently **zero
`CHANGES_REQUESTED` reviews across 137 PRs**. So the harvest listed PRs
successfully and found nothing to mine from them — the queue issue's
content comes entirely from gate rejections, as it did before. The
absence of the failure line is the whole signal; a populated
change-request section is not available as evidence today, and will not
be until some PR actually receives a change request.

`pull-requests: read` is therefore proven **sufficient for the call** —
`gh pr list` returned a 137-PR listing rather than a refusal — and
unproven for nothing that remains.

## Post-release battery, on merged `main`

```
Ran 1272 tests in 16.062s
OK
lint: 0 problem(s) across 23 skills
gates: 0 problem(s)
selftest: ok
```

## What went wrong

1. **The Ship subagent died mid-stage.** It completed every external
   action — push, PR #303, merge, #297 closed, workflow dispatched — and
   then hit an API connection error immediately before writing this
   file. Nothing was left half-done in the repo or the tracker; the
   damage was to the record, not the release. This artifact was
   reconstructed from git, `gh` and the run logs, which is why its first
   assumption says so.

2. **This run duplicated work that was already open.** PR **#298**
   ("fix(factory): toolsmith-mine.yml grants pull-requests:read", branch
   `routine/2026-08-17-toolsmith-mine-pr-read`) was opened by the daily
   improvement routine on 2026-08-17T11:53Z — before this run existed —
   and carries the *same one-line grant*, the same regenerated payload
   and manifest, a near-identical regression test, and the same
   `Closes #297`. Nobody looked for open PRs before starting; the run
   discovery only listed open *issues*.

   The fix that shipped is materially identical to #298's. The only
   difference worth naming: #298 asserts the whole four-line block as one
   string; what shipped extracts the block's body via a `permissions()`
   helper and asserts into it, which also catches a grant relocated to a
   job-level block. #298 is now redundant and its `Closes #297` target is
   already closed. **It was left open and untouched** — closing another
   author's PR is the operator's call.

## Outcome

The weekly toolsmith harvest works. It had one scheduled run in its life
and that run failed; the next one it had, it passed, with the specific
refusal gone and no problems of any kind. The defect `defect.md`
describes is resolved, and the two criteria `verification.md` recorded
as NOT RUN are now settled by the evidence above.

Three things are carried forward rather than closed: the pin cap (an
operator console call), the `merged-label` job's failure on every
non-work-order PR (seeded), and the process gap that let this run
duplicate an open PR (seeded).

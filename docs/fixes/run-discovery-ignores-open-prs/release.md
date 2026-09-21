---
stage: ship
run: maintenance:run-discovery-ignores-open-prs
date: 2026-08-25
assumptions:
  - "Prepare-and-stop, per the run brief's release authorization: `None. Prepare-and-stop: pre-flight, open the PR, write release.md, stop.` The PR is open and green; the merge is a human's."
  - "The release mechanism is the merge to `main` itself. Nothing here is mirrored, versioned, or published, so there is no tag and no payload step — the merge is the whole release."
---

# Release: ask before starting

## Pre-flight

- [x] **Verification green.** `verification.md` C1–C7, all PASS, re-run at
      the tip after Review sent the run back to Implement.
- [x] **No secrets in diff; target config present.** The run's whole diff
      scanned for token, key and credential patterns — no hits. The change
      needs no configuration at all: no environment variable, no workflow
      permission, no credential, and no new external call. The one command
      it implies an agent will run is deliberately unnamed in the skill
      bodies, because naming it there is what the protocol forbids.
- [x] **Migrations/data changes have a tested forward path.** None, and
      not in a hand-waving sense: nothing in this change writes anywhere.
      No artifact gains a field, no frontmatter key is added, `protocol.py`
      is not in the diff, and the orientation tables are untouched — C3.
- [x] **Rollback plan concrete.** Below.
- [x] **Footprint is what the design claimed.** Nothing under
      `factory/`, no workflow, no `Makefile`, no `CODEOWNERS` — so no
      `factory_init.py update-manifest` and no manifest line. Checked
      against `factory_init.MIRRORS` with a `git diff --name-only` filter
      rather than remembered.

**One thing the pre-flight caught and could not explain.** The first full
battery run of this stage failed with one test — on a run that took 26.5s
against a 15.5s norm — and the failing test's identity was not captured
before the output scrolled. Eight subsequent runs pass, five sequential
and three concurrent under self-induced load, all 1349 tests. Recorded
here rather than resolved, because "it passed on retry" is exactly how a
real flake gets lost, and because a clean-looking release log that omits
the retry is a lie to the next release.

## Rollback plan

```
# From a checkout of main, after the merge:
git revert --no-edit <merge-sha>          # or, if squash-merged:
git revert --no-edit <squash-sha>

# Nothing mirrored moves and no manifest is pinned to any of it, so there
# is nothing to regenerate. Confirm rather than assume:
python3 lint.py                           # expect: lint: 0 problem(s) across 24 skills
python3 -m unittest discover tests        # expect: OK
python3 gates.py                          # expect: gates: 0 problem(s)
git status --porcelain                    # expect: empty
```

There is no live state to unwind. The change is one protocol section, two
skill steps, one checker and its tests; reverting it removes a rule and a
pin and returns the pipeline to asking nothing.

## Release log

1. `git push -u origin agent/discovery-ignores-open-prs` → 11 commits,
   branch created remotely.
2. `gh pr create --base main --body-file …` → **PR #345** opened.
   `gh pr create`, not `gh pr edit`, which is unusable on this repo — it
   fails on the deprecated Projects-classic GraphQL field and leaves the
   body unchanged while looking like a warning.
3. Waited for CI on the PR event. Green on the first attempt:

   ```
   check                 SUCCESS
   review                SUCCESS
   needs-review-label    SUCCESS
   merged-label          SKIPPED
   ```

   `needs-review-label` is the job that cannot be pre-flighted locally —
   `gates.py` skips detector B without a PR event payload — so this is the
   first real evidence that the body's `No work order:` waiver plus
   `Closes #344` satisfies it. No body rewrite and no close/reopen was
   needed.

   As on the previous run, `gh pr checks 345` will stop showing that
   `SUCCESS` if anything is pushed to the branch: the job runs only on
   `opened`/`reopened`, and the tool displays the latest run per workflow.
   A later `SKIPPED` there is a job that did not re-run, not one that
   failed.
4. `gh pr view 345` → `OPEN MERGEABLE CLEAN`.
5. **Stopped here.** No merge, no tag, no publish.

## Post-release checks

Not applicable yet, and deliberately not invented: nothing has shipped.
What will apply once a human merges:

- The next run started in this repo — by any agent, including the daily
  improvement routine — reaches `capture` step 3 or `idea` step 3 and
  reports one of the three outcomes. That is the first time the rule runs
  as written rather than as this session ran it by hand.
- `#344` closes automatically on merge via `Closes #344`.
- The seed at `docs/backlog.md` line 29 stays claimed; nothing un-claims
  it, because the file is append-only and the claim suffix is the one
  sanctioned in-place edit.

## Outcome

**Prepared, not shipped.** The run brief authorizes no release action, and
ADR-0036 clause 2 independently forbids the author merging: a non-authoring
reviewer must re-execute the verification and record it on the PR. Both
findings in `review.md` were found by the author, including the major one
that sent the run back to Implement — which is the situation that clause
exists for.

There is a second reason to stop here, and this run is the one entitled to
say it. `gh pr list --state open` now returns **13**: #320, #322, #324,
#326, #328, #330, #333, #335, #337, #339, #341, #343 and this one, every
one agent-authored and every one waiting on the same clause. This run
exists because a queue of two was deep enough to make an agent rebuild
work that was already finished. The queue is the constraint on this
pipeline, and it is now six times deeper than the depth that caused the
defect this run just fixed.

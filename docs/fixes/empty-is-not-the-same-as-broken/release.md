---
stage: ship
run: maintenance:empty-is-not-the-same-as-broken
date: 2026-08-25
assumptions: ["Prepare-and-stop, per the run brief's release authorization: `None. Prepare-and-stop: pre-flight, open the PR, write release.md, stop.` The PR is open and green; the merge is a human's.", "The release mechanism for this repo is the merge to `main` itself — there is no deploy, tag, or publish step for a root tool. The payload copy ships with the same merge because it is checksum-pinned in the same commits."]
---

# Release: the queue body says what the harvest could read

## Pre-flight

- [x] **Verification green.** `verification.md` C1–C7, all PASS, re-run at
      the tip after Review sent the run back to Implement. No unresolved
      failures.
- [x] **No secrets in diff; target config present.** The run's whole diff
      scanned for token, key, and credential patterns — no hits. The change
      adds no environment variable, no workflow permission, and no new
      external call: it reads the same two listings through the same seam
      and writes one more line into a body the tool already posted.
- [x] **Migrations/data changes have a tested forward path.** None, in the
      strict sense. The one piece of live state is the pinned queue issue's
      body, which the harvest regenerates *whole* on every run — so the
      next weekly mine overwrites it into the new shape without a migration,
      and a revert overwrites it back. Idempotent in both directions, which
      is the existing upsert contract, not something this run added.
- [x] **Rollback plan concrete.** Below.

## Rollback plan

```
# From a checkout of main, after the merge:
git revert --no-edit <merge-sha>          # or, if squash-merged:
git revert --no-edit <squash-sha>

# Each code commit carries its own manifest regeneration, so the payload
# copy and its checksum move back together. Confirm, don't assume:
python3 factory_init.py update-manifest   # expect: factory-init: 0 problem(s)
git status --porcelain                    # expect: empty — nothing left to regenerate
python3 gates.py                          # expect: gates: 0 problem(s)  (detector E)
python3 -m unittest discover tests        # expect: OK
```

No state to unwind beyond the tree: the next scheduled harvest rewrites the
queue body from whatever code is on `main`.

## Release log

1. `git push -u origin agent/toolsmith-empty-vs-failed` → pushed 9 commits,
   branch created remotely.
2. `gh pr create --base main --body-file …` → **PR #343** opened.
   `gh pr create` was used rather than `gh pr edit`, which is unusable on
   this repo (it fails on the deprecated Projects-classic GraphQL field and
   leaves the body unchanged while looking like a warning).
3. Waited for CI on the PR event. All jobs green:

   ```
   check                 SUCCESS
   review                SUCCESS
   needs-review-label    SUCCESS
   merged-label          SKIPPED
   ```

   `needs-review-label` is the one that cannot be pre-flighted locally —
   `gates.py` skips detector B without a PR event payload — so this is the
   first real evidence that the body's `No work order:` waiver plus
   `Closes #342` satisfies it. It does, on the first attempt: no body
   rewrite and no close/reopen was needed, unlike the previous run.

   Read this line for what it is, because `gh pr checks 343` will not show
   it. That job runs only on `opened`/`reopened`, so the two artifact
   commits pushed after it report `SKIPPED` and the tool displays the
   latest run per workflow. The `SUCCESS` above is from the `opened` event,
   against the body that is still the body — nothing has edited it since.
   A reader who checks today and sees `SKIPPED` is seeing a job that did
   not re-run, not one that failed.
4. `gh pr view 343` → `OPEN MERGEABLE CLEAN`.
5. **Stopped here.** No merge, no tag, no publish.

## Post-release checks

Not applicable yet, and deliberately not faked: nothing has shipped. The
checks that *will* apply once a human merges, recorded so they are not
invented later:

- The next weekly `toolsmith-mine` run posts a body whose first content
  line begins `Sources:` — the first time the line renders on GitHub rather
  than in a test's captured argument. This is Verify's largest open gap.
- Issue #294 keeps its marker and its pin through that update (the edit
  path re-pins and tolerates a refusal).
- `#342` closes automatically on merge via `Closes #342`.

## Outcome

**Prepared, not shipped** — the run brief authorizes no release action, and
ADR-0036 clause 2 independently forbids the author merging: a non-authoring
reviewer must re-execute the verification and record it on the PR. Every
finding in `review.md` was found by the author, including the major one
that sent the run back to Implement, which is exactly the situation that
clause exists for.

PR #343 is open, green, and `MERGEABLE CLEAN`. Counted rather than
estimated: `gh pr list --state open` returns **12**, all agent-authored and
all waiting on that clause — #320, #322, #324, #326, #328, #330, #333,
#335, #337, #339, #341, and this one. The queue is the constraint on this
pipeline, not the work.

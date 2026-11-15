# The gate, per PR: steps 1 to 5

Moved verbatim from [SKILL.md](../SKILL.md), which links here from the step
that needs it. A phrase such as "this file", "above", "below" or
"the Rules" can name SKILL.md or a part of it.

1. **Head and CI.** Record the PR's head SHA once, here: `gh pr view <N> --json
   headRefOid`, or REST `gh api repos/{owner}/{repo}/pulls/<N> --jq
   .head.sha`, or MCP `pull_request_read`. That SHA is the gated head,
   the recorded head, and every later step uses it: the checks below,
   the fast-path classification, the `changed-files` list, the
   reviewer's worktree, the verdict comment and the `merge-command`.
   Read the PR's head again before the review is dispatched, before the
   verdict comment and immediately before the merge; if it differs from
   the recorded head, the gate restarts from step 1 on the new head and
   nothing recorded for the old one counts. The gate restarts at most
   once per run for a PR: a head that moves again is reported as **head
   moved** and the gate ends there, with nothing merged; the next run
   gates the PR from step 1. Run the `ci-status` hook.
   With a `required_check`, green
   means that check is **present and successful**. A rollup with no
   failures and no pending checks is not green when the required check
   never ran: treat a missing check as its own state, re-trigger CI once
   if the repo's hook says how, and never enqueue on it. Pending CI does
   not stop steps 2 to 4: the review needs the recorded head, not CI's
   result, so it may be dispatched while the check is pending. Steps 2
   and 3 are still decided before any reviewer is dispatched, so a held
   PR and a fast-path PR get no reviewer. Nothing merges and nothing is
   enqueued until this step's CI rule reads green (read again at the
   recorded head) and step 5 passes or the fast path applies. Red CI
   after a `pass` never merges.
2. **Holds.** A `hold_labels` label on the PR or its issue ends the gate
   here: no review, no merge.
3. **Fast path.** If the `fast-path` hook says the diff at the recorded
   head is low-risk
   **and** no specialist reviewer matches it, skip step 4. That
   classification counts as the review for the Merge policy (ADR-0088). If the hook
   cannot prove its own inputs are current (a stale build, an unreadable
   classifier), fail closed: review the PR and dispatch every specialist.
   A head that moved since step 1 is not an unproven input: the gate
   restarts from step 1 on the new head, as step 1 says.
   When the fast path applies, post a fast-path comment on the PR, after
   reading its head again as step 1 does before the verdict comment:
   its first line is the line the hook printed, verbatim (`fast-path:
   low-risk`), and its second line is `Head: <sha>`, the recorded head.
   It is the PR's record of why it merges without a reviewer, and the
   gated head a later session reads (Phase 3 step 1). It is never a
   verdict: it carries no score, and step 4's re-review detection keys
   only on a `reviewer-verdict: flag` first line, so a PR that leaves
   the fast path gets a first review.
4. **Review.** When Phase 0's profile check found no `verdict` hook, no
   verdict can be derived and a review could not lead to a merge, so
   for a PR that is not on the fast path (step 3) this step does not
   run: dispatch no reviewer, report the PR as unreviewed and held for a
   human, and go to step 5, whose `no verdict hook` comment is its
   record. That PR never merges, under any `merge` setting; the human
   merging can request a review. A fast-path PR is unaffected: the
   fast path stays open, its classification is the Owner's written
   review (ADR-0088), and under `merge: auto` it can still merge. Otherwise dispatch the universal reviewer, plus each specialist
   the `reviewers` hook matches to the changed files, with the input
   [the reviewer contract](reviewer-contract.md) defines. A
   reviewer is never the PR's author. When the PR already carries a
   verdict comment from this queue whose first line is a
   `reviewer-verdict: flag` line (read by the comment rule of Phase 3
   step 1), the universal review is a re-review: also hand the reviewer
   `priorIssues` (that comment's issues), `priorHeadSha` (its `Head:`
   line) and `fixDiff`, as the contract's Re-review section defines. A
   prior comment that cannot be read, or that has no `Head:` line,
   makes it a first review. Specialists are dispatched as on a first
   review.
   - Dispatch each reviewer into its own detached worktree at the
     recorded head (`git worktree add --detach <path> <head-sha>`,
     `<head-sha>` being the recorded head), never into
     the shared checkout, and never let it switch that checkout's
     branch. A reviewer with no worktree reads through the API and
     cannot run code. Remove the worktree (`git worktree remove
     <path>`) once the review is recorded.
   - Snapshot `git status --porcelain`, the current branch and `HEAD`
     before each reviewer dispatch and compare all three afterwards.
     The snapshot detects a change, it does not prevent one. A reviewer
     that changed the checkout has produced an invalid review: restore
     it by the procedure in
     [the reviewer contract](reviewer-contract.md), then
     re-dispatch.
   - A review that timed out or errored is recorded as `error`, never as
     `pass`.
5. **Verdict.** Run the `verdict` hook on the universal reviewer's
   `score`, passed as one quoted argument and only after it reads as a
   usable score, a bare finite number from 0 to 10 (the score is the
   reviewer's text, never a shell fragment; a score that fails the check
   never reaches the hook), and act on its exit code only: the reviewer is handed no pass
   line and returns no verdict, and a `verdict` it returns anyway is
   ignored whichever way it points. Exit 0 is `pass`, exit 1 is `flag`.
   Anything else is `error`, and the cause sets the remedy. A
   reviewer-side error (the review timed out, or the reviewer's score is
   not usable) gets one re-dispatch of the reviewer, then holds
   the PR for a human. A hook-side error (a missing hook, a hook that
   did not run, or any exit code other than 0 or 1 on a usable score: a
   wrong argument count gives 2, a killed process 137) gets no re-dispatch, because a second review
   cannot change it: hold the PR for a human at once. Under
   `merge: auto` an `error` never merges.
   Post a verdict comment on the PR whose first line is the line the
   hook printed, verbatim, so every comment carries the score, and whose
   second line is `Head: <sha>`, the recorded head, so the comment says
   which head it covers. When the hook printed no `reviewer-verdict:`
   line, the first line is `reviewer-verdict: error (<reason>)`, with
   `<reason>` one of `no verdict hook`, `hook did not run`, `hook exit
   <code>` (an exit code other than 0 or 1 that printed no such line),
   `reviewer timed out` or
   `no usable score`, so the comment still parses like the hook's own
   lines. The comment carries the score and the findings whenever the
   reviewer returned a score. On a re-review the comment lists the
   reviewer's `issues`, `resolutions` and `deferred` findings under
   three separate headings, `Issues`, `Resolutions` and `Deferred`, so
   a later re-review takes its `priorIssues` from `Issues` alone. All pass
   → the Merge policy, once step 1's CI is green. A derived `flag` or a specialist `block` → the
   contract's retry policy (one retry on the same branch, then
   `needs-review` and no merge). After a re-review, file its `deferred`
   findings as the contract's retry policy says, before the Merge
   policy or the retry runs. They never change the verdict.

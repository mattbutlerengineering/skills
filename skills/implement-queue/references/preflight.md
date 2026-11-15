# Phase 0 pre-flight: steps 2 to 4 in full

Moved verbatim from [SKILL.md](../SKILL.md), which links here from the step
that needs it. A phrase such as "this file", "above", "below" or
"the Rules" can name SKILL.md or a part of it.

## Step 2: the default preflight read

   `git fetch origin`, take `<sha>` from `git rev-parse refs/remotes/origin/main`,
   then:
   - With a `required_check`: read
     `gh api repos/{owner}/{repo}/commits/<sha>/check-runs --paginate`
     for that check, and
     `gh api 'repos/{owner}/{repo}/actions/runs?head_sha=<sha>&event=push'`
     for the head's push-triggered runs (issue-triggered workflows also
     run against the head and never decide it). That check present and
     `completed` with `success` is green. Queued or in progress is
     pending. Red is every completed conclusion other than `success`
     (`failure`, `cancelled`, `timed_out`, `skipped`, `neutral`,
     `action_required`, `startup_failure`, `stale`), and the check
     missing once every push-triggered run of the head has settled.
     Missing while a push-triggered run of the head is still queued or
     in progress is pending.
   - Without one: read
     `gh run list --branch main --commit <sha> --event push --json databaseId,name,status,conclusion`.
     A failed, cancelled or timed-out run is red; a run still queued or
     in progress is pending; green needs at least one completed
     `success` and no red run. No completed push run at all is not green.
   - Pending, or no push run yet, waits: poll the same read once a
     minute for up to 15 minutes (a profile's `preflight` hook may set
     another bound). Still not settled is unproven: claim nothing,
     report main as unproven and stop the iteration. Never claim a
     CI-fix issue or new work on an unproven main.
   - If main is red, read the failing job's log first. When it shows no
     repo cause (a runner or network failure, a cancelled or timed-out
     job), re-run the failed jobs once per head SHA: a run whose
     `run_attempt` is above 1 (`gh run view <run-id> --json attempt`)
     has had its re-run, so a later iteration on the same red head does
     not re-run it again. The `<run-id>` of a check run is in its
     `details_url` (`/actions/runs/<run-id>/job/<job-id>`; the check
     run's own `id` is the job id), and the push-runs read above lists
     it directly. Re-run with `gh run rerun <run-id> --failed` (cloud
     twin in the list above), then wait and judge the head again by the
     same read. Green on that final run is green. Only a second failure,
     or a failure with a repo cause, makes fixing main **this**
     iteration: claim or file the CI-fix issue, work it through Phase 2,
     and skip to Phase 3. A profile's `preflight` hook may say how to
     re-run instead. The re-run is never a way to skip CI or to declare
     main green without the check present and successful on the final
     run.

## Step 3: failed-PR causes and settled green PRs

   A failed PR is sorted by these causes before it can block, in this
   order, and the first match wins:

   - A failed PR with no linked issue (a dependency bot's, the release
     bot's) has nothing to label, is reported, and does not block
     claiming.
   - A failed PR that carries a `hold_labels` label, or whose issue
     does, is handed to a human, is reported, and does not block
     claiming.
   - A PR the evidence says must not merge (an automated revert whose
     red was infrastructure) is never fixed, re-run or updated toward
     green, is reported, and does not block claiming.
   - A failed PR of this queue whose issue carries `agent-failed` was
     given up on by the queue: it is not fixed or re-run again, is
     reported (its failing job linked) for a human to close or take
     over, and does not block claiming. This is what labelling the
     issue `agent-failed` in Phase 0 step 3 releases.
   - A failed PR whose failing jobs show no repo cause (a runner or
     network failure, a cancelled or timed-out job) gets its failed jobs
     re-run once per head SHA by the re-run rule of step 2, and is
     judged again. A PR still red after its re-run counts as failed
     and, when it is this queue's and matches no earlier cause, blocks
     claiming; the re-run is no exemption.

   A green PR is settled when its head commit is at least 15 minutes
   old and its head SHA has not changed since this session recorded it.
   Step 3 records every open PR's head SHA in each iteration. A PR with
   no record is judged on age alone, so a PR first seen with an old head
   commit goes to the gate at once, which keeps a one-pass session
   (nothing claimed) gating its green PRs. A young head waits until its
   commit is 15 minutes old, whatever the iteration. A head that changed
   since it was recorded is not settled whatever its date, and is
   recorded anew. A head named in this session's own worker result as
   the head that worker pushed counts as settled at once while the PR's
   head still equals it; this wins over the changed-since-recorded rule
   for that head only, and a head pushed by anyone else gets no such
   exception. The head commit's date is read first with
   `gh api repos/{owner}/{repo}/commits/<headRefOid> --jq .commit.committer.date`,
   `<headRefOid>` being the head from the list above (no MCP twin is
   verified). Where `gh` cannot read it, run
   `git fetch --depth=1 origin pull/<N>/head`, confirm
   `git rev-parse FETCH_HEAD` equals the head SHA, then run
   `git show -s --format=%cI <sha>`. A date read from any commit other
   than the PR's current head SHA leaves the PR not settled. The
   committer date is a proxy, since GitHub does not expose push time:
   `git rebase` resets it, and the real failure is a commit made earlier
   and pushed later, which looks old when it was just pushed; the
   recorded-head comparison catches that from the second iteration on,
   and a one-pass session accepts it. A date that cannot be read by
   either source
   leaves the PR not settled. An unsettled green PR waits this
   iteration, is not reviewed, and is reported; a failed PR keeps its
   disposition above.

## Step 4: another queue session

4. Look for another queue session, and report it before claiming. List
   the open issues that carry `in-progress` and that this session did
   not claim, with `gh issue list --label in-progress --state open --limit 1000 --json number,title,updatedAt`
   (cloud: `gh api 'repos/{owner}/{repo}/issues?labels=in-progress&state=open&per_page=100' --paginate`,
   dropping every entry that carries a `pull_request` key; MCP:
   `list_issues` with `labels: ["in-progress"]`, state open). A fresh
   session has claimed none, so every one counts, and a looping session
   subtracts the issues it claimed in earlier iterations, never one Phase 1
   skipped. Give each its
   claim time, the last line of
   `gh api repos/{owner}/{repo}/issues/<N>/timeline --paginate --jq '.[] | select(.event == "labeled" and .label.name == "in-progress") | .created_at'`
   (the timeline lists events oldest first). There is no MCP twin for
   the timeline in the GitHub MCP server's `issue_read` methods, so an
   MCP-only session reports each issue without a time. List the open
   PRs this session did not open whose head commit is under 15 minutes
   old, with the head from `gh api repos/{owner}/{repo}/pulls/<N> --jq .head.sha`
   and its time from `gh api repos/{owner}/{repo}/commits/<sha> --jq .commit.committer.date`;
   the commit's date stands in for the push time. Report both lists
   before Phase 1 claims anything. The label claim is the mutex, so
   this session proceeds to Phase 1 and never stops for what this step
   finds. A hard stop is not used, because one stale `in-progress`
   label, a crashed worker's, would block the queue for ever. What the
   report narrows is what this session touches: never touch an issue or
   PR listed here (no claim, relabel, merge or branch update, except that Phase 3
   step 1's head comparison and `--disable-auto` still run, since they
   only tighten), and claim
   only issues that pass the post-claim check in Phase 1. A `lock` hook
   that keeps its lock in the local git common dir cannot see a cloud
   session, so it does not replace this step or the Rules' One queue
   session per repo at a time. Under `source: work-orders` the issue
   list does not apply, because the claim there is `wo:in-progress`
   through the lifecycle machine in
   [references/work-orders.md](work-orders.md), and the pull
   request list still applies.

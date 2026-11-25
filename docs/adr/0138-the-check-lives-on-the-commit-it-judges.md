# The check lives on the commit it judges

- Status: accepted
- Date: 2026-11-24

The Owner chose option A on decision issue #2298. This ADR amends
ADR-0098's Decision 2: `check` now declares two outputs instead of one.

## Context

The 2026-11-20 workflow audit found two places where the `check` run
lands on the wrong commit. Both were confirmed against run history.

1. **Factory PRs.** The assembler runs `gh workflow run validator.yml
   -f pr=N` with no `--ref`. The `check` job checks out
   `refs/pull/N/head`, but a dispatched run's check runs attach to the
   tip of the ref it was dispatched on, which is main. In run 36475022721
   the job checked out PR #579's head, and its check run was recorded on
   8823343, the assembler's spend-row commit on main. PR #579's own head
   never got a `check`. Two things broke as a result:
   `conductor_merge.wait_checks`, which polls the PR head's check runs,
   stalled until it timed out. And the merge train's preflight, which
   judges main by the `check` run on main's head, could read an agent
   PR's red as main red, or let an agent PR's green hide a red main.
   `--ref <agent-branch>` does not fix this. It would run the agent
   branch's copy of `validator.yml` with `FACTORY_REVIEW_TOKEN` in reach
   (ADR-0098).
2. **Bot pushes to main.** `gate-digest.yml` and the assembler's
   spend-row step push with `GITHUB_TOKEN`, and those pushes start no
   workflow. Main's new tip therefore had no `check` (gate-digest commit
   661ffc7 has 17 check runs, and none is named `check`). The merge train
   read that as unproven and went report-only until a human pushed.
   Dispatching the validator on main did not work either, because the
   dispatch required a `pr` input.

Option B would have taught `wait_checks` and preflight to find the
dispatched run by the PR number in its inputs, and to judge a bot's
ledger-only commit by its parent. It lost because every reader of a
`check` run would need that special case.

## Decision

**A base-code job posts check's verdict onto the commit check judged.**
`validator.yml` gains a `check-on-head` job. It runs after `check`, only
on a `workflow_dispatch` that names a `pr`, and only when `check` passed
or failed. It creates a check run named `check` through the Checks API,
on the commit `check` checked out, with check's result as the conclusion.
It has to be a check run, not a commit status, because `wait_checks`
reads check runs. The job holds only `checks: write`. It checks out no
code and runs no `make`, so the pull request's code never runs with that
grant.

- **The commit comes from `check` itself.** Right after checkout, `check`
  records `git rev-parse HEAD` as a second job output, `judged`, before
  any PR code runs. A later step cannot rewrite an earlier step's
  outputs, so the PR's code cannot redirect the verdict. The poster still
  refuses any value that is not 40 lowercase hex digits. The commit is
  not read from the PR's current head, because a push to the PR after
  `check` started would then receive a verdict on a commit nobody judged.
- **The verdict is `needs.check.result`**, which GitHub computes, as for
  the reviewer (ADR-0098 Decision 2). A cancelled or skipped `check`
  posts nothing.
- **A PR dispatch's own check run carries another name.** On a dispatch
  with `pr`, the `check` job is named `check (dispatched for PR N)`. Its
  check run still lands on main's tip, but under that name it is no
  longer read as main's `check`. Every other run is still named `check`.

**The `pr` input is optional, and a dispatch without it checks the
default branch's tip.** With no `pr`, `check` uses checkout's default
ref, which is the tip of the dispatched ref, and its check run lands on
that same commit. Without a PR to read, the synthesize steps, the
reviewer and the `wo:needs-review` flip all skip.

**Both bot pushes dispatch the validator on main.** Right after its push
lands, each runs `gh workflow run validator.yml` with no `pr` and no
`--ref`, so the dispatch runs the default branch's own definition:

- the assembler's deliver job, after "Commit the run's spend row"
  succeeds. The step uses `continue-on-error`, because a missed check on
  main is not the order's failure.
- gate-digest, after it commits the gate-latency rows. The workflow
  gains `actions: write` for this.

The validator pushes nothing, so neither dispatch can recurse.

## Narrowest reading, stated

The issue's option A names two parts: the poster job, and the optional
`pr` with bot-push dispatches. Renaming the PR-dispatch check run is
neither of them. It is included because without it, main's tip would
still carry a `check` that judged a PR, and that is exactly the
misreading the issue sets out to remove. Nothing else changed. Readers
of `check` (preflight, `wait_checks`, the queue profile's
`required_check`) are untouched.

## Consequences

- A factory PR's head carries `check` with the dispatched run's verdict.
  `wait_checks` sees it, and preflight never sees it on main.
- A bot push to main gets its own `check` within minutes. The preflight
  can then prove main green, so the merge train no longer waits for a
  human push. If the dispatch fails, the tip has no `check` and reads as
  unproven, which is the old behaviour.
- A dispatch race is harmless. If someone pushes main between a bot push
  and its dispatch, the dispatch checks the newer tip. That tip is the
  one preflight judges.
- Each re-dispatch on the same PR posts another `check` run on its head.
  The check-runs endpoint returns the latest run per name by default.
- **Unverified until a live run:** GitHub may replace the `details_url`
  of a check run created with `GITHUB_TOKEN` by its own link. The run
  URL is also written in the check's summary for that reason. A check
  run created with `GITHUB_TOKEN` starts no workflow, and nothing here
  depends on one starting.
- `check` now declares two outputs. `judged` is a sha recorded by a step
  that runs before any PR code, and it reaches only the poster's `env:`.
  ADR-0098's other rules about the handed-over findings are unchanged.

# A re-review converges on the first review's findings

- Status: accepted
- Date: 2026-11-11

The Owner chose this fix on 2026-11-11, from a measurement of where
this repo's development time goes. Builds on [ADR-0123](0123-the-orchestrator-derives-the-reviewer-verdict-from-the-score.md),
which has the orchestrator derive the verdict from the reviewer's
score. It changes what a second review of the same pull request may
hold the pull request for, not the threshold or who derives the
verdict.

## Context

The gate's review loop does not converge. Measured on 2026-11-11 from
the GitHub API: 10 of 26 gated pull requests pass their first review. A
flagged one takes 2 to 3 rounds and 20 to 30 minutes, with a tail of 5
to 13 hours. 6 of the last 7 `implement-queue` pull requests merged at
4 or 5 out of 10 on an Owner override, with no pass.

Every round is a fresh full review. It returns 4 to 6 new findings,
most against the text the previous fix added, and many asking for more
than the issue did: the second review of #1728 asked for a one-winner
mutex where the issue asked for a post-claim check. The same pattern is
on #1720, #1724, #1725 and #1728.

## Decision

1. **A re-review holds a pull request for three things only.** A prior
   issue that is still open, a wrong line in the fix diff, or a major
   defect (hallucination, regression, security) anywhere in the diff.
2. **Every other finding is deferred.** That includes a request for
   more than the acceptance criteria or a prior issue asked. A deferred
   finding is not scored, and the orchestrator files the deferred
   findings of one re-review as one issue without `ready`: the Owner
   decides whether a follow-up enters the queue.
3. **The threshold, the `verdict` hook and the verdict comment's first
   two lines are unchanged**, so ADR-0123 stands.

## Rejected alternatives

- **Raising the retry cap.** It buys more rounds of the same review,
  and that review does not converge.
- **Lowering the pass threshold.** ADR-0123 keeps the threshold out of
  the reviewer's sight and in one module; moving it does not stop a
  second review from raising new findings.
- **Filing follow-ups with `ready`.** The queue would feed itself:
  every re-review could add work that no person asked for.

## Consequences

- A defect that is not major and that the first review missed can
  merge. It is tracked in the follow-up issue, not fixed in the pull
  request.
- The first review is the one full adversarial pass. A weak first
  review is no longer made up for by a second one.
- The Owner's overrides on #1725 and #1728 ("beyond the issue's ask,
  state the limit") become the written rule, so those merges no longer
  need an override.

## If rejected

Delete the Re-review section of the reviewer contract and its three
inputs (`priorIssues`, `priorHeadSha`, `fixDiff`). Every round is a
full review again.

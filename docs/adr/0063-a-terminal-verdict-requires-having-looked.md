# A terminal verdict requires having looked

- Status: provisional
- Date: 2026-08-25

ADR-0032 gives a work order a terminal state, `wo:failed`, and ADR-0045
makes `assembler.yml` its writer. The workflow flips an order to it when
a dispatched run fails after the claim — without that, a dead run leaves
the order on `wo:in-progress` forever, where the gate digest and the
improvement routine both read it as work still in flight. That reasoning
is correct and is not disturbed here.

What was missing is that the flip fires on `failure()` alone, and one of
the steps that can fail is the one that asks whether the agent delivered
anything. `assembler.pr_for_issue` answers `None` both when no open PR
closes the order's issue and when the `gh pr list` behind that question
was unusable — an ordinary rate limit is enough (`cli.gh_runner`:
*"unauthenticated, or rate-limited (CalledProcessError) gh raises
CLI_FAILURES"*). Measured, the two cases are byte-identical in both
channels the workflow branches on: exit 1, and `pr=`.

So the factory could stamp a verdict about an agent's performance onto
the order after failing to observe that performance at all — and because
the validator trigger is gated on the same empty `pr` output, the PR the
agent did deliver would sit unchecked, with no event left to wake the
validator.

## Decision

A run may apply `wo:failed` only when it actually observed the agent's
delivery to be absent. `find-pr` now states whether it got to look, as a
`looked` step output, and the failure step is suppressed when — and only
when — that output is an explicit `'false'`.

An unset output still flips. A run that died before the find step ever
executed is a failure the order should record, and reading `''` as
permission to flip is what keeps this narrow: it removes exactly one
case, the one where a step ran and reported blindness.

The run still fails. A find that cannot look is a real failure and the
operator must see red; what changes is only whose failure it is recorded
as.

## The trade

The order stays on `wo:in-progress` after a blind find. That is the rot
the flip exists to prevent, so this ADR is buying one kind of wrongness
with another, and the reason to prefer this one is that they are not
symmetric:

- A false `wo:failed` is **silent and terminal**. The order leaves the
  in-flight queues the digest and the routine read, so the two mechanisms
  that would surface a stuck order have both been told there is nothing
  to surface.
- A stuck `wo:in-progress` is **loud and recoverable**. The run is red,
  the order still appears in the digest, and the improvement routine
  still sees it. Every mechanism that notices stuck work is still
  looking at it.

An honest unknown that stays visible beats a confident wrong answer that
does not.

## Alternatives

**Let a blind find pass quietly.** Then no label is wrong, but the
operator loses the only signal that the run learned nothing. A green run
on a blind find is a worse lie than a wrong label.

**Distinct exit codes instead of an output.** `cli.report` owns the
0/nonzero convention for every tool in the repo, and a workflow `if:`
cannot read an exit code without capturing it by hand. Step outputs are
the seam `resolve` and `claim` already use to tell the workflow what to
branch on.

**Re-trigger the validator on a later run.** That would fix the orphaned
PR as well as the label, and it needs a record of which orders have
unchecked deliveries. No such record exists; building one is a feature.
Left out, and named in the run's `release.md` as carry-forward.

## Notes

- Status is provisional: the trade above is a judgment about which
  wrongness costs less, and the operator who runs this factory is the one
  who has felt both. Confirm or reverse on evidence from a real blind
  find.
- Numbered 0063 rather than 0062 deliberately. Open PR #333 adds an
  `0062-`, and an untracked `0062-` sits on the `feature/pipeline-board`
  branch; that collision is already two-way and this ADR declines to make
  it three.

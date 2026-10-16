# A finished run's retry redoes its bookkeeping, and a launch re-reads its issue

- Status: provisional
- Date: 2026-10-16

Amends no record. ADR-0034's open outcome vocabulary and #954's per-run
spend files stand. This decides what a `retry` answer means when the
Worker already finished, and what `next` reads before anything spends.

## Context

A Conductor run ends in bookkeeping: the spend row's commit on the item
branch, the push, the pull request. A failure there stalled the item
with cause `delivery-failed` after a `completed` run row, and `retry`
relaunched the Worker exactly as it does after a budget stop. One
consumer spec completed three times for $12.53 (issue #939) because a
commit hook refused the spend row, whose complaint the stall carried
only as husky's last line. The spend rows then sat uncommitted in a
worktree on a branch never pushed, so `close` refused the batch.

Separately, `next` offered paid retries and fresh spec launches for nine
items whose issues other pull requests had already closed; #954 stopped
the PR from opening, after the run had spent.

## Decision

1. **A delivery-failed stall whose run row is `completed` is retried by
   `next`, never by a Worker run.** On the Owner's `retry`, `next`
   commits the spend row the worktree holds (or re-meters it from the
   kept result event), pushes, opens or updates the PR, and writes one
   state row `stalled → <step>` carrying the completed run's own
   `run_id`. That row has no `pid` and a reason that is not
   `launched`: it is not a launch, so the run sequence and calibrate's
   wall-time join pass over it, while the item view's `finishing`
   resolves to the completed run and the survey advances the item in
   the same tick. A launch of that step with another run id is refused.
   The runner keeps `pr-body.md` when delivery fails, for that turn.
2. **Such a stall offers `retry` and `block` only.** No band is
   involved; `retry-up` would bump a run that is not going to happen.
3. **Before any run launches, `next` reads the issue's state.** One
   `gh issue view --json state` per item about to launch (merge turns
   excepted: they are answered consent). An issue that is closed, or
   whose state gh cannot read, holds the item behind a clarify ask the
   tool writes itself — options `block` and `proceed`, no state row —
   until the Owner answers; `proceed` re-reads before launching.
4. **A stall reason from a failed git call carries the command's
   stderr tail.** `cli.detail` gains `tail`; the spend and delivery
   writes keep the last three lines, so a hook's own complaint reaches
   the ask. Every other caller keeps the last line.

## Consequences

- A hook or push failure costs a second of the Owner's session, not a
  Worker run; the spend row that failed to commit reaches the branch
  and `close` sees it.
- A closed issue costs nothing: the first `next` after the close holds
  it. The Conductor still words a Worker's own clarify asks; this one
  it only presents.
- `conductor_next.py` (mirrored) owns `next`'s impure side and the
  delivery the runner shares with it; `conductor_flow.py` stays pure.
- Not decided: a `wo` for a re-metered build spend row (the item key
  is recorded, since the briefed breakdown row is not), and a blocked
  item whose spend file was never committed (its retry is the Owner's
  hand commit; `close` does not edit a Worker's branch).

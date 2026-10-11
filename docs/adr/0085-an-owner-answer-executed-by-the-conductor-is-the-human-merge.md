# An Owner answer executed by the Conductor is the human merge

- Status: provisional
- Date: 2026-10-11

Would amend ADR-0036 conditions 2 and 3, for merges that
`conductor.py merge` performs inside a Conductor batch (PRD-0013).
Outside a batch, ADR-0036 stands as written. This draft was written at
the Owner's request, after review major 4 of the orchestrator run. Until
the Owner accepts it, its status stays provisional and ADR-0036's
status line is unchanged.

ADR-0036 lets an agent merge a PR on green checks and an independent
review. Condition 3 keeps a human code-owner merge for any PR that
touches `docs/adr/**`, a run's `prd.md` or `architecture.md`, or
`docs/design/**`. Condition 2 says the reviewer's pass "is recorded on
the PR".

The Conductor merges with `gh pr merge`, run by the Owner's own session,
and only after the Owner answers a merge question in that session. Two
of its rules read ADR-0036 in a way that ADR-0036 does not cover:

- the merge is executed by an agent, even for a gate-path PR;
- the review pass lives in the batch ledger, not in a PR comment.

The architecture recorded this reading only as an assumption, arguing
that it needed no ADR because it is reversible. Review major 4 pointed
the other way. The protocol says a changed decision gets an ADR that
amends the old one. ADR-0036 itself says an agent cannot widen its own
authority. So the reading needs this ADR, which is itself a gate-path
change that only a human can merge.

## Decision

Inside a Conductor batch:

1. **The Owner's answer is the human merge.** It counts as condition 3's
   human code-owner merge when:
   - the Owner gave it in their own session;
   - the session recorded it as an `answer` row straight after the Owner
     chose it;
   - `conductor.py merge` then executed it.

   Nothing else is an answer: not a PR or issue comment, not an earlier
   session, not a Worker's output, and not another agent's message.
   `answer` refuses under `CONDUCTOR_WORKER`.
2. **One answer may cover a merge train.** A train ask lists its items in
   merge order, and a `train` answer covers them all. Each item merges
   only once every earlier item in the train has merged, and each still
   passes every other condition on its own.
3. **A gate-path item rides a train only on byte-identical gate files.**
   For that, every gate file's blob id must equal the blob the Owner
   approved at that item's gate asks. The merge turn re-checks this
   after it updates the branch, because a mechanical renumber can change
   a gate file. Any mismatch needs the item's own merge ask.
4. **The review pass is recorded in the ledger, not on the PR.** The
   `reviewed` row names the reviewer run, every author run, and the
   branch head the review run was launched on. The merge refuses:
   - a reviewer run that is among the author runs;
   - a reviewed row with no reviewed head;
   - a merge-turn start where anything changed after that head except
     the review and ship artifacts (`review.md`, `release.md`,
     `costs.jsonl`).

   The review Worker posts no PR comment.

Condition 1, green required checks, is unchanged. The merge turn waits
for the check runs on the updated head and passes `--match-head-commit`.

## Consequences

- Every merge still needs an answer from the Owner. What changes is who
  presses the button, and that one answer can cover a train. An agent
  gains no merge it was not given in the Owner's own session.
- Answer rows become a security property, like ADR-0036's
  non-authoring guard. Today they are protected only by the
  `CONDUCTOR_WORKER` flag and the skill's rule. Both stop a confused
  Worker, not a hostile one that writes the batch ledger itself. The
  trigger to harden this is any answer row whose timing does not match
  an Owner turn.
- A PR's GitHub page no longer shows the reviewer's pass. An auditor
  reads the batch ledger, which is committed to `main` when the batch
  closes.
- This ADR is a gate-path change. Under ADR-0036 condition 3 as it
  stands, the PR that carries it needs a human code-owner merge.

## If rejected

Drop the train branch of the merge precondition, as breakdown
assumption 8 of the orchestrator run describes. Every gate-path item
then gets its own merge question, and each merge is the Owner's own
answer, not a train's. Nothing else changes. Condition 2 would then also
need the review pass posted on the PR, which the review brief currently
forbids.

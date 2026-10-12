# Standing consent may cover a Conductor merge

- Status: accepted (Owner, 2026-10-11)
- Date: 2026-10-11

Amends ADR-0085, for merges that `conductor.py merge` performs inside a
Conductor batch. The Owner chose this policy on 2026-10-11, in session:
opt-in, and narrow. It resolves issue #679.

ADR-0085 makes an Owner answer, given in the Owner's own session and
executed by the Conductor, the human merge. Its first consequence is
"every merge still needs an answer from the Owner". PRD-0013 lists
unattended merges as out of scope. A repo that drains its queue from a
scheduled routine has no Owner in the session, so the Conductor cannot
take over that path.

## Decision

`factory.json` gains a standing-consent policy,
`conductor.standing_consent` (`enabled`, `tier_labels`). It is **off by
default**: absent, or with `enabled: false`, nothing below applies, and
every merge needs the Owner's answer as ADR-0085 says. A malformed
policy is a config problem (detector F, and `next` and `merge` both
refuse), never a default.

When it is on, a Conductor merge may go ahead with no in-session Owner
answer only when **all** of these hold:

1. **A passed review by a distinct Worker.** This is the merge
   precondition ADR-0085 already enforces for every merge: a `reviewed`
   pass whose reviewer run is none of the item's author runs, with its
   reviewed head, and nothing unreviewed after that head.
2. **Green required checks.** The merge turn already waits for every
   check run on the updated head to finish green before it lands.
3. **A tier label, if the policy names any.** With a non-empty
   `tier_labels`, the item's issue must carry one of them, read when
   the consent is recorded.
4. **No gate-path file.** The item branch changes no file that
   `conductor_flow.GATE_PATH` matches: `docs/adr/**`, `docs/design/**`,
   or a run's `prd.md` or `architecture.md`. A gate-path item always
   needs the Owner's own answer, so ADR-0036 condition 3 and ADR-0085
   stand for it unchanged.

The policy covers only an item that no merge ask covers, answered or
not. Once the Owner has a merge question on an item, the Owner's answer
decides it.

`next` records each covered item as a `consent` row in the batch
ledger: `policy: "standing"`, and a reason naming what the policy
checked. The merge turn treats that row as the item's consent. It then
re-checks the policy as `factory.json` reads at merge time, and the item
branch's gate files after merging `main` in. If the policy was turned
off, or a gate file appeared, the merge is refused and the item needs
the Owner's own answer.

A `consent` row is not an `answer`. The scorecard's Owner-touch figures
count answers only, so a standing merge is never counted as an Owner
touch or as Owner wait.

## Consequences

- PRD-0013 put unattended merges out of scope. This ADR changes that,
  and only for the narrow set above. Every other ask still needs the
  Owner in session: the spend ask, gate asks, stall and clarify asks,
  and the batch's closing merge. An unattended session can advance a
  batch only up to its next ask.
- An agent can now merge with no human answer in the loop. The policy is
  the Owner's written consent in advance, and only the Owner edits
  `factory.json`. Only `next` writes a `consent` row, and `next` now
  refuses under `CONDUCTOR_WORKER`, the same guard ADR-0085 puts on
  `answer`. The same trust limit as ADR-0085 holds: this stops a
  confused agent, not a hostile one that edits `factory.json` or the
  ledger.
- The merged PR's GitHub page shows no human decision. An auditor reads
  the `consent` row in the batch ledger and the policy in
  `factory.json` at that commit.
- This ADR is itself a gate-path change, so the PR that carries it needs
  a human code-owner merge.

## If rejected

Delete the `consent` row kind and the policy keys. Every merge then
needs an Owner answer again, exactly as ADR-0085 says. A repo that has
turned the policy on would get a config problem from `next`, never a
silent merge.

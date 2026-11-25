# A factory-driven run that reached a human-merged PR graduates maturity

- Status: accepted (Owner, 2026-11-24)
- Date: 2026-11-24

Amends ADR-0012 and ADR-0019. The Owner chose the recommended option on
issue #2200, in session, on 2026-11-24.

## Context

ADR-0012 says a skill graduates past draft "only via a real run".
ADR-0019 adds that evals never graduate maturity. Neither says whether
a run the factory drove itself counts as a real run: one an agent ran
from an autorun brief, a dispatched work order or an unattended
routine, with no human answering each stage live.

LEDGER.md answered by default. Every stage skill reads used-once on the
one feature:seed-backlog dogfood run, and capture, autorun and
ux-design read draft. Yet the repo holds 72 committed capture runs, 27
autorun briefs and three ux.md files (the 2026-11-20 eval-tooling
audit, issue #2200). The ledger's "draft (written, never exercised)"
was false for those three skills.

## Decision

**A run the factory drove itself is graduation evidence when it reached
a human-merged PR.** It counts the same as a run a human drove, for
every skill the run exercised. The LEDGER evidence line names the run
(its run-ref and directory) and the PR number.

**Human-merged means the run's own record shows a human merged it.**
The PR's `mergedBy` on GitHub is not enough on its own: agents in this
repo merge with the Owner's credential, so an agent merge and an Owner
merge show the same login. The run's `release.md`, or the batch ledger
under ADR-0085, must say the Owner merged the PR, or that the merge
executed an Owner answer given in session (ADR-0085). The citing change
also checks the PR with `gh pr view <N> --json state,mergedBy` and
cites only a PR whose state is `MERGED`.

**A merge an agent performed on standing authorization is not decided
here.** That covers a brief or session that authorized "merge once CI
is green", and ADR-0086 standing consent. Such a run does not graduate
a skill until the Owner rules on it.

**Evals still never graduate maturity** (ADR-0019 is unchanged on that).
Neither does a run whose PR closed unmerged, or a run with no PR.

## Consequences

- capture and autorun move to used-once on
  maintenance:the-reviewer-token-runs-agent-code
  (`docs/fixes/the-reviewer-token-runs-agent-code/`). Its `release.md`
  records that the Owner merged PR #923 on 2026-10-15 and calls it a
  human merge. The run was driven from `autorun-brief.md`, and its
  `defect.md` is the capture artifact.
- ux-design stays draft. None of its three runs has a human merge in
  its own record. process-dashboard's PRs #266–#276 and assembly-line's
  PR #1168 were merged by the agent on the session's or the brief's
  authorization: the standing-authorization case left to the Owner
  above. pipeline-board's `release.md` cites PR #351, which closed
  unmerged. Its diff landed as PR #484, whose body says "Human merge
  required" because it touches `docs/adr/**`. #484 was merged on
  2026-09-21 under the Owner's login, but no record says who merged
  it. If the Owner confirms that merge was theirs, ux-design graduates
  on feature:pipeline-board.
- The rule says what counts as evidence. It does not sweep the ledger.
  Other skills graduate one cited run at a time, as before.

# This repo opts in to implement-queue auto-merge, with a docs fast path

- Status: accepted (Owner, 2026-10-15)
- Date: 2026-10-14

The Owner accepted this on 2026-10-15, in session, with ADR-0095.
Applies ADR-0087 (a queue profile may opt in to `implement-queue`
auto-merge) and ADR-0088 (a fast-path classification is the review for
auto-merge) to this repo. Recorded by the `faster-sdlc` feature run
(`docs/features/faster-sdlc/breakdown.md`, Milestone 3; issue #908). It
amends nothing: both ADRs were written for a consumer repo's profile,
and this repo never wrote one, so `implement-queue` here has stopped at
reviewed, green PRs (ADR-0033's gate 3). The Owner's acceptance of this
ADR is the gate on the rest of Milestone 3.

## Context

The measured wait, over the last 150 merged PRs on 2026-10-14
(`gh pr list --state merged --limit 150`): median open-to-merge time
0.64h, p75 2.0h, p90 13.5h. 24 PRs (16%) were open longer than 4h, and
they hold 96% of all PR open-hours. The longest were routine and agent
PRs from 2026-09-28 that sat about 9 days, until the next Owner merge
session. Merges come in bursts: 52 on 2026-10-14, none from 2026-09-29
through 2026-10-06. A green, reviewed PR waits for a session, not for a
decision. `main` has no branch protection and the ADR-0070 merge queue
is off (`docs/kb/main-unprotected.md`), so nothing re-tests a PR against
the main it will actually land on.

## Decision

1. **`.claude/implement-queue.md` sets `merge: auto`.** ADR-0087's four
   conditions apply unchanged to every open PR in this repo, whatever
   its author or branch: the required check present and green, an
   independent review passed, no gate-path file, no hold label. The
   required check is `check`, the validator workflow's gate job (`make
   check`). The hold labels are ADR-0087's default, `needs-review`.
2. **Gate paths are ADR-0087's defaults plus three.** To `docs/adr/**`,
   `docs/design/**`, `**/prd.md` and `**/architecture.md` this repo adds
   `factory/templates/**`, `.github/**` and `.claude-plugin/plugin.json`.
   A release PR (ADR-0095) touches the last, so it keeps a human merge;
   so does any change to the workflows or the stamped payload.
3. **The fast-path rule**: every changed path is under `docs/` and none
   is a gate path. `python3 fast_path.py <base> <head>` is the
   classifier (issue #909): `fast-path: low-risk` and exit 0 when the
   rule holds, `fast-path: review (<first non-matching path>)` and exit
   1 otherwise and on an empty diff, and exit 2 with a `fast-path:`
   problem string when git fails or a ref does not resolve, which is
   ADR-0088's fail-closed case. A low-risk PR that no specialist
   reviewer matches satisfies condition 2 without a reviewer dispatch
   (ADR-0088); everything else is reviewed.
4. **The merge train merges one PR at a time.** Two green PRs can go red
   together (`docs/kb/cross-pr-merge-hazards.md`: number collisions, a
   check meeting the data it governs, manifest drift). So before each
   merge the train runs `update-branch` on that PR and waits for a
   green `check` against the main of that moment; the next PR starts
   only after the previous merge has landed. A PR whose updated branch
   goes red is reported, not merged.

## Rejected alternatives

- **Branch protection with GitHub's merge queue (ADR-0070).** It would
  re-test each PR against the queue's head, but it needs required
  checks configured on `main`, which the Owner has left unprotected;
  turning that on is a repo-settings decision outside this run.
- **Auto-merge for agent PRs only.** The wait falls on routine, agent
  and Owner PRs alike, and a profile keyed on author is a second rule
  for the same merge. ADR-0087's conditions already say what makes a
  PR mergeable; the author is not one of them.
- **A fast path by label or by author.** A label is set by whoever
  opens the PR; the path rule is read from the diff and committed in
  the classifier, which is the audit record ADR-0088 asks for.

## Consequences

- The profile's commit is the Owner's standing consent, as ADR-0087
  frames it, and the classifier's commit is the fast path's. Both
  change only by a PR, which touches `.claude/` and root Python, not a
  gate path; the Owner may add them to `gate_paths` later.
- A merge the session's runtime denies is never retried by another
  route (ADR-0087). The merge command, `gh pr merge <N> --auto --squash
  --delete-branch`, needs a session permission the Owner grants
  outside the repo (issue #910's Owner step).
- The merge-train routine (`docs/factory/merge-train-routine.md`,
  issue #911) is the scheduled caller: Phase 0 and Phase 3 of
  `implement-queue` over open PRs, claiming no new issue.
- Milestone 3's measure is the same three numbers as the baseline
  above, two weeks after the routine's first run (issue #912).

## If rejected

No profile is written. `implement-queue` keeps stopping at reviewed,
green PRs, the fast-path classifier stays advice a human can run, and
the Owner's merge sessions remain the only path to `main`.

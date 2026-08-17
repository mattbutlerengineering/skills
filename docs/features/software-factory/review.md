---
stage: review
run: feature:software-factory
date: 2026-08-16
---

# Review: software-factory (Milestone E re-review)

## Scope

Re-review after the fix loop, per the breakdown's 2026-08-14 mandate
("Verify and Review re-run after Milestone E"); supersedes the
2026-08-14 review (git history). Two jobs: audit every prior finding's
disposition against the tree, and review the delta the fix loop
produced — 5719599..663265c, 15 commits (PRs #286–#293 plus close-out
chores), 1,144 insertions across 30 files. Files read in full diff:
assembler.yml, validator.yml, cost-report.yml, Makefile, assembler.py,
budget_guard.py, cost_report.py, rejection_mining.py, setup.md,
ADR-0055, docs/backlog.md, skills/doctor/SKILL.md, and the five test
files; template mirrors verified by detector E (today's battery:
`gates: 0 problem(s)`, `selftest: ok`; full suite `Ran 1234 tests …
OK`). Three passes over the delta: correctness, design conformance,
security.

## Prior findings — dispositions verified in-tree

- **Critical (gate 3 silent for factory PRs)** — FIXED, WO-0030.
  validator.yml gains the `workflow_dispatch` arm with a synthesized
  PR payload; assembler.yml finds the agent's PR by its Closes link
  (`assembler.pr_for_issue`, the tested authority) and dispatches
  gate 3 by name. No-match fails the find step through `cli.report`'s
  nonzero exit and the `failure()` step flips the order to `wo:failed`
  (`test_no_match_writes_empty_and_exits_nonzero`,
  `test_assembler_finds_the_pr_and_dispatches_the_validator`).
- **Major (success-path ledger row dies with the runner)** — FIXED,
  WO-0031. The row is re-applied to a fresh `origin/main` worktree and
  pushed — never from HEAD, which could smuggle agent commits onto
  main (`test_the_push_leaves_from_a_fresh_main_worktree_not_head`).
- **Major (hard_stop pushes before it records)** — FIXED, WO-0032.
  Append now precedes push_wip so the WIP commit carries the row
  (`test_the_exhaustion_row_is_inside_the_pushed_commit`).
- **Major (fail-closed PAUSE never sets FACTORY_PAUSED)** — FIXED,
  WO-0033. The pause step is gated `always() && pause == 'true'`;
  outputs are written before the failing exit
  (`test_the_pause_step_survives_a_failing_report_step`, and the
  resume step deliberately does not survive one).
- **Major (ADR-0034 stops not wired)** — FIXED in its surgical half,
  WO-0034: `timeout-minutes: 60` on the job, `--max-turns 100` on the
  agent step. The token-budget hook is DEFERRED by ADR-0055 (accepted)
  — a recorded decision now, not an undocumented gap.
- **Major (stamped-repo dispatch impossible, undisclosed)** — FIXED as
  disclosure: setup.md names the charter gap and its fail-closed
  consequence; shipping payload charters is DEFERRED by ADR-0055.
- **Minors** — two FIXED via WO-0035 (excerpts sanitized through
  sweeps' `sanitize`, fenced with pre-defanged runs, duplicate Closes
  refs deduped via ordered `dict.fromkeys`). The remaining seven
  (gates.py's J-roster contradiction, the WIP-cap claim, digest title
  sanitize, NaN cost row, gate_digest row discard, duplicate tracker
  refs, the predictable heredoc delimiter) stay DEFERRED on their
  2026-08-14 reasons — none was in this delta's touched files.

## Findings (new, this delta)

### Minor: dispatched validator runs attach no check to the PR head — the critical's ghost returns under branch protection

- Scenario: `gh workflow run` binds the run to main's ref, so no check
  run or commit status lands on the factory PR's head SHA. Today the
  verdict still reaches gate 3 — `make check`'s findings ride the
  reviewer comment and the `wo:needs-review` flip lands — but the PR's
  own Checks surface stays empty. The day physical branch protection
  activates (breakdown note: when the repo goes Pro or public),
  required checks on factory PRs never report, and the original
  critical resurfaces as "permanently unmergeable."
- Decision: deferred — paired explicitly to branch-protection
  activation; fix shape is the dispatched check job POSTing a commit
  status to the PR head SHA. Must land in the same change that turns
  protection on.

### Minor (security): the agent's token gained `actions: write`

- Scenario: the hand-off needs `actions: write` at job level, and the
  claude-code-action step receives the same GITHUB_TOKEN — a
  dispatched agent can `gh workflow run` any workflow_dispatch
  workflow, including the charter replay, a paid model run. Bounded by
  ADR-0032 (the prompt substrate is repo-controlled), so near the
  owner-attacks-self floor.
- Decision: deferred — next assembler.yml touch: move find-pr + the
  validator trigger to a follow-on job (`needs: assemble`) that alone
  carries `actions: write`, restoring the agent job's narrower token.

### Minor (security): the dispatch arm's fork guard is a comment, not a condition

- Scenario: the review job admits `workflow_dispatch` unconditionally;
  nothing verifies the dispatched PR is same-repo (the comment asserts
  factory PRs always are). A write-collaborator induced to run
  `gh workflow run validator.yml -f pr=<fork PR#>` executes the fork's
  Makefile in a job whose post step holds FACTORY_REVIEW_TOKEN (a PAT)
  — the exfiltration the pull_request arm's head-repo guard exists to
  block. Today the dispatcher set is the owner alone.
- Decision: deferred — next validator touch: the synthesize step fails
  unless `head.repo.full_name == GITHUB_REPOSITORY` (all three jobs),
  converting the comment into an enforced condition.

### Minor (design): the synthesize step breaks validator.yml's every-step-calls-make contract

- Scenario (decayed contract): the one-file-two-repos design rests on
  "it names no command of its own: every step calls a make target"
  (breakdown note, 2026-07-12) — each repo's Makefile knows where its
  tools live. The payload-synthesis step inlines `gh api` plus a
  python one-liner, three identical times; a stamped repo that
  relocates its tools cannot relocate this logic through its Makefile.
- Decision: deferred — fold into a make target (`make pr-event PR=…`)
  on the next validator touch; the Makefile↔CI lockstep test then
  pins it like every other step.

### Minor: a manual validator re-dispatch re-flips `wo:needs-review`

- Scenario: the pull_request arm deliberately excludes `synchronize`
  from the label job so a push to an open PR "must not re-flip an
  order a human already moved along" — but the synthesized payload
  always says `action: opened`, so an owner re-dispatching the
  validator on an already-reviewed PR (after a body fix, say) re-flips
  the order and the digest's queue-entry math double-counts, skewing
  ADR-0041's latency rows.
- Decision: deferred — rare, owner-driven path; make the flip
  idempotent (skip when the order is already past `wo:needs-review`)
  on the next validator touch.

## Passes with no findings

Correctness came back clean beyond the above: `pr_for_issue` fails
closed on gh errors, silent truncation (LIST_WINDOW discipline,
mirrored from rejection_mining), and no-match; `resolve_row`'s
sub-bullet capture stops at the first blank or unindented line so the
next row never bleeds into the substrate; the spend-push race loses
only a row that detector G recovers at the merge gate on the one path
that reaches it, and shows red on the step either way; hard_stop's
reorder costs no resilience (the append is local IO a push failure
cannot touch); sanitize-before-fence ordering means the quoted line
can never close the fence. Security beyond the two minors: every new
gh/git call is an argv list; the dispatched PR number is int-derived
before it reaches `-f pr=`; no secret is echoed; the synthesized
payload is fetched fresh from REST (which also heals issue #216's
stale-payload class for the dispatch path). Design: seam discipline
held (Closes grammar stays in knowledge_plane, subprocess in cli,
problem strings through cli.report); all template mirrors are
byte-identical (detector E green); doctor's target roster and the
lockstep test were extended with `find-pr` rather than drifting.

## Verdict

Ready to ship. The 2026-08-14 review's critical and all five majors
are fixed in-tree with pinning tests or explicitly recorded in
ADR-0055 — the operator's arbitration, now a citable decision. This
delta introduces no critical or major findings; its five minors are
deferred with logged reasons, one (the PR-head check status) bound to
a named future trigger so it cannot resurface silently. The
verification FAILs that remain (no live gate traversal) are
operator-adjudicated to `docs/backlog.md` and are Operate-stage
graduation material, not review blockers. Next stage is Ship.

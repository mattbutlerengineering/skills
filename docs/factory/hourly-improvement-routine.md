# Hourly improvement routine

The protocol for the `factory-hourly-improvement` scheduled cloud
routine: one bounded improvement to the factory's own process per hour,
taken from evidence to merged `main` inside a single run. Each run is
an [implement-queue](../../skills/implement-queue/SKILL.md) pass over
one issue the run files itself, under this repo's
[queue profile](../../.claude/implement-queue.md) and ADR-0096, which
is the Owner's standing consent for the merge it performs. It is built
on the mechanism ADR-0044 decided for the
[daily routine](improvement-routine.md) (a harness schedule, a
versioned playbook, a journal found by marker) and takes the
[toolsmith charter](../../factory/charters/toolsmith/CHARTER.md)'s
limits on what a change may be; no new ADR. Where this file and the
profile disagree on a merge, the profile wins; where this file and the
charter disagree on a change, the charter wins.

Two facts frame every run:

- **The merge is the profile's, never this file's.** A PR merges only
  when ADR-0087's four conditions hold on its current head: the
  required check present and green, a review passed by a reviewer
  distinct from the author or the fast path taken (ADR-0088), no
  gate-path file, no hold label. The routine reaches `main` by the
  profile's `merge-command` hook and by no other route.
- **This file is not the routine's to edit.** Amendments are proposed
  in the journal comment (§7) and applied by the human.

It differs from its two neighbours on purpose. The daily routine mines
the correction stream (its §6) and never merges; this routine does no
reflect mining, so a correction event is still the daily routine's to
quote and count. The [merge train](merge-train-routine.md) clears PRs
other people and routines leave open; this routine gates and merges
only the PR it opened, and any PR it leaves behind is the train's.

## Markers on GitHub

Every marker this file names obeys the rules in
`docs/factory/routine-markers.md` (the MCP-only environment; find by
both forms, write raw then verify, never create on doubt); read it
before the first GitHub read or write. This file's own: the journal's
`<!-- factory-hourly-improvement-journal -->`, the state line's
`<!-- hourly-improvement-state last-scan=... -->`, and the PR body's
`<!-- hourly-improvement-routine -->`. Each `gh` command below states
an intent; the environment may offer only the GitHub MCP tools or the
REST API through `gh api`, and either carries it out.

## 1 Preconditions and degrade ladder

Check in order; the first hit sets the run mode.

1. GitHub is unreachable — `gh auth status` fails and no GitHub MCP
   tool answers → record the failure in the session log and stop.
2. The repo variable `FACTORY_PAUSED` is `true` → **report-only
   mode**: orient, health sweep and journal; no branch, issue, PR or
   merge.
3. The queue profile is missing, or its `merge` key is not `auto` →
   **PR-only mode**: the run may open its PR but merges nothing; the
   PR is reported as awaiting the merge train or a human (ADR-0087).
4. An open PR authored by this routine exists — head branch prefixed
   `hourly/`, or body starting `<!-- hourly-improvement-routine -->` →
   **finish-first mode**: routine PRs never stack, so this run's work
   is that PR. Take it through the gate (§6). Review comments on it
   are addressed on its branch. A PR that cannot be made green with
   one small fix is closed with a comment naming the failing job; its
   issue stays open and gains `needs-human`.
5. `main` is red — any verify command fails on an untouched checkout,
   or the latest `check` run on `main` failed → the fix is this run's
   work (§4 rung 1).
6. Otherwise → **normal mode**.

## 2 Orient (read-only)

1. `CLAUDE.md` — the working conventions every change must satisfy.
2. The journal's latest comment (§7) and its
   `<!-- hourly-improvement-state last-scan=... -->` marker, plus the
   last seven days of comments, which name what this routine already
   tried. No marker → the scan window is 24 hours back.
3. `git log --oneline origin/main` since last-scan.
4. Open PRs (`gh pr list`), with age, author, and every issue a body
   `Closes`: those issues are covered and never picked.
5. The latest `check` runs on `main`.
6. The issue queue, `gh issue list --state open` (ADR-0083).
7. `docs/backlog.md`, the advisory seed inbox (ADR-0029).
8. `python3 one_owner.py` — read-only intel. Its findings are report
   material only: ADR-0061 makes each one a question for a human, so
   none is ever this routine's pick.

## 3 Health sweep

Run the verify suite at the repo root, exactly:

```
python3 -m unittest discover tests
python3 lint.py
python3 gates.py && python3 gates.py --selftest
```

Classify `main`: **green**; **red-on-main**; or **environment-broken**
(the commands cannot run at all — report the environment, don't chase
it).

## 4 Pick exactly one

Report-only and finish-first runs skip this section. Otherwise strict
priority; the first rung that matches wins, and everything below the
pick is report material:

1. **Red main.** The fix, if it fits the size bound; otherwise a quiet
   run with an escalation at the top of the journal comment.
2. **A ready queue item.** An open issue that is not a work order (no
   `wo:*` label), not a permanent-state issue (a journal, digest,
   queue or cost report), not labelled `ready-for-human`,
   `needs-human` or `needs-info`, not blocked by an open issue, not
   covered by an open PR, and not one whose own text asks for Owner
   design or Owner spend consent; oldest first. Only if it fits the
   size bound.
3. **A process gap with evidence.** The sources, in order, each
   reproduced in this run before it counts:
   - *An unenforced stated rule.* A rule written in `CLAUDE.md`, a
     `docs/factory/*-routine.md` protocol, the queue profile, a
     charter under `factory/charters/`, or a skill's `SKILL.md`, that
     no test under `tests/`, no `gates.py` detector and no `lint.py`
     check pins. Evidence: the quoted sentence and the search that
     found no assertion. The fix is a test under `tests/` that fails
     before the change and passes after it, with the rule's own words
     in the assertion.
   - *A stale knowledge page.* A `docs/kb/*.md` page whose `verified:`
     commit is behind `origin/main` on a path its `sources:` line
     names. The fix is the
     [knowledge-base](../../skills/knowledge-base/SKILL.md) skill's
     re-verification: re-read the sources, correct what drifted, move
     `verified:` to the tip, and keep the page's `CLAUDE.md` index line
     true.
   - *A backlog seed.* A `docs/backlog.md` line with no `(claimed:)`
     marker, S-sized, whose own text needs no Owner decision and that
     no open issue or PR covers. The fix lands with the seed marked
     claimed, in the grammar `docs/pipeline-protocol.md` gives, naming
     this run's issue.
4. **Nothing fits** → a quiet run. A quiet hour is a valid outcome;
   inventing work to fill the slot is how S-sized routines become
   unreviewable.

Two exclusions apply to every rung, and an excluded candidate goes
under Proposals instead:

- A fix that would touch a file the profile's `gate_paths` match, or
  any root module `factory_init.MIRRORS` lists (its mirror under
  `factory/templates/**` is a gate path), can never merge in-run.
- A candidate the journal shows this routine already tried in the last
  seven days (a closed PR, a flagged review, a denied merge) is not
  tried again.

The size bound is ADR-0034's S class: one file cluster, obvious test.
If scoping reveals more, don't start; propose the split.

## 5 Implement

- Branch `hourly/YYYY-MM-DDTHH-<slug>` off fresh `origin/main`.
- **The routine is the orchestrator, not the author.** When the
  environment can dispatch a subagent, one worker is dispatched with
  implement-queue's worker brief, the toolsmith charter's `Must never`
  list, and the pick's evidence; the routine session itself writes no
  code, so the agent that merges is never the agent that wrote the
  change. When dispatch is unavailable the routine implements
  directly, and §6 step 4 then governs.
- Failing test first, then the change. Full verify suite green before
  push; if the change turned it red and the fix isn't obvious, abandon
  the branch and report honestly.
- Conventional-commit title, matching repo history.
- File the run's issue — a plain issue with a `type:*` label, no
  `wo:*` label and no work-order id (ADR-0032) — carrying the
  evidence, the acceptance criteria the reviewer will check, and the
  line `Carrier: the hourly improvement routine`. Then open the PR.

PR body skeleton (the `No work order:` line and the `Closes #` line
together satisfy detector B's traceability contract):

```
<!-- hourly-improvement-routine -->
No work order: hourly improvement routine — <one-line reason>

Closes #<the run's issue>

## What / why
<the evidence that selected this work, and the change>

## Verification
<verify-suite result; the test that failed first>

## Merge danger
<Door: and Blast radius: lines, per the protocol's Pull request body section>
```

## 6 Gate and merge

Implement-queue's gate, run for this one PR under the profile:

1. **CI.** Wait for `required_check` (`check`) to be present and green
   on the PR's current head, polling no more than once a minute for at
   most thirty minutes. A rollup with no `check` run is not green.
   Still pending at the limit → report **awaiting CI** and stop; the
   next run finds the PR in finish-first mode.
2. **Holds.** A `hold_labels` label on the PR or its issue ends the
   gate: no review, no merge.
3. **Fast path.** Run the profile's `fast-path` hook in the branch
   checkout after `git fetch origin`. `fast-path: low-risk`, with no
   specialist matched, is the review (ADR-0088). Exit 2 fails closed:
   review.
4. **Review.** Otherwise dispatch the universal reviewer with the input
   [the reviewer contract](../../skills/implement-queue/references/reviewer-contract.md)
   defines. The reviewer is never the author; snapshot
   `git status --porcelain` before and after, and a changed checkout
   voids the verdict. An error or timeout is `error`, re-dispatched
   once and then held. A `flag` gets one fix on the same branch by a
   new worker and one more gate; a second `flag` labels the issue
   `needs-human`, comments the reviewer's output on the PR, and ends
   the run with no merge. When the routine authored the change itself
   and the fast path did not apply, there is no distinct reviewer to
   dispatch: stop at the PR and report it **awaiting review**; the
   merge train's Phase 0 reviews it.
5. **Gate paths.** Re-check the diff against the profile's
   `gate_paths`; §4 excluded them, and a match here still ends the run
   at the PR.
6. **Merge.** If the branch is behind `main`, run the `update-branch`
   hook and wait for a green `check` on the new head
   (`docs/kb/cross-pr-merge-hazards.md`). Re-check steps 1, 2 and 5 on
   that head, then run the `merge-command` hook. A merge the runtime
   denies is reported as **awaiting a human merge** with the denial,
   and is never retried by another route in this run (ADR-0087). Wait
   for the merge to land and for `main`'s `check` to finish; a red
   `main` afterwards is reported at the top of the journal comment and
   is the next run's rung 1.

Caps: one issue, one PR and one merge per run; one `update-branch`;
no retry of a denied merge.

## 7 Report and journal

This routine keeps its own journal issue, titled **Factory hourly
improvement journal**, body starting
`<!-- factory-hourly-improvement-journal -->`. Find it by marker, in
either form (§Markers on GitHub); create it only when that search
succeeded and found none. It is not pinned: GitHub allows three pinned
issues per repo and those slots are already contended.

A quiet run with green health leaves only the session log, so the
previous state marker stands and the next window simply extends.
Every other run writes exactly one journal comment:

```
<!-- hourly-improvement-state last-scan=<this run's start, ISO-8601 UTC> -->
**YYYY-MM-DD HH:MM — <merged | pr-open | finished-prior | report-only | stopped>**: <one line>
- Pick: <what and why, with the evidence — or which rung ended the search>
- Health: <verify suite, main CI, open PRs with age>
- Gate: <check result, fast path or reviewer verdict, merge result or denial>
- Proposals: <excluded candidates, splits, playbook diffs, escalations>
- Spend: <estimate for this run>
```

Spend is reported here and never appended to
`docs/factory/costs.jsonl`, exactly as ADR-0044 decided for the daily
routine.

## 8 Non-negotiables

Re-read before the first push and again before the merge.

- Never merge by any route but §6: the profile's four conditions on
  the current head, the `merge-command` hook, and no retry of a denied
  merge (ADR-0087). Never merge any other PR.
- Never change a file the profile's `gate_paths` match or a root
  module `factory_init.MIRRORS` lists; such a change goes under
  Proposals.
- Never run `trigger_eval.py`, `charter_replay.py`, or anything else
  needing the `claude` CLI or an API key beyond the worker and reviewer
  dispatch §5 and §6 define. Never write `evals/results/**` and never
  change LEDGER maturity (ADR-0012, ADR-0019).
- Never create a work-order issue or write a work-order id ahead of
  its breakdown row (ADR-0032).
- Never weaken, skip or delete a test, detector, eval or charter to go
  green — the failing case is the finding.
- Never edit this file, `docs/factory/routine-markers.md`,
  `docs/factory/improvement-routine.md`, the queue profile, any
  schedule, another routine's journal, or the version in
  `.claude-plugin/plugin.json` (ADR-0095).
- Caps: one issue, one PR, one merge, S size, branch prefix `hourly/`,
  body marker `<!-- hourly-improvement-routine -->`,
  conventional-commit titles.

## 9 Amending this playbook

The routine proposes; the human applies. A proposed amendment is a
unified diff under Proposals with one line of rationale. Schedule
changes — cron, prompt, model — are proposed the same way and applied
by the human. The schedule prompt duplicates the hard limits (one
issue, one PR, one merge through the profile's hook, never a gate path,
never a denied merge retried, no self-edit) as defense in depth for the
hour this file is unreadable; a change to any of those updates prompt
and playbook together.

## Trigger

**Created 2026-10-15.** A scheduled trigger is recurring paid spend,
and the Owner explicitly asked for this one on 2026-10-15, in session
("create a routine that runs every hour and makes improvements to our
process. opens a pr then merges it"). Nothing in this file authorizes
creating, editing or running a trigger, and no agent or routine does so
on the strength of this file. It takes ADR-0044's shape, as the merge
train's does:

- **Name:** `factory-hourly-improvement`.
- **Trigger id:** `trig_014pdzwD8DaDfYuZ51NGj3dX`, created 2026-10-15 21:51 UTC.
  First scheduled run 2026-10-15 22:07 UTC.
- **Cadence:** every hour, stored as `7 * * * *` UTC — the
  platform's minimum interval, and the cadence the Owner asked for.
- **Model:** Sonnet (`claude-sonnet-5-5`), as the other routines; the
  worker and reviewer dispatches use the same model.
- **Connectors:** none. The create call attaches every account
  connector by default; they are cleared before any run.
- **Environment:** `git`, and GitHub through the GitHub MCP tools; the
  `gh` CLI may be absent, and where it is present its `gh pr` and
  `gh issue` subcommands may be refused by the proxy while `gh api`
  REST calls succeed. Markers follow §Markers on GitHub. Subagent
  dispatch uses the `Agent` tool. The `merge-command` hook needs the
  session permission ADR-0096 names; until it holds, every run ends
  **awaiting a human merge** and says so.
- **Prompt:** a thin pointer to this file, plus the duplicated hard
  limits §9 lists.
- **Reporting:** the marker-found journal issue in §7.
- **Spend:** reported in the journal; excluded from the cost ledger
  exactly as ADR-0044 decided.

## Decisions

**2026-10-15: created by Owner decision**, in session, in the words
§Trigger quotes. The Owner's ask was a routine that opens a PR and then
merges it; the design meets it inside the rules already in force rather
than beside them: the merge is ADR-0096's standing consent through the
queue profile, the reviewer is distinct from the author as ADR-0036
requires, and a docs-only change takes ADR-0088's fast path. The daily
routine and the merge train are unchanged; whether the daily routine
stays worth its slot once this one has run for a while is the Owner's
later call.

# Daily improvement routine

The complete daily protocol for the `factory-daily-improvement`
scheduled cloud routine (ADR-0044) — the factory improving itself on a
cadence. The routine is the
[toolsmith charter](../../factory/charters/toolsmith/CHARTER.md) operating
on a schedule: same mission (mine the correction stream, build rules and
tooling), same grants, same `Must never` list. Where this file and the
charter disagree, the charter wins. This protocol instantiates the
reflect loop ADR-0033 names — "the correction stream is the raw material
the reflect loop turns into charter rules" — and never built.

Two facts frame every run:

- **One bounded improvement per day, at most.** The routine opens at
  most one PR and files at most one issue per run, and a human merges
  everything: the routine is always the author, so ADR-0036's
  independent-reviewer merge path is closed to it by construction.
- **This file is not the routine's to edit.** An agent cannot widen its
  own authority (the reasoning behind ADR-0036, applied to the routine's
  own constitution). Amendments are proposed as diffs in the daily
  report (§9) and applied by the human.

## 1 Preconditions and degrade ladder

Check in order; the first hit sets the run mode.

1. `gh auth status` fails → nothing on GitHub is reachable. Record the
   failure in the session log and stop.
2. The repo variable `FACTORY_PAUSED` is `true` (`gh variable list`) →
   **propose-only mode**. The circuit breaker (ADR-0034) formally gates
   the assembler, but a paused factory is no place to open new work.
   Orient, health sweep, reflect, and journal still run; no branch, no
   issue, no PR.
3. An open PR authored by this routine exists — head branch prefixed
   `routine/`, or body starting `<!-- improvement-routine -->` →
   **no-new-PR mode**: routine PRs never stack. If that PR has
   unaddressed review comments, today's work is addressing them (push to
   its branch — the one case where the routine touches an existing PR).
   Otherwise the day is propose-only.
4. Otherwise → **normal mode**.

## 2 Orient (read-only)

Read, in order:

1. `CLAUDE.md` — the working conventions every change must satisfy.
2. The pinned gate-queue digest: the open issue whose body starts with
   `<!-- factory-gate-digest -->`. Found by marker, never by number —
   the same idiom `gate_digest.py` itself uses.
3. The journal's latest routine comment (§7) and its
   `<!-- routine-state last-scan=... -->` marker. Missing marker or
   first run → the scan window defaults to 7 days back.
4. `git log --oneline` on main since last-scan.
5. Open PRs (`gh pr list`), with age. Note the routine's own, if any
   (that decision already happened in §1).
6. The latest CI runs on main (`gh run list --branch main --limit 5`).
7. `LEDGER.md` — skills stuck at draft or used-once and bouncy trigger
   scores are Proposals material: paid eval runs are proposed, never
   run (§8).
8. `.beads/issues.jsonl` — the committed queue export. Record its
   freshness (`git log -1 --format=%cs -- .beads/issues.jsonl`); if
   older than 7 days, downweight rung 2 of §4 and say so in the report.
   The export is read-only intel: the cloud environment runs neither
   `bd` nor dolt, and the routine never edits `.beads/**`. Status
   changes it would have made (claim, close) go in the report for the
   human to apply.

## 3 Health sweep

Run the verify suite at the repo root, exactly:

```
python3 -m unittest discover tests
python3 lint.py
python3 gates.py && python3 gates.py --selftest
```

Classify main: **green**; **red-on-main** (any command fails on an
untouched checkout, or the latest main CI run failed); or
**environment-broken** (the commands cannot run at all — report the
environment, don't chase it).

## 4 Pick exactly one

Modes from §1 gate this section: propose-only and no-new-PR days skip
straight to §6. In normal mode, strict priority — the first rung that
matches wins, and everything below the pick becomes report material,
never work:

1. **Red main.** The fix is the day's work if it fits the size bound;
   otherwise propose-only plus an escalation at the top of the journal
   comment.
2. **A ready queue item.** Eligible: status `open` in the export, no
   unresolved blocking dependency, priority order (P0 first), oldest
   first. Only if it fits the size bound.
3. **A graduated reflect candidate** (§6): a candidate rule with two or
   more distinct correction events across the journal history. The edit
   lands in `factory/charters/<role>/CHARTER.md` or
   `skills/<slug>/SKILL.md` — never a gate-change path. Prefer a
   detector to a paragraph (charter, actions 2): when the rule is
   machine-checkable and the detector still fits the size bound, ship
   the detector and its failing-first test instead of prose.
4. **Nothing fits** → propose-only day. A quiet day is a valid outcome;
   inventing work to fill the slot is how S-sized routines become
   unreviewable.

The size bound is ADR-0034's S class: one file cluster, obvious test.
If scoping reveals more, don't start — propose the split in the report.
Budgets pressuring decompose into smaller work is the discipline the
pipeline wants everywhere; the routine gets no exemption.

## 5 Implement (TDD)

- Branch `routine/YYYY-MM-DD-<slug>` off fresh `origin/main`.
- Failing test first, then the change — the same discipline the SWE and
  toolsmith charters demand. Full verify suite green before push; if
  the routine's own change turned it red and the fix isn't obvious,
  abandon the branch and report honestly.
- If anything under `factory/templates/**` or any root file in
  `factory_init.MIRRORS` changed: `python3 factory_init.py
  update-manifest`, manifest committed with the change (detector E).
- Conventional-commit title, matching repo history (`fix(gates): ...`,
  `chore(factory): ...`).
- File the day's improvement issue — a plain issue, no `wo:*` labels
  and no work-order id: a work-order issue exists only downstream of a
  breakdown row (ADR-0032). Then open the PR.

PR body skeleton (the first two lines satisfy detector B's
traceability contract):

```
<!-- improvement-routine -->
No work order: daily improvement routine — <one-line reason>

Closes #<the improvement issue>

## What / why
<the signal that selected this work, and the change>

## Verification
<verify-suite result; the test that failed first>

## Daily report
<the §7 sections: Health, Queue, Reflect, Proposals>
```

Cite a real work-order id in place of the `No work order:` line only
when the PR genuinely implements that breakdown row. Beads tracker ids
(`wo-` prefixed slugs) are not work-order ids; they neither satisfy nor
trip detector B, and belong in prose only as queue references.

## 6 Reflect (every run, every mode)

Harvest the correction stream since last-scan:

- Reviews in CHANGES_REQUESTED state, review comments, and issue
  comments on PRs updated inside the window.
- Comments on gate-change-path PRs (`docs/adr/**`, a run's `prd.md`,
  `architecture.md`, `docs/design/**`) — these are gate 1/2 rejections
  (ADR-0033).
- Issues labeled `wo:failed`, `needs-human`, or `budget-exhausted`.

Rules, all from the toolsmith charter:

- **Quote, don't summarize.** Each harvested correction enters the
  report as the quoted comment plus its permalink plus a one-line
  candidate rule. Evidence is quoted, never summarized into existence.
- **Count before writing.** One rejection is an anecdote. A candidate
  becomes PR-eligible (§4 rung 3) only at two or more distinct
  correction events across the journal history.
- **Escalate, never apply.** A pattern implying a gate change, scope
  change, or autonomy graduation is human-only (ADR-0033); it goes
  under Proposals, and nowhere else.

## 7 Report and journal

The journal is one pinned issue titled **Factory improvement journal**,
body starting `<!-- factory-improvement-journal -->`. Find it by marker
among open issues; create and pin it if absent; re-pin if unpinned —
the same create-or-adopt-and-heal protocol the gate digest uses.

Exactly one journal comment per run:

```
<!-- routine-state last-scan=<this run's start, ISO-8601 UTC> -->
**YYYY-MM-DD — <PR | comments-addressed | propose-only | stopped>**: <one line>
- Pick: <what and why — or which rung ended the search>
- Health: <verify suite, main CI, open PRs with age>
- Queue: <export freshness; top ready items>
- Reflect: <corrections harvested; candidate rules with counts>
- Proposals: <eval runs to fund, splits, playbook diffs, escalations>
- Spend: <estimate for this run>
```

On PR days the PR body carries the full report and the journal comment
is the one-liner plus a link — but the state marker is always in the
journal comment: the journal is the routine's only memory.

Spend is reported here and never appended to
`docs/factory/costs.jsonl`. Ledger rows are work-order-keyed and
detector-validated (ADR-0034, ADR-0041, ADR-0043); an unkeyed routine
row is exactly the drift detector G exists to catch.

## 8 Non-negotiables

The routine re-reads this list before pushing anything.

- Never merge any PR, including its own (ADR-0033 gate 3; ADR-0036
  requires a non-authoring reviewer; charter `Must never`).
- Never touch a gate-change path in a routine PR: `docs/adr/**`, a
  run's `prd.md`, `architecture.md`, `docs/design/**` (ADR-0033,
  ADR-0036). Needed changes go under Proposals.
- Never run `trigger_eval.py`, `charter_replay.py`, or anything needing
  the `claude` CLI or an API key. Never write `evals/results/**`
  (append-only, real runs only) and never change LEDGER maturity
  (CLAUDE.md eval honesty; ADR-0012, ADR-0019).
- Never create a work-order issue or write a work-order id ahead of its
  breakdown row (ADR-0032; detectors B and C enforce).
- Never weaken, skip, or delete a test, detector, eval, or charter to
  go green — the failing case is the finding (charter).
- Never edit this file, `.beads/**`, or the schedule.
- Caps: one PR, one issue, S size, branch prefix `routine/`, body
  marker `<!-- improvement-routine -->`, conventional-commit titles.

## 9 Amending this playbook

The routine proposes; the human applies. A proposed amendment is a
unified diff under Proposals with one line of rationale, ideally traced
to a correction event (§6). Changes to the schedule itself — cron,
prompt, model — are proposed the same way and applied by the human via
the harness scheduler. The schedule prompt deliberately duplicates four
hard limits (one PR, never merge, no paid evals, no self-edit) as
defense in depth for the day this file is unreadable; a change to any
of those must update prompt and playbook together.

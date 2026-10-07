# Weekly queue-groomer routine

The protocol for the `factory-weekly-queue-groomer` scheduled cloud
routine — one of the three roster routines issue #437 settled, built on
the mechanism ADR-0044 already decided for the daily routine (no new
ADR; `docs/features/factory-evolution-v1/architecture.md` §Decisions
records why). It works in the
[planner charter](../../factory/charters/planner/CHARTER.md)'s territory
— the dispatch plane — under that charter's `Must never` list. Where
this file and the charter disagree, the charter wins.

Its mission is grooming the ready queue: finding work-order issues
(`wo:*`-labeled) that have gone stale or stuck, and keeping the seed
inbox (`docs/backlog.md`) honest. It is not reflect-loop mining (the
[daily improvement routine](improvement-routine.md) and the
[weekly retro/reflect routine](retro-reflect-routine.md) own that), and
it does not duplicate the reconcile sweep (`sweeps.py reconcile`), which
already files dispatch-plane/knowledge-plane disagreements (ADR-0032,
ADR-0060) as intake issues.

Two facts frame every run:

- **The groomer reports; humans move work orders.** It never adds,
  removes, or flips a `wo:*` label. Lifecycle labels belong to the
  validator, the assembler and the three human gates (ADR-0033); a
  groomer that relabels is a second, unreviewed dispatcher. Every label
  change it wants is a proposal in the report.
- **This file is not the routine's to edit.** Amendments are proposed as
  diffs in the weekly report (§8) and applied by the human.

This file is the minimum needed to run once (issue #438 defers full
protocol rigor to the routine's own first runs); it grows by PR from
what those runs report.

## 1 Preconditions and degrade ladder

Check in order; the first hit sets the run mode.

1. `gh auth status` fails → record the failure in the session log and
   stop.
2. `FACTORY_PAUSED` is `true` (`gh variable list`) → **propose-only
   mode**: orient, survey and journal; no branch, no PR. A paused
   factory's queue is expected to look stale — say so rather than
   flagging every item.
3. An open PR authored by this routine exists — head branch prefixed
   `routine-groom/`, or body starting `<!-- queue-groomer-routine -->` →
   **no-new-PR mode**. Unaddressed review comments on it are this
   week's work; otherwise propose-only.
4. Otherwise → **normal mode**.

## 2 Orient (read-only)

1. `CLAUDE.md`, and `docs/pipeline-protocol.md` §"Seed backlog
   (optional)" — the backlog's grammar and its append-only producer
   rule.
2. This routine's journal (§6): its latest comment's
   `<!-- queue-groomer-state last-scan=... -->` marker. First run → no
   prior state; survey everything.
3. Every open issue carrying a `wo:*` label (`gh issue list --label
   ...`, one call per lifecycle label), with label-event history for
   the age of its current label.
4. The breakdown rows those issues mirror (`docs/**/breakdown.md`) —
   read only, to know whether a row is checked and what blocks it.
5. Open PRs, and which work-order issue each closes.
6. The latest open reconcile-sweep intake, if any — its findings are
   already filed and are cited, not re-reported.
7. `docs/backlog.md`, and the run directories its `(from: ...)` and
   `(claimed: ...)` markers name.

## 3 Survey

Classify each open work-order issue; one line per finding, with the
issue link, its current label, and how long it has held it:

- **Stuck in progress** — `wo:in-progress` with no open PR closing it
  and no commit or comment in 7 days.
- **Unblocked but still blocked** — `wo:blocked` whose breakdown row's
  blockers are all checked or closed.
- **Waiting on nobody** — `wo:ready-for-agent` untouched for 14 days,
  or `wo:needs-review` whose PR has no review activity in 7 days.
- **Failed and forgotten** — `wo:failed` with no follow-up issue, PR,
  or comment since the failure.

And the seed inbox:

- **Dead claims** — `(claimed: <run-ref>)` naming a run with no run
  directory, or a run whose directory holds only its first artifact
  and has not changed in 30 days.
- **Already resolved** — a seed whose named condition no longer holds
  on main (cite the commit or PR that fixed it).
- **Duplicates** — two seeds naming the same condition.

A finding the reconcile sweep already filed is listed by its intake
link and nothing more. The thresholds above are starting values; tune
them by amendment (§8) from what the first runs report.

## 4 Pick exactly one

Modes from §1 gate this section. In normal mode, first match wins:

1. **Backlog hygiene PR** — an append-only edit to `docs/backlog.md`
   that records resolved seeds, dead claims, or duplicates as new,
   well-formed `session:` lines, following the file's own precedent (a
   "Resolved —" line that names the seeds it closes). Existing lines are
   never rewritten or deleted: the producer rule forbids it, and a
   rewritten origin marker breaks claim provenance. `python3 lint.py`'s
   backlog grammar check must pass.
2. **Nothing to append** → propose-only week. The survey is still the
   run's output.

Work-order findings are never a PR: they are report lines with the
exact label change or comment the groomer proposes, for a human to
apply.

## 5 Implement

Branch `routine-groom/YYYY-MM-DD-<slug>` off fresh `origin/main`; full
verify suite green before push. File one plain hygiene issue (no
`wo:*` labels, no work-order id — ADR-0032) naming the seeds the PR
addresses, then the PR; detector B requires the `Closes #N` link even
under the `No work order:` waiver. PR body opening:

```
<!-- queue-groomer-routine -->
No work order: weekly queue-groomer routine — <one-line reason>

Closes #<the hygiene issue>
```

followed by What / why (each appended line and the evidence behind it),
Verification, and the §6 report.

## 6 Report and journal

This routine keeps its own journal issue, titled **Factory queue-groomer
journal**, body starting `<!-- factory-queue-groomer-journal -->`. Find
it by marker; create it if absent. It is not pinned by default: GitHub
allows three pinned issues per repo and those slots are already
contended. Marker lookup never depends on the pin.

Exactly one journal comment per run:

```
<!-- queue-groomer-state last-scan=<this run's start, ISO-8601 UTC> -->
**YYYY-MM-DD — <PR | comments-addressed | propose-only | stopped>**: <one line>
- Pick: <what and why — or why nothing>
- Queue: <open work orders by label; each finding with age and proposed action>
- Seeds: <dead claims, resolved, duplicates>
- Already filed: <reconcile-sweep intakes cited>
- Proposals: <label flips and comments for a human; threshold amendments>
- Spend: <estimate for this run>
```

Spend is reported here and never appended to `docs/factory/costs.jsonl`,
exactly as ADR-0044 decided for the daily routine.

## 7 Non-negotiables

Re-read before pushing anything.

- Never merge any PR, including its own.
- Never add, remove, or flip a `wo:*` label, never close or reopen a
  work-order issue, never comment on one — proposals only.
- Never create a work-order issue or write a work-order id ahead of its
  breakdown row (ADR-0032), and never edit a `breakdown.md`.
- Never rewrite or delete an existing `docs/backlog.md` line; never add
  a `(claimed: ...)` marker — only `idea` and `capture` claim seeds.
- Never touch a gate-change path: `docs/adr/**`, a run's `prd.md`,
  `architecture.md`, `docs/design/**`.
- Never run anything needing the `claude` CLI or an API key.
- Never edit this file, `.beads/**`, any schedule, or another routine's
  journal.
- Caps: one PR, one issue, S size, branch prefix `routine-groom/`, body marker
  `<!-- queue-groomer-routine -->`.

## 8 Amending this playbook

The routine proposes; the human applies. A proposed amendment is a
unified diff under Proposals with one line of rationale. Schedule
changes — cron, prompt, model — are proposed the same way and applied
by the human.

## Trigger

**Created 2026-09-29.** A scheduled trigger is recurring paid spend, and
the owner explicitly approved this one on 2026-09-29, as the pilot for
the roster routines. Nothing in this file authorizes creating, editing
or running a trigger, and no agent or routine does so on the strength of
this file. The trigger takes ADR-0044's shape:

- **Name:** `factory-weekly-queue-groomer`.
- **Trigger id:** `trig_01W5PgiQb4G2qwMXnNVFtACx`, created 2026-09-29
  04:11 UTC. First run 2026-09-30 13:17 UTC.
- **Cadence:** weekly — Wednesday 13:17 UTC (`17 13 * * 3`), off the
  daily routine's slot and the other roster routines' days.
- **Model:** Sonnet (`claude-sonnet-5-5`).
- **Connectors:** none — no MCP connectors; `gh` and `git` only. The
  create call attaches every account connector by default; they were
  cleared at 04:11:48 UTC, before any run.
- **Prompt:** a thin pointer to this file, plus duplicated hard limits
  as defense in depth: one PR, never merge, never relabel a work order,
  no self-edit. A change to any of those updates prompt and playbook
  together.
- **Reporting:** the marker-found journal issue in §6.
- **Spend:** reported in the journal; excluded from the cost ledger
  exactly as ADR-0044 decided.

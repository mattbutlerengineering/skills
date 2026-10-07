# Weekly doc-gardener routine

The protocol for the `factory-weekly-doc-gardener` scheduled cloud
routine — one of the three roster routines issue #437 settled, built on
the mechanism ADR-0044 already decided for the daily routine (no new
ADR; `docs/features/factory-evolution-v1/architecture.md` §Decisions
records why). It is the
[toolsmith charter](../../factory/charters/toolsmith/CHARTER.md) tending
the factory's own documentation, under that charter's `Must never`
list. Where this file and the charter disagree, the charter wins.

Its mission is documentation hygiene in the gaps the offline detectors
leave: stale cross-references, drifted indexes, and `LEDGER.md` upkeep.
It is not reflect-loop mining (the
[daily improvement routine](improvement-routine.md) and the
[weekly retro/reflect routine](retro-reflect-routine.md)) and not queue
grooming (the [weekly queue-groomer routine](queue-groomer-routine.md)).

Two facts frame every run:

- **What a detector already gates is not the gardener's.** A finding
  `gates.py` or `lint.py` reports makes main red, and red main is the
  daily routine's rung 1. The gardener works only on rot no detector
  sees — and when a class of rot is machine-checkable, the better
  outcome is a proposed detector, not a weekly hand-fix forever.
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
   mode**: orient, survey and journal; no branch, no issue, no PR.
3. An open PR authored by this routine exists — head branch prefixed
   `routine-garden/`, or body starting `<!-- doc-gardener-routine -->` →
   **no-new-PR mode**. Unaddressed review comments on it are this
   week's work; otherwise propose-only.
4. The verify suite is red on an untouched checkout → **propose-only
   mode**: fixing red main is the daily routine's work, and a doc PR
   stacked on red main cannot show its own verification.
5. Otherwise → **normal mode**.

## 2 Orient (read-only)

1. `CLAUDE.md` and `CONTEXT.md` — conventions, and the canonical
   vocabulary every living doc should use.
2. This routine's journal (§6): its latest comment's
   `<!-- doc-gardener-state last-scan=... -->` marker. Missing marker or
   first run → the window is 7 days back.
3. `git log --name-status` on main since last-scan — renamed, moved, or
   deleted paths and symbols are where references rot first.
4. The verify suite, exactly as the daily routine's §3 runs it, to know
   what the detectors already cover this week.
5. The detector roster in `gates.py`'s module docstring and the
   `check_*` functions in `lint.py` — the boundary of §3.

## 3 Survey

Look for rot of these kinds, outside what §2.5's checks already gate:

- **Stale code references.** Backticked paths, `file.py:NN` line
  citations, function or constant names, and counts ("the fourteen
  mirrored tools") in living docs that no longer match the repo.
  Detector I checks markdown link targets only; a path in a code span
  is invisible to it.
- **Drifted indexes.** A hand-kept list that has fallen behind what it
  lists — the "Where things are decided" section of `CLAUDE.md` and
  `AGENTS.md`, the charter table in `factory/CHARTERS.md`, the plugin
  description's skill list — wherever no detector already holds the
  list to its source. (`docs/adr/README.md` is held by detector D and
  the README skill table by `lint.py`; those are out of scope.)
- **Vocabulary drift.** A living doc using a term `CONTEXT.md` lists
  under `_Avoid_` where it means the canonical term.
- **`LEDGER.md` upkeep.** A skill whose evidence column trails the real
  runs that exercised it (a completed run directory that used the skill
  but is not cited), or a trigger-eval cell pointing at an older result
  than the newest recorded one for that skill. These are always
  proposals: maturity graduates only by a real run and a human-applied
  edit (ADR-0012, ADR-0019), never by the gardener.

Living docs are `README.md`, `CLAUDE.md`, `AGENTS.md`, `CONTEXT.md`,
`docs/pipeline-protocol.md`, `docs/factory/**` (except the routine
protocol files), and `factory/CHARTERS.md`. Run artifacts, ADRs and
eval results are historical records: a stale reference there is
reported, never edited.

## 4 Pick exactly one

Modes from §1 gate this section. In normal mode, first match wins:

1. **A stale reference or drifted index in a living doc**, fixable in
   one file cluster: correct it to match the repo, citing the commit
   that moved the thing referred to.
2. **Nothing fits** → propose-only week. The survey is still the run's
   output.

If the same class of rot shows up in two consecutive runs, propose a
detector for it under Proposals in addition to (never instead of)
fixing this week's instance. The size bound is ADR-0034's S class; one
doc cluster per PR, never a sweep across the tree.

## 5 Implement

Branch `routine-garden/YYYY-MM-DD-<slug>` off fresh `origin/main`; full
verify suite green before push (a doc fix can still trip detector C or
I). File one plain issue naming the rot (no `wo:*` labels, no
work-order id — ADR-0032), then the PR; detector B requires the
`Closes #N` link even under the `No work order:` waiver. PR body
opening:

```
<!-- doc-gardener-routine -->
No work order: weekly doc-gardener routine — <one-line reason>

Closes #<the gardener issue>
```

followed by What / why (the stale text, what it should say, and the
commit that moved it), Verification, and the §6 report.

## 6 Report and journal

This routine keeps its own journal issue, titled **Factory doc-gardener
journal**, body starting `<!-- factory-doc-gardener-journal -->`. Find
it by marker; create it if absent. It is not pinned by default: GitHub
allows three pinned issues per repo and those slots are already
contended. Marker lookup never depends on the pin.

Exactly one journal comment per run:

```
<!-- doc-gardener-state last-scan=<this run's start, ISO-8601 UTC> -->
**YYYY-MM-DD — <PR | comments-addressed | propose-only | stopped>**: <one line>
- Pick: <what and why — or why nothing>
- Health: <verify suite result on the untouched checkout>
- Rot: <each finding: file, line, stale text, what it should say>
- Ledger: <proposed LEDGER.md edits, with the run evidence for each>
- Proposals: <detectors for recurring rot; fixes in ADRs or run artifacts for a human>
- Spend: <estimate for this run>
```

Spend is reported here and never appended to `docs/factory/costs.jsonl`,
exactly as ADR-0044 decided for the daily routine.

## 7 Non-negotiables

Re-read before pushing anything.

- Never merge any PR, including its own.
- Never touch a gate-change path: `docs/adr/**`, a run's `prd.md`,
  `architecture.md`, `docs/design/**`; never edit any other run
  artifact either.
- Never change LEDGER maturity or its evidence column, and never write
  `evals/results/**` (CLAUDE.md eval honesty).
- Never run `trigger_eval.py`, `charter_replay.py`, or anything needing
  the `claude` CLI or an API key.
- Never edit `skills/**` — a skill-text change needs a plugin version
  bump and belongs under Proposals.
- Never weaken, skip, or delete a test or detector to make a doc pass.
- Never create a work-order issue or write a work-order id ahead of its
  breakdown row (ADR-0032).
- Never edit this file or any routine protocol file, `docs/backlog.md`,
  `.beads/**`, any schedule, or another routine's journal.
- Caps: one PR, one issue, S size, branch prefix `routine-garden/`,
  body marker `<!-- doc-gardener-routine -->`.

## 8 Amending this playbook

The routine proposes; the human applies. A proposed amendment is a
unified diff under Proposals with one line of rationale. Schedule
changes — cron, prompt, model — are proposed the same way and applied
by the human.

## Trigger

**2026-09-29: deferred by owner decision** while the
[queue groomer](queue-groomer-routine.md)'s trigger pilots, so one weekly
run bounds the new spend while its journal shows real cost. The deferral
is not an approval: nothing authorizes creating this trigger.

**Not yet created.** A scheduled trigger is recurring paid spend, and
creating one awaits the owner's explicit approval. Nothing in this file
authorizes creating it, and no agent or routine creates it on the
strength of this file. When the owner approves, the trigger takes
ADR-0044's shape:

- **Name:** `factory-weekly-doc-gardener`.
- **Cadence:** weekly — proposed Friday 13:17 UTC (`17 13 * * 5`), off
  the daily routine's slot and the other roster routines' days.
- **Model:** Sonnet.
- **Connectors:** none — no MCP connectors; `gh` and `git` only.
- **Prompt:** a thin pointer to this file, plus duplicated hard limits
  as defense in depth: one PR, never merge, never change LEDGER
  maturity, no self-edit. A change to any of those updates prompt and
  playbook together.
- **Reporting:** the marker-found journal issue in §6.
- **Spend:** reported in the journal; excluded from the cost ledger
  exactly as ADR-0044 decided.

Once it exists, a human PR records its trigger id in this section.

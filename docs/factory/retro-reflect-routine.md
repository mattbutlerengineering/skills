# Weekly retro/reflect routine

The protocol for the `factory-weekly-retro-reflect` scheduled cloud
routine — one of the three roster routines issue #437 settled, built on
the mechanism ADR-0044 already decided for the daily routine (no new
ADR; `docs/features/factory-evolution-v1/architecture.md` §Decisions
records why). It is the
[toolsmith charter](../../factory/charters/toolsmith/CHARTER.md) run on a
weekly cadence: same mission, same grants, same `Must never` list. Where
this file and the charter disagree, the charter wins.

Its mission is the deeper pass over the correction stream that the
[daily improvement routine](improvement-routine.md)'s §6 Reflect cannot
make from inside one day's window. The daily routine quotes each
correction it sees and counts a candidate rule against the journal
history; this routine reads the whole week at once, reconciles the
daily's candidate rules against each other and against the toolsmith
queue, and graduates what the daily's per-day view keeps missing — the
same rule phrased two ways on two days, or a pattern whose events all
fall in different daily windows.

Two facts frame every run, as for the daily routine:

- **One bounded improvement per week, at most.** At most one PR and one
  issue per run, and a human merges everything (ADR-0033 gate 3;
  ADR-0036's independent-reviewer path is closed to the author).
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
   mode**: orient, consolidate and journal; no branch, no issue, no PR.
3. An open PR authored by this routine exists — head branch prefixed
   `routine-retro/`, or body starting `<!-- retro-reflect-routine -->` →
   **no-new-PR mode**. Unaddressed review comments on it are this
   week's work (push to its branch); otherwise propose-only.
4. An open PR authored by the daily routine (`routine/` prefix or
   `<!-- improvement-routine -->` marker) already lands a charter or
   skill rule → that candidate is taken; exclude it from §4 and say so.
5. Otherwise → **normal mode**.

## 2 Orient (read-only)

1. `CLAUDE.md` — the conventions every change must satisfy.
2. This routine's journal (§6): its latest comment's
   `<!-- retro-reflect-state last-scan=... -->` marker. Missing marker or
   first run → the window is 7 days back.
3. The Factory improvement journal (body marker
   `<!-- factory-improvement-journal -->`) — every daily comment inside
   the window, and the Reflect lines of its whole history. These are the
   daily routine's candidate rules with their counts.
4. The toolsmith queue (body marker `<!-- factory-toolsmith-queue -->`)
   — the weekly `rejection_mining.py` harvest of gate rejections and
   change-requested reviews, recurrence counts first.
5. The raw correction stream inside the window, exactly as the daily §6
   defines it: CHANGES_REQUESTED reviews and review/issue comments on
   PRs updated in the window, comments on gate-change-path PRs, and
   issues labeled `wo:failed`, `needs-human`, or `budget-exhausted`.
6. `factory/charters/*/CHARTER.md` and `skills/*/SKILL.md` — so a
   candidate that an existing rule already covers is recognized as a
   recurrence of a *broken* rule, not a new one.

Every marker lookup is by body marker, never by issue number — the gate
digest's idiom.

## 3 Consolidate

Build one candidate register for the week:

- **Merge restatements.** Two daily candidates, or a daily candidate and
  a toolsmith-queue entry, that name the same rule become one candidate
  whose event list is the union. Keep every quoted comment and permalink
  — evidence is quoted, never summarized into existence.
- **Count distinct correction events**, not mentions: the same comment
  quoted on two days is one event.
- **Classify each candidate**: *new rule*, *existing rule not followed*
  (quote the rule and the violation), or *gate/scope/graduation
  implication* (escalate only — ADR-0033 keeps those human-only).

## 4 Pick exactly one

Modes from §1 gate this section. In normal mode, first match wins:

1. **A graduated candidate** — two or more distinct correction events
   across the whole history, not already landed or in an open PR. Prefer
   a detector and its failing-first test to a paragraph when the rule is
   machine-checkable and still fits the size bound; otherwise a charter
   or `SKILL.md` edit.
2. **Nothing graduates** → propose-only week. The consolidated register
   is still the run's output.

The size bound is ADR-0034's S class. If scoping reveals more, propose
the split instead of starting.

## 5 Implement

As the daily §5, with this routine's names: branch
`routine-retro/YYYY-MM-DD-<slug>` off fresh `origin/main` (deliberately
not `routine/`, so the daily's §1 check does not mistake it for its own
PR); failing test first; full verify suite green before push; manifest
regenerated if a mirrored file changed. File one plain improvement
issue (no `wo:*` labels, no work-order id — ADR-0032), then the PR, body
opening:

```
<!-- retro-reflect-routine -->
No work order: weekly retro/reflect routine — <one-line reason>

Closes #<the improvement issue>
```

followed by What / why (the quoted events that graduated the rule),
Verification, and the §6 report.

## 6 Report and journal

This routine keeps its own journal issue, titled **Factory retro/reflect
journal**, body starting `<!-- factory-retro-reflect-journal -->`. Find
it by marker; create it if absent. It is not pinned by default: GitHub
allows three pinned issues per repo and the gate digest, the improvement
journal and the toolsmith queue already contend for them. Marker lookup
never depends on the pin. A separate issue — rather than comments on the
improvement journal — keeps the daily routine's "latest comment carries
the state marker" read intact.

Exactly one journal comment per run:

```
<!-- retro-reflect-state last-scan=<this run's start, ISO-8601 UTC> -->
**YYYY-MM-DD — <PR | comments-addressed | propose-only | stopped>**: <one line>
- Pick: <what and why — or why nothing graduated>
- Register: <candidates, merged restatements, event counts, class>
- Broken rules: <existing rules the week's corrections show unfollowed>
- Proposals: <escalations, charter/playbook diffs, splits>
- Spend: <estimate for this run>
```

Spend is reported here and never appended to `docs/factory/costs.jsonl`
— ADR-0044's decision, for the same reason: ledger rows are
work-order-keyed and detector-validated, and an unkeyed routine row is
drift detector G exists to catch.

## 7 Non-negotiables

Re-read before pushing anything.

- Never merge any PR, including its own.
- Never touch a gate-change path: `docs/adr/**`, a run's `prd.md`,
  `architecture.md`, `docs/design/**`. Needed changes go under
  Proposals.
- Never run `trigger_eval.py`, `charter_replay.py`, or anything needing
  the `claude` CLI or an API key; never write `evals/results/**`; never
  change LEDGER maturity.
- Never create a work-order issue or write a work-order id ahead of its
  breakdown row (ADR-0032).
- Never weaken, skip, or delete a test, detector, eval, or charter rule
  to make a candidate fit — the failing case is the finding.
- Never edit this file, `docs/factory/improvement-routine.md`,
  `.beads/**`, any schedule, or another routine's journal.
- Caps: one PR, one issue, S size, branch prefix `routine-retro/`, body
  marker `<!-- retro-reflect-routine -->`.

## 8 Amending this playbook

The routine proposes; the human applies. A proposed amendment is a
unified diff under Proposals with one line of rationale, traced to a
correction event where one exists. Schedule changes — cron, prompt,
model — are proposed the same way and applied by the human.

## Trigger

**Not yet created.** A scheduled trigger is recurring paid spend, and
creating one awaits the owner's explicit approval. Nothing in this file
authorizes creating it, and no agent or routine creates it on the
strength of this file. When the owner approves, the trigger takes
ADR-0044's shape:

- **Name:** `factory-weekly-retro-reflect`.
- **Cadence:** weekly — proposed Monday 13:17 UTC (`17 13 * * 1`), clear
  of the daily routine's slot, so the week it reads is complete.
- **Model:** Sonnet.
- **Connectors:** none — no MCP connectors; `gh` and `git` only.
- **Prompt:** a thin pointer to this file, plus the four duplicated hard
  limits as defense in depth: one PR, never merge, no paid evals, no
  self-edit. A change to any of those updates prompt and playbook
  together.
- **Reporting:** the marker-found journal issue in §6.
- **Spend:** reported in the journal; excluded from the cost ledger
  exactly as ADR-0044 decided.

Once it exists, a human PR records its trigger id in this section.

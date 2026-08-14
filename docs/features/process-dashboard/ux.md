---
stage: ux-design
run: feature:process-dashboard
date: 2026-08-13
---

# UX: Process dashboard v1

One page, glance-first, read-only except backlog order. Data is
gathered fresh at open and sections fill progressively as each repo
answers. Every item links out to GitHub — the console observes; acting
happens where the gates live.

## Flows

### The morning glance (primary)

1. Operator opens the console; the header shows per-repo gather status
   and sections fill as repos answer.
2. Operator scans the needs-you strip: gate-queue items with ages and
   drift flags, most urgent first.
3. Operator clicks an item and lands on its GitHub PR / issue / file
   in a new tab, acting there (approve, merge, investigate).
4. Scrolling continues the glance: runs by repo, backlog, factory
   output, metrics.

### Prioritize the backlog

1. Operator scrolls to a repo's backlog list.
2. Drags seeds into the new order; the list shows an "unsaved order"
   dirty state.
3. Clicks Save order — the repo's `docs/backlog.md` lines are
   rewritten once, claim markers intact. Nothing writes before Save.

### Trace the factory's output

1. Operator scrolls to Factory output.
2. Reads work orders with lifecycle state, PR, and spend; clicks
   through to the PR on GitHub.

### Judge improvement

1. Operator scrolls to Metrics: headline totals, then per-repo rows.
2. Trends (cost/WO, gate latency) answer "are we improving" at a
   glance; anything deeper goes back to the ledger itself.

## Screens

### The console (single page)

```
┌────────────────────────────────────────────────────────────────┐
│ PROCESS DASHBOARD          gathered: skills ✓  eat-sheet …     │
│                            as of 2026-08-13 09:02              │
├────────────────────────────────────────────────────────────────┤
│ NEEDS YOU (3)                                                  │
│ ● merge gate   WO-0018 PR #260 — waiting 2d 4h        [skills] │
│ ● prd gate     WO-0021 mirror #61 — waiting 5h     [eat-sheet] │
│ ⚠ drift        #123 closed but WO-0018 row unchecked  [skills] │
├────────────────────────────────────────────────────────────────┤
│ RUNS                                                           │
│ ┌─ skills ──────────────────────┐ ┌─ eat-sheet ─────────────┐  │
│ │ process-dashboard ▸ ux-design │ │ menu-import ▸ verify    │  │
│ │ software-factory  ▸ implement │ └─────────────────────────┘  │
│ │ deepening-cli-…   ▸ operate   │                              │
│ └───────────────────────────────┘                              │
├────────────────────────────────────────────────────────────────┤
│ BACKLOG — one list per repo, ordering is priority              │
│ skills                                    [Save order] (dirty) │
│  ⣿ 1. omp skill:// references …                                │
│  ⣿ 2. next-maintenance-1 under-triggers …                      │
│  ⣿ 3. …                (claimed seeds shown dimmed, unmovable) │
├────────────────────────────────────────────────────────────────┤
│ FACTORY OUTPUT                                                 │
│ WO       title              size  state        PR      spend   │
│ WO-0017  gate-queue digest  S     merged       #245    $3.20   │
│ WO-0018  rejection mining   S     in-progress  #260    $1.10   │
├────────────────────────────────────────────────────────────────┤
│ METRICS                                                        │
│ month spend $84 / $300 caps   cost/WO $4.10 ↓   gate wait 26h ↓│
│   skills     $61 / $300   cost/WO $4.40   gate wait 30h        │
│   eat-sheet  $23 / $150   cost/WO $3.10   gate wait 18h        │
└────────────────────────────────────────────────────────────────┘
```

- Purpose: answer "what's going on and what needs me" in one scan;
  the only action taken *in* the console is reordering a backlog.

Per-section states:

**Header / gather (loading).** Fresh-on-open gather with per-repo
status ("skills ✓, eat-sheet …"); sections render as answers arrive.
An "as of" timestamp anchors the glance. A repo that fails to answer
shows its error in place (on its card / rows) — the page renders on;
an unreachable repo is never silently absent.

**Needs-you strip.** Gate-queue entries (which gate, what, waiting
how long, which repo) and drift flags (⚠, what disagrees with what),
each linking to the PR/issue/file involved. Empty: "Nothing waits on
you." — the good state, stated plainly.

**Runs (repo cards).** One card per repo: active runs with current
stage and next step, matching what the router would say. Empty card:
"No active runs." Unreachable repo: the card carries the error text.

**Backlog (per repo).** Seeds in file order with drag handles;
claimed seeds dimmed and unmovable; drag marks the list dirty
("unsaved order"); Save rewrites that repo's `docs/backlog.md` once.
Save failure keeps the dirty state and shows the error — the order
is never silently lost. Empty: "No docs/backlog.md in this repo."

**Factory output.** Work orders with size, lifecycle state, PR link,
and spend per order. Empty: "No factory stamped in this repo." (a
pipeline-only repo is normal, not an error).

**Metrics.** Headline totals (month spend vs summed caps, cost/WO
trend, gate-latency trend) then one row per repo. Empty: "No runs
recorded yet." A repo with a ledger problem shows the problem line,
not a silently smaller number.

## Conventions to match

- Canonical vocabulary (CONTEXT.md): runs, stages, seeds, work
  orders, gates — the UI never invents synonyms.
- Waiting ages in the gate digest's format (`2d 4h`, `<1h`); dates
  ISO (`YYYY-MM-DD`).
- Fail loud, render on: a failed source shows its error where its
  data would be — never a silently missing section (the repo's
  problem-string ethos, on screen).
- Everything that names a PR, issue, or file links to it on GitHub.

## Deliberately not designed

- Visual styling, theme, typography — Implement picks something
  plain; no brand exists to match.
- Mobile layout and animations.
- Control-plane affordances (approve/dispatch/merge buttons) and
  alerting — later versions per the PRD; nothing here forecloses
  them.
- In-console detail panes — click-through goes to GitHub in v1.
- First-run onboarding beyond a plain "no repos configured" message
  pointing at the config (whose shape is Architect's).

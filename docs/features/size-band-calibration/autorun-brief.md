# Autorun brief: size-band-calibration

Not an artifact. Written 2026-10-20 by the orchestrator under the `/goal`
"complete remaining gh issues". The Owner answered two questions in
session, taking the recommended option each time:

1. What to drive: "#987 Decompose loop 2/4 (Recommended)", the first of
   the six remaining real issues.
2. Unmetered owner sessions: "Exclude, report the count (Recommended)".
   Calibration reads only metered ledger rows that join to a breakdown
   row's `size:` band, and prints how many rows it excluded and why. No
   cost is ever estimated for an unmetered session.
3. Release: "Prepare-and-stop, open PR (Recommended)". Ship pushes the
   branch, opens one PR and stops. It does not merge.

The rest of this brief is the orchestrator's reading of issue #987 and of
the repo, and is marked that way. When a stage needs an answer this brief
doesn't hold, it follows the autorun rule: take the skill-supplied default
and log it, or else stop and surface the question.

## What and why (orchestrator's reading of #987)

Step 2 of 4 in the Decompose learning loop; step 1 is #986, merged as
#1040 (`decompose_signals.py`). Judged effort ranges are overconfident;
computing each size band's range from the empirical distribution of past
error (Balanced Relative Error percentiles) helps, and needs only sorting,
so it fits stdlib Python. Measured on 2026-10-16: 7 of 184 rows in
`docs/factory/costs.jsonl` record a cost, 145 are `owner-session:unmetered`,
2 join to a breakdown row's `size:` band (both S), and `origin/main`
holds 0 Conductor batch ledgers.

- **Meter first.** Make work-item cost land in the ledger with a joinable
  size band (Conductor batches are the expected source).
- **Then calibrate.** Once a band has enough items (the backlog's
  step-weight seed uses n >= 5), compute the band's BRE percentile
  interval from history and report band misses.
- **Guard against gaming.** Always report band misses next to cost and
  the re-plan rate (from `decompose_signals.py`), so size inflation shows
  up as cost.

## Acceptance (from the issue)

- The ledger rows a calibration reads carry a size band, and the join is
  tested.
- The calibration refuses to report a band below its minimum n, and says
  so.
- No calibration number is ever written by hand (eval honesty).

## Idea-stage inputs (orchestrator's reading)

- **Problem, from the sufferer's view.** The Owner sizes work items S/M/L
  without knowing how far off the bands run. Nobody can say what an M
  actually costs or how often one overruns.
- **Who has it, and how they cope today.** The Owner, and every Decompose
  run. They size by feel and accept the miss.
- **Why now.** #986 shipped the re-plan rate, the number that keeps this
  loop honest; steps 3 and 4 (#988, #989) calibrate against what this
  step measures.
- **Evidence.** Anecdote, labelled: the 2026-10-16 measurement above, and
  the cited estimation literature (Jorgensen, Teigen and Molokken, JSS
  2004).
- **Rough shape.** A stdlib-only root tool, like `decompose_signals.py`,
  that joins ledger rows to size bands and prints a per-band interval or
  a refusal. A hunch, not a design.
- **Success.** The tool prints a band's interval only when n meets the
  minimum, and otherwise says why not.
- **Ways this dies.** Too few metered rows ever exist; a hand-set number
  creeps in; sizes inflate.

## Scope, constraints and tracker

- In: the metering seam into the ledger, the join, the BRE calculation,
  the refusal below minimum n, the report next to cost and re-plan rate.
- Out: transcript-based metering of owner sessions, prompt changes to the
  Decompose skill (#988, #989), any hand-written calibration number.
- Stdlib only. Root-only tool unless Architect finds a payload caller
  (ADR-0110 precedent). Feature and fix branches never touch
  `.claude-plugin/plugin.json`'s version (ADR-0095).
- Issue #987 seeds the run and the PR closes it. No work order is
  mirrored; the PR body carries a `No work order:` line.
- No user-facing surface: CLI text output only (`ux:` not applicable).

## Operate

operate:
  minimum-signal: step 3 (#988) reads this tool's output, either using
    the numbers or failing on them

Operate does not run in this invocation.

stop-after: ship

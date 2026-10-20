---
stage: prd
run: feature:size-band-calibration
date: 2026-10-20
ux: not-applicable
ux-reason: "CLI text output only; no screens or flows."
assumptions:
  - "Interview answered from autorun-brief.md in this directory; no live interview held. The brief holds three Owner answers (drive #987; exclude unmetered owner sessions and report the count; prepare-and-stop release). Everything else traces to the brief's sections marked as the orchestrator's reading of issue #987, or to idea.md."
  - "Minimum n is 5 per band, taken from the brief (issue #987 and the backlog step-weight seed). Whether it is a constant or an option is left to Architect."
  - "No PRD id assigned: the prd skill and TEMPLATE.md assign none, and the brief rules out work-order mirroring."
  - "The success criterion that a refusal prints for a band with n below the minimum, and that a band with no joined rows prints differently from a band with too few, is derived from the issue's 'refuses and says so' acceptance line; it applies the fail-closed rule (no zero standing in for no data)."
  - "How the ledger walk is shared with conductor_calibrate, where the size band is joined (at ledger write time or later through breakdown rows), how Balanced Relative Error is defined and which percentiles form the interval are left to Architect as open questions (orchestrator instruction)."
---

# PRD: Calibrate S/M/L size bands from past error

## Problem statement

The Owner sizes work items S, M or L without knowing how far off the bands
run. Nobody can say what an M actually costs or how often one overruns, so a
size is a feel and a miss is accepted, not measured. Judged effort ranges
are known to run overconfident, and nothing here corrects for it. Steps 3
and 4 of the Decompose learning loop (#988 lessons file, #989 eval and
prompt optimization) calibrate against what this step measures, so neither
can show an effect until it exists.

The data is thin. Measured 2026-10-16 (cited from #987, not re-measured):
7 of 184 rows in `docs/factory/costs.jsonl` record a cost, 145 are
`owner-session:unmetered`, 2 join to a breakdown row's `size:` band (both
S), and `origin/main` holds 0 Conductor batch ledgers. Metering has to put
cost, with a joinable size band, into the ledger before calibration has
anything to read.

## Solution

Two parts, in order.

1. **Metering.** Work-item cost lands in the ledger in a form that can be
   joined to a breakdown row's `size:` band. Conductor batches are the
   expected source. The join is tested.
2. **Calibration.** One command at the repo root reads the ledger, joins
   metered rows to size bands, and prints per band either an interval of
   past error (Balanced Relative Error percentiles, from sorting alone) or a
   refusal that says why. Below the minimum of 5 metered items, a band
   prints the refusal and no number. Beside each band it prints the band's
   misses, its cost, and the re-plan rate from `decompose_signals.py`, so
   that inflating sizes shows up as cost. It prints how many ledger rows it
   excluded and why. Unmetered owner sessions are excluded and never given
   an estimated cost. Every printed number is computed from ledger rows;
   none is written by hand.

## Actors

- **Owner** — maintains this repo, sizes work items at Decompose, and runs
  the command to read it.
- **Calibration step (#988, #989)** — later steps of the Decompose learning
  loop that read this tool's output as their baseline.
- **Reviewer** — whoever examines the run's PR at the merge gate and judges
  whether a number can be trusted.

## User stories

1. As the Owner, I want work-item cost recorded in the ledger with a size
   band that can be joined, so that calibration has metered rows to read.
2. As the Owner, I want one command that prints each size band's interval
   of past error, so that I can see how far S, M and L actually run.
3. As the Owner, I want a band with too few items to print a refusal with
   the reason and no number, so that a thin sample never passes for a
   calibration.
4. As the Owner, I want band misses printed next to cost and the re-plan
   rate, so that inflating sizes to look accurate shows up as cost.
5. As the Owner, I want the count of excluded rows and the reason printed,
   so that I can see how much of the ledger the numbers cover and that
   owner-session work is invisible to them.
6. As a Calibration step, I want every figure computed from ledger rows by
   the tool, so that I compare against a baseline nobody edited.
7. As a Reviewer, I want the join and the refusal pinned by tests on exact
   output strings, so that I can trust the behavior without a live ledger.

## Success criteria

- [ ] A ledger row the calibration reads joins, by its work-order token, to
      a breakdown row's `size:` band at read time, and a test asserts that
      join. The ledger gains no field (Owner decision 4, autorun-brief.md).
- [ ] A band whose metered n is below 5 prints a refusal naming the band,
      its n, the minimum and the reason, and prints no interval. A test
      asserts the exact string at n = 4 and the interval at n = 5.
- [ ] A band with no joined rows prints a string different from the
      below-minimum refusal. A test asserts both.
- [ ] Rows from `owner-session:unmetered` and rows with no recorded cost
      are excluded; the output prints the excluded count and the reason for
      each kind. No cost is estimated for an excluded row. A test asserts
      this.
- [ ] Each reported band prints its misses beside its cost and the re-plan
      rate drawn from `decompose_signals.py`. Where the re-plan rate is
      unmeasurable it is named as such and never printed as zero.
- [ ] No calibration number is written by hand: every interval and count
      printed is computed from ledger rows, and a test with a fixture
      ledger asserts the figures from the rows.
- [ ] The tool is stdlib only and makes no network call.
- [ ] Tests through the public interface cover at least: a band at n = 4, a
      band at n = 5, a band with no rows, a ledger of only unmetered rows,
      and a mixed ledger. Each asserts exact output strings.
- [ ] `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
      `python3 gates.py` and `python3 gates.py --selftest` all pass.

## Out of scope

- Transcript-based metering of owner sessions. Owner-session work stays
  invisible to calibration.
- Any prompt or behavior change to the Decompose skill (#988, #989).
- Any hand-written calibration number, including a seeded default interval.
- Estimating a cost for an unmetered session.
- Mirroring this run's items to work orders; the PR body carries a
  `No work order:` line.
- A plugin version bump (ADR-0095).
- Re-weighting `DEFAULT_STEP_WEIGHTS` in `conductor_calibrate`; that seed
  in `docs/backlog.md` stays its own item.

## Open questions

- How is the ledger walk shared with `conductor_calibrate`, which already
  reads closed Conductor batch ledgers for per-step weights? Reuse, a shared
  seam, or a separate reader. For Architect.
- Where is the size band joined: written onto the ledger row at metering
  time, or joined later through breakdown rows whose shape has drifted? For
  Architect.
- What is the minimum n's home: a constant of 5 or an option? The brief
  fixes the value at 5. For Architect.
- How is Balanced Relative Error defined against a band's expectation, and
  which percentiles form the interval? For Architect.
- Is the tool root-only, or does a payload tool import it (ADR-0110
  precedent)? For Architect.
- Will metering ever produce volume (today 2 joinable rows, both S)? If
  not, the tool refuses everywhere indefinitely. Honest, but it gives
  steps 3 and 4 nothing. Operate reads this; the brief's minimum signal is
  that #988 uses the output or fails on it.

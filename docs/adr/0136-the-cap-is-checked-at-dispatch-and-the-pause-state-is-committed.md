# The cap is checked at dispatch, and the pause state is committed

- Status: accepted
- Date: 2026-11-24

The Owner decided both questions in session, taking the recommended
option of each decision issue: option 1 of #2312 and option 2 of #2261.
This amends ADR-0034's monthly circuit breaker.

## Context

ADR-0034 says the breaker "pauses dispatch repo-wide when spend crosses
the cap". It was built as one weekly job. cost-report.yml runs on
Mondays, judges only the month of its run date, and sets the
`FACTORY_PAUSED` repo variable. The assembler's only cost check was
`vars.FACTORY_PAUSED != 'true'`.

Two gaps followed.

- **#2312.** Spend that lands after a Monday report goes through for up
  to a week. A month's last partial week is never judged at all: the
  first Monday of the next month judges the new month, finds $0.00, and
  clears the pause. The audit reproduced a month ending 5.9 times over
  its cap with the breaker never tripping.
- **#2261.** The cloud routines cannot read `FACTORY_PAUSED`. `gh variable
  list` and the REST call answer 403 through the cloud proxy, and no MCP
  tool exposes repo variables. The routine protocols all said "propose-only
  when `FACTORY_PAUSED` is true", and the routines diverged: two treated
  the unreadable variable as not paused (fail open), one was permanently
  propose-only, and one flagged the inconsistency.

## Decision

**The assembler checks the cap at dispatch time (#2312, option 1).** The
dispatch job runs `make cost-check` (`cost_report.py check`) before it
resolves or claims an order. That is `cost_report.guard` for the current
UTC month, judged at the moment the money is about to be spent. A PAUSE
verdict fails the step, so nothing after it runs: the order stays on
`wo:ready-for-agent` and no agent job starts. An unreadable ledger or an
unresolvable cap fails closed the same way. `FACTORY_PAUSED` stays as the
kill switch on the job's `if:`.

**The routines read a committed pause state (#2261, option 2).** The
weekly cost-report run also commits its verdict as
`docs/factory/pause.json` (`paused`, `as_of`, `reason`), composed by
`cost_report.run_report` as its `state` output and written and pushed by
the workflow. The job's grant becomes `contents: write` for that commit.
Every routine protocol reads the file through `python3
tools/cost_report.py pause-state` instead of `gh variable list`. Exit 0
means not paused. Paused, a missing file, an unparseable file and a file
with no boolean `paused` each exit nonzero, and the routine takes its
propose-only or report-only mode and quotes the printed line in its
journal.

## Narrow readings

- #2312's option 1 adds the dispatch-time check and changes nothing else
  about the weekly report. The report still judges only its run date's
  month, and it still clears `FACTORY_PAUSED` on an under-cap verdict.
  Option 2 of that issue (re-running the report on ledger pushes, and
  judging the previous month on a month's first run) was not taken.
- #2261's option 2 offered "a pinned issue or a committed file". This
  takes the committed file: a cloud routine reads it from its own
  checkout with no API call at all.
- The pause state is the report's verdict, published whether or not
  `FACTORY_PAUSE_TOKEN` exists. It is written weekly and is not a
  second kill switch: a hand-set `FACTORY_PAUSED` reaches the assembler
  but not the routines, the same as before this decision. Pausing on
  purpose still means lowering `monthly_cap_usd` or disabling the
  workflow, as cost-report.yml's resume step already says.

## Consequences

- A cap breach now stops the next dispatch, not the next Monday's.
  The dispatch job's run goes red on a refusal, which is how the Owner
  sees it.
- A missing `docs/factory/pause.json` fails closed. Until cost-report.yml
  has run once after this lands (a `workflow_dispatch` or the next
  Monday), every routine runs propose-only or report-only. A freshly
  stamped repo behaves the same way until its first report.
- The file is only as fresh as the last weekly run. The routines'
  pause therefore still lags spend by up to a week. The assembler, which
  is where dispatched spend happens, no longer does.
- A stamped repo's Makefile carries `cost-check`, and doctor lists it in
  the full target set. Without it the dispatch job fails on every ready
  label.
- cost-report.yml now pushes to the default branch once a week. On a repo
  whose default branch is protected against the Actions bot, that step
  fails red and the routines fail closed.

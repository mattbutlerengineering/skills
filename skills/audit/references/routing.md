# Routing — one finding, one carrier

The carrier ladder `audit` and `automate` share. `audit` owns this file;
`automate` cites it as `../audit/references/routing.md` and says in its
own `SKILL.md` which of its recommendations take which rung. Below, a
"finding" is an audit finding or an automate recommendation.

One finding, one carrier. The ladder:

1. **A seed in `docs/backlog.md`** — the default for anything worth
   remembering and not worth a run today. One line, the protocol's
   grammar, origin `session:YYYY-MM-DD`:

       - <finding one-liner> (from: session:2026-08-08)

2. **A maintenance run** — hand it to `capture` when something is broken
   or degraded and is worth a run now. Capture interviews; neither
   `audit` nor `automate` writes `defect.md` on its behalf.
3. **A feature run** — hand it to `idea` when the finding is a direction
   worth building.
4. **Nothing.** A verdict, recorded in the report.

Before appending anything: **read `docs/backlog.md` first and drop
findings it already carries.** The dedupe happens before the write, not
after — an append is not undone by noticing, and a backlog that repeats
itself stops being read.

# The gate timeline read and the open queues join human_gates

- Status: accepted (Owner, 2026-10-13)
- Date: 2026-10-13

Amends ADR-0056's list of what deliberately did NOT move. It resolves
issue #740. The Owner decided in session on 2026-10-13: reproduce the
defect first, and if it reproduces, amend ADR-0056 and do the deepening.
It reproduced, and its minimal fix merged as #791 (#790).

## Context

ADR-0056 gave the three human gates one module, `human_gates`, and kept
it pure: no gh, no ledger, no filesystem, no clock. It left the timeline
read with each tool on purpose. `gate_digest._timelines`,
`rejection_mining._timelines` and `dashboard._timeline` were "gh reads
with an owner of their own at the cli seam", and ADR-0056 judged that
a network adapter inside a pure module would couple two seams to save
nothing. It also left each tool to build its own open queues, which
`gate_digest._queues` and `dashboard._queues` did by hand.

That bound rested on the copies having nothing left to share but their
label. The fixes since then say otherwise:

- **#491** made admission drop a label flip whose `created_at` is not a
  timestamp, and added `refused_timestamps` so a caller could report
  the drop. The report only happens if each caller calls the second
  function on the same raw timeline. It was wired into `gate_digest`
  and `dashboard` and missed in `rejection_mining`. There the cost is a
  lost rejection: a dropped `unlabeled` leaves its stay open, and
  `completed_stays` never yields it. #740 reasoned this from the code,
  and #790 reproduced it. #791 wired the call into the third copy.
  One fix had to be applied three times.
- **#665** taught `dashboard` to tell an unreadable age (the read
  failed) from an unknown one (the read held no arrival).
  `gate_digest._queues` had already been fixed for the same collapse
  (`docs/fixes/dashboard-timeline-unreadable-age/defect.md`). The same
  fix was made twice, in two queue builders.

The fetch, the page flattening, the admission and the refusal report
were identical in all three copies apart from the problem label and the
repo slug. The queue membership and the age arithmetic were identical in
both builders.

## Decision

Two functions join `human_gates`.

- **`read_timelines(numbers, run, label, slug="{owner}/{repo}")`**
  returns `({issue number: label events}, problems)`. In one call it
  fetches each timeline through the injected gh runner at cli's gh port
  (`cli.gh_read`), flattens the slurped pages, admits the label events,
  and reports refused timestamps as `<label>: timeline for #N refused`
  problems. An issue whose read failed is absent from the map, never
  present and empty. `refused_timestamps` is retired: the count is no
  longer a second call a caller can forget.
- **`open_queues(open_issues, mirror, events_by_issue, now)`** is pure.
  It returns `[(Gate, [Waiting(issue, waited, aged)])]` for all three
  gates, aged at the `now` the caller passes. `waiting_issues(open_issues,
  mirror)` names the issues it will age, for a caller that reads only
  those timelines (the dashboard).

`gate_digest`, `rejection_mining` and `dashboard` call these and keep
only what is theirs: the problem label, the slug, and how their rows
render. `dashboard._age_seconds` goes, because `open_queues` ages with
`waited_seconds` the way `gate_digest` already did.

The module is no longer pure in one function. `read_timelines` reads gh,
but only through the runner the caller injects. That is the same port
every gh-reading tool takes (ADR-0042), so tests still pass a
fake and never touch the network. Everything else in `human_gates` stays
events in, gate facts out. It still has no ledger, no filesystem and no
clock.

## Consequences

- A refused timestamp now reaches every timeline reader, and any
  future reader gets the report with the read.
- An open gate wait is computed in one place. The unread-versus-unknown
  distinction (#665) lives in `open_queues`, tested once against a
  literal `now`.
- The tests moved to the new interface. `tests/test_human_gates.py`
  covers the read (flattening, absent on failure, the refusal under
  every label, the dropped `unlabeled`) and the queues. The per-caller
  copies of those cases shrank to caller checks.
- `human_gates` now imports `cli`. Both are already mirrored into the
  payload (`factory_init.MIRRORS`), so a stamped repo needs no new
  file, and the manifest is regenerated in the same change.
- ADR-0056's other boundaries stand. The posts, the compositions, the
  ledger capture and `mirror_map` still live where it put them, and
  ADR-0074's stay end is untouched.

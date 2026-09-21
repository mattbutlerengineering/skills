---
stage: review
run: maintenance:a-malformed-timestamp-is-silently-dropped
date: 2026-09-20
assumptions: []
---

# Review: a malformed timeline timestamp is refused with no problem string

Self-authored; ADR-0036 clause 2 still wants a non-authoring reviewer.

## Findings

### 1. One walk, two questions — the alternative that duplicated `label_events`' loop was rejected

The first draft gave `refused_timestamps` its own copy of `label_events`'
loop (same `kind in ("labeled", "unlabeled")` check, same `.get("label")`
read), reasoning that `label_events`'s signature must not move for its
existing three production callers and ~15 test call sites. That would
have put two functions reading the same three payload keys
(`event`/`label`/`created_at`) in one module — precisely the shape
`one_owner.py` looks for. The shipped version factors both into one
private `_admit(timeline) -> (admitted, refused)`, and `label_events` /
`refused_timestamps` each return one half. `label_events`'s signature and
every existing caller are untouched; the payload-key read has one owner.
`one_owner.py` before and after this change reports the identical 7
findings (verification.md §5), confirming the refactor did not add one.

### 2. Why this stayed a caller-side fix, not a `label_events` problems channel

Issue #491 leaves the seam open ("label_events (or its caller)"). Giving
`label_events` a problems return was rejected for the same reason #326's
own architecture record rejected it for the admission decision itself:
`human_gates.py` has no problems-returning function today, and the
module's docstring calls it pure "by construction" (ADR-0056). Adding one
function that returns problems would break that uniform shape for a
count two of the module's four importers need and one does not. Routing
the count through a new pure function that both `label_events` and
`refused_timestamps` share, called by the two callers that already carry
a `problems` list past `label_events`, keeps the module's contract intact
and costs each caller three lines.

### 3. `dashboard.py` is in scope though it is not mirrored — deliberate, and named by the issue

`dashboard.py` ships root-only; nothing about detector E or
`factory_init.MIRRORS` requires touching it for this fix. It is included
because issue #491's own acceptance criterion names `dashboard:`
alongside `gd:`, and because the same silent drop is reachable through
`dashboard.gather` → `_queues` → `_timeline` by the identical mechanism.
Leaving it out would have closed the issue's letter for `gate_digest.py`
while leaving the operator console silently wrong the same way.

### 4. `rejection_mining.py` is the one caller left untouched — and that is checked, not assumed

The cited defect.md's own caller-exposure table names `rejection_mining`
as the one `label_events` importer with "no duration arithmetic," so a
refused timestamp there costs nothing observable through
`gate_rejections` today. `defect.md`'s Ruled out section restates this
rather than silently narrowing scope. Widening this run to a third
prefix (`rm:`) there would be unrequested scope against a caller the
evidence says is not actually losing anything yet.

### 5. The problem string names the issue and the count, not the individual events

`"gd: timeline for #123 refused 1 malformed timestamp(s)"` deliberately
does not name which event, which label, or what the bad `created_at`
value was. `gh_read`'s own problem strings for a failed or unparseable
fetch follow the same shape (issue number, no payload excerpt) — GitHub
timeline JSON is not something this repo's problem-string contract has
ever echoed verbatim into an issue body or a workflow log line, and
doing so here would be new, unrequested surface. An operator who needs
the raw event still has the `gh api .../timeline` call to run by hand;
the count is what tells them to look.

### 6. Bounded blast radius

Every code change is additive: a new private walk (`_admit`), a new
public function (`refused_timestamps`) with no existing caller, and one
new conditional `problems.append` in each of two functions that already
mutate a `problems` list. No existing return value, exception type, or
problem string changes shape for any well-formed input — pinned by every
pre-existing test in the three touched suites passing unmodified
(verification.md §4).

## Residual risk

A stamped repo whose `gate-digest.yml` run hits this path for the first
time will see the job go from green to red: `cli.report` returns 1
whenever `problems` is non-empty, so a nonzero refused count now fails
the workflow step exactly the way an already-failing per-issue timeline
fetch does today (`test_a_failing_timeline_still_posts_the_digest` pins
that this is pre-existing behavior, not new). That is the fix working as
intended — the whole point of issue #491 is that this case should stop
being invisible — but it is a real, visible change: a scheduled job that
was silently swallowing a malformed event will now flag it red once a
day for as long as the malformed event stays inside the fetched window,
the same "not a transient" shape the original defect.md's blast-radius
section already described for the crash #326 fixed. The digest still
posts either way (render-on, never abort); only the exit code moves.

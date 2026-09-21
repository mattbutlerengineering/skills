---
stage: review
run: maintenance:an-unresolvable-cap-plans-a-full-batch
date: 2026-08-27
assumptions: []
---

# Review: an unresolvable cap plans a full batch

Scope: `work_queue.py` (+11/-2), its payload mirror,
`factory/manifest.json` (regenerated), `tests/test_work_queue.py` (+52).

Written by the same agent that wrote the change, so ADR-0036 clause 2 is
unsatisfied.

## Correctness

**Checked, not a finding — `cap is None` is exactly the reported set.**
`factory_config.resolve_cap` returns `(None, [problem])` or
`(value, [])`; the new branch and the `cap_problems` list therefore fire
together, never apart. The refusal adds no case that `resolve_cap` did
not already report.

**Checked, not a finding — removing `cap is not None` from the loop is
safe and not merely tidy.** Past the refusal `cap` is a positive number
by `_positive_number`'s definition, so the guard could only ever be
true. Keeping it would advertise a case the function above no longer
admits.

**Checked, not a finding — the refusal is not reachable from a healthy
config.** Criterion 4 pins a resolvable cap planning under it and
refusing over it, and the two existing cap tests are untouched.

**Minor, deferred — a config broken in two ways reports one refusal.**
The cap refusal returns before the `wip_cap` check, so a config with
neither value names the cap. Both underlying `config:` problems are
still printed, and the reader is sent to the same file either way.
Reordering to collect both refusals would mean giving up the early
return that both siblings use; not worth the shape change for a
second sentence about the same file.

**Open, not fixed here — `factory_config.load` still lets a shape-invalid
config through.** It reports read and parse problems only, which is why
this defect existed: every value check happens later, in whichever
caller happens to ask. That is deliberate (detector F owns shape, via
`config_problems`), and it means each caller must fail closed for
itself. `work_queue` now does, alongside `cost_report` and
`budget_guard`. Recorded because the pattern will recur in the next
caller that resolves a config value.

## Design

The change is one early return in the shape the function already uses
eleven lines below it, and a comment naming the rule and its two
siblings rather than restating the mechanics. No new function, no new
constant, no interface change. The problem string follows the house
grammar — `wq:` prefix, the decision rather than the cause, the cause
left to the `config:` string beside it.

## Security

No new input surface; nothing new is read, executed or emitted. The
change removes a way for an incomplete config to produce a spend plan
with no ceiling, which is a spend-control improvement rather than a
security one, but it fails in the safe direction either way.

## Verdict

No critical findings. One minor deferred with its reason, one
pre-existing pattern recorded. The blocking condition on shipping is
ADR-0036 clause 2.

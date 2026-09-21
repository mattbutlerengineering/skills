---
stage: review
run: maintenance:an-infinite-cap-is-no-cap
date: 2026-08-27
assumptions: []
---

# Review: an infinite cap is no cap

Scope: `factory_config.py` (+8/-2), its payload mirror,
`factory/manifest.json` (regenerated), `tests/test_factory_config.py`
(+38).

Written by the same agent that wrote the change, so ADR-0036 clause 2
is unsatisfied.

## Correctness

**Checked, not a finding — the fix is at the predicate, not the
comparison.** Guarding `cost_report.decide` would have closed the cap
side and left `resolve_budget` handing an infinite ceiling to the
dispatch path. Four call sites share `_positive_number`, so one clause
closes all of them, and the value grammar keeps one owner.

**Checked, not a finding — `NaN` needed no clause.** `nan > 0` is
already false, so NaN was refused before this change and still is. The
new docstring says so explicitly, because the next reader will otherwise
wonder why only infinity is named.

**Minor, deferred — `Infinity` in JSON is a Python extension.** Strict
JSON has no infinity literal, so a config carrying one is already
non-portable, and a stricter reader would reject it at parse time with
`parse_constant`. Not done here: that changes how the file is READ, for
every field at once, and this defect is about what an amount may be.
Worth its own decision if the repo ever wants `factory.json` to be
portable JSON.

**Checked, not a finding — no behaviour change for real configs.**
Criterion 4 pins a finite config resolving identically and the breaker
still tripping at 150 against 100.

## Design

The change is one clause inside the existing predicate and adds
`import math`, matching how `cost_report` already reaches for
`math.isfinite` on the spend side. The docstring now carries the reason
rather than only the rule, so the constraint is not mistaken for
defensive padding later.

## Security

No new input surface. The change only narrows what the config may say;
nothing new is read, executed or emitted. It removes a way to silently
disable a spend control, which is a small security improvement in
itself.

## Verdict

No critical findings. One minor deferred with its reason. The blocking
condition on shipping is ADR-0036 clause 2.

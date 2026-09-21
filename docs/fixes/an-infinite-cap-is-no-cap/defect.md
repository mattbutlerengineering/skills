---
stage: capture
run: maintenance:an-infinite-cap-is-no-cap
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance is recorded at the head of
  autorun-brief.md"]
---

# Defect: an infinite cap is no cap

## Defect

`factory_config._positive_number` is the single statement of what a
valid dollar amount is, shared by all four value checks:

```python
# factory_config.py:93
def _positive_number(value):
    """True for a positive int/float that is not a bool — True is an int
    in Python, and a bool where a dollar amount belongs is a typo."""
    return (not isinstance(value, bool)
            and isinstance(value, (int, float)) and value > 0)
```

`float("inf") > 0` is true, so an infinite amount is admitted. Python's
`json.loads` accepts a bare `Infinity` literal, so this reaches the
predicate straight from a config file.

## Why it matters

An infinite cap cannot be crossed. `cost_report.decide` compares
`total_cost >= cap`, and `anything >= inf` is false, so the circuit
breaker returns CONTINUE at every spend level.

The module is explicit that this is the failure it must not have:

> a NaN, infinite, or negative spend would slip past the comparison and
> silently CONTINUE (fail open), so it PAUSEs with its own reason
> instead — failing closed

That guard is applied to the spend and not to the cap, though the
comparison has two sides and either one being infinite defeats it.

## Reproduction

Every check in the repo calls this config valid:

```
$ python3 -c "
import json, factory_config, cost_report
cfg = json.loads('{\"monthly_cap_usd\": Infinity, \"budgets_usd\": {\"S\": 1, \"M\": 2, \"L\": Infinity}, \"routing\": {\"mechanical\": \"m\", \"implementation\": \"i\", \"architecture_review\": \"a\"}, \"wip_cap\": 2}')
print('resolve_cap    ', factory_config.resolve_cap(cfg))
print('resolve_budget ', factory_config.resolve_budget('L', cfg))
print('config_problems', factory_config.config_problems(cfg))
print('decide(1e9,inf)', cost_report.decide(1e9, float('inf'))[0])
"
resolve_cap     (inf, [])
resolve_budget  (inf, [])
config_problems []
decide(1e9,inf) CONTINUE
```

A billion dollars of recorded spend continues, and `config_problems` is
what detector F reports, so CI calls the config clean too.

`NaN` is already rejected — `nan > 0` is false — which is why this gap
is narrow and easy to miss: the neighbouring nonsense value fails
closed by accident, and the infinite one does not.

## Breakdown

- [x] `_positive_number` requires a finite value. Acceptance: a test
      asserts `inf` is refused by all four call sites — `resolve_cap`,
      `resolve_budget`, and both `config_problems` checks — and that
      finite positives are unaffected.
- [x] The circuit breaker cannot be disabled by config. Acceptance: a
      test asserts an `Infinity` cap yields a problem rather than a
      resolvable cap.
- [x] Full battery green, payload mirror and manifest regenerated.

## Notes

2026-08-27 — the fix is one clause in `_positive_number` rather than a
check in `cost_report.decide`. Four call sites share that predicate, so
the cap, the per-size budgets and detector F's report are all corrected
by it; a guard added at the comparison would have fixed the cap alone
and left an infinite budget resolvable. No clause was needed for `NaN`:
`nan > 0` is already false.

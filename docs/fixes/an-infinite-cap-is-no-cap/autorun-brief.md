# Autorun brief — an infinite cap is no cap

## Provenance

No user-supplied brief exists for this run. It was authored from this
session's own investigation under a standing autorun instruction. The
candidate came from testing a module's stated convention against its
code: `cost_report` claims it "fails CLOSED", and `cost_report.decide`
validates its spend argument against exactly this failure — but nothing
validates the cap it is compared against.

## What and why

`factory_config._positive_number` is the one home for what a valid
dollar amount is. It excludes bools deliberately ("a bool where a dollar
amount belongs is a typo") but admits `float("inf")`, because `inf > 0`
is true.

`json.loads` accepts a bare `Infinity` literal, so a `factory.json`
carrying `"monthly_cap_usd": Infinity` parses, resolves, and passes the
whole value grammar with zero problems — `resolve_cap`,
`resolve_budget` and `config_problems`, which is what detector F
reports. `cost_report.decide` then compares `total >= inf`, which is
false for every finite spend, so the verdict is CONTINUE at any amount.

ADR-0034's monthly circuit breaker is thereby disabled silently and
permanently by a config every check in the repo calls valid.

`decide` already rejects a non-finite SPEND for precisely this reason,
in its own words: it "would slip past the comparison and silently
CONTINUE (fail open)". The same sentence describes the cap side, which
is unguarded.

## Scale and re-entry

Maintenance run, slug `an-infinite-cap-is-no-cap`. Re-entry is
`implement`: the rule already exists and already has an owner; it is
one clause short.

## Scope

In: `_positive_number` requires a finite value, which fixes the cap, the
per-size budgets, and detector F's report together because all four call
sites share it.

Out: `cost_report.decide`'s own spend validation, which is already
correct. Out: any change to `gates.py` (PR #320) — detector F reports
`config_problems`, so it is fixed from here without being touched.

## Constraints

Stdlib only. `factory_config.py` is mirrored, so `update-manifest` must
run.

## Release authorization

None. Ship prepares and stops.

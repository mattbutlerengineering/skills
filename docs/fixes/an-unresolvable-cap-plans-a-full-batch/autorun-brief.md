# Autorun brief — an unresolvable cap plans a full batch

## Provenance

No user-supplied brief exists for this run. It was authored from this
session's own investigation under a standing autorun instruction. The
candidate came from testing a module's stated convention against its
code: `work_queue.priced` states ADR-0034's fail-closed rule in its own
docstring and applies it to an unpriceable row — and `plan_batch`, six
lines further down, fails open on the other half of the same config.

## What and why

`work_queue.plan_batch` prices a batch against the monthly cap:

```python
cap, cap_problems = factory_config.resolve_cap(config)
problems += cap_problems
...
elif cap is not None and spent_usd + projected + row["budget"] > cap:
```

`resolve_cap` answers `(None, [problem])` when `factory.json` names no
usable `monthly_cap_usd`. `cap is None` then makes the cap comparison
disappear, and every eligible row goes into the batch — however much the
month has already spent. The problem string is reported, but so is a
runnable plan.

Two functions in the same file already refuse in exactly this situation.
`priced` drops a row whose size the budget table does not cover, and
says why: "ADR-0034's fail-closed rule, applied before the money is
spent instead of after". `plan_batch` itself returns an empty batch for a
`wip_cap` it cannot read — "refusing to guess a batch size". An
unresolvable cap is the same kind of fact: not an absent limit, an
unknown one.

The module docstring makes the promise the code does not keep: "the
batch is priced from each row's `size:` band against month-to-date
ledger spend and monthly_cap_usd (ADR-0034), so an over-cap batch is
refused BEFORE any agent is paid for."

## Scale and re-entry

Maintenance run, slug `an-unresolvable-cap-plans-a-full-batch`.
Re-entry is `implement`: the rule exists and has two correct
applications in the same file; a third path skips it.

## Scope

In: `plan_batch` refuses to plan when no cap resolves, in the shape its
`wip_cap` sibling already uses.

Out: `resolve_cap` itself, which correctly reports and returns None.
Out: `cost_report.guard` and `budget_guard.guard`, which already fail
closed on the same input. Out: detector F, which reports the config
problem independently and is unaffected.

## Constraints

Stdlib only. `work_queue.py` is mirrored, so `update-manifest` must run.

## Release authorization

None. Ship prepares and stops.

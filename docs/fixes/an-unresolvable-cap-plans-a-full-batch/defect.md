---
stage: capture
run: maintenance:an-unresolvable-cap-plans-a-full-batch
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance is recorded at the head of
  autorun-brief.md"]
---

# Defect: an unresolvable cap plans a full batch

## Defect

`work_queue.plan_batch` guards the cap comparison on the cap existing:

```python
# work_queue.py:145
    cap, cap_problems = factory_config.resolve_cap(config)
    problems += cap_problems
    ...
        elif cap is not None and spent_usd + projected + row["budget"] > cap:
```

`factory_config.resolve_cap` answers `(None, [problem])` whenever
`factory.json` names no usable `monthly_cap_usd`. So `cap is None` is
precisely the case where the ceiling is unknown — and it is the case in
which the whole comparison is skipped.

## Why it matters

The module docstring states the opposite promise:

> the batch is priced from each row's `size:` band against month-to-date
> ledger spend and monthly_cap_usd (ADR-0034), so an over-cap batch is
> refused BEFORE any agent is paid for

And two other paths in the same file already refuse on the same class of
input. `priced`, six lines above:

> A row whose size the budget table does not cover is dropped with its
> `config:` problem rather than run at an unknown price — ADR-0034's
> fail-closed rule, applied before the money is spent instead of after.

and `plan_batch` itself, on the very next config value:

```python
    wip = config.get("wip_cap")
    if not isinstance(wip, int) or isinstance(wip, bool) or wip < 1:
        return [], sorted(deferred), problems + [
            "wq: factory.json wip_cap must be a positive integer —"
            " refusing to guess a batch size"]
```

One config value it cannot read refuses a batch; the next one plans a
full one. The sibling tools agree with the first: `cost_report.guard`
PAUSEs on an unresolvable cap ("failing closed") and
`budget_guard.guard` HARD-STOPs on an unresolvable budget for the same
stated reason.

## Reproduction

A `factory.json` that parses, and names budgets, routing and a wip_cap,
but no monthly cap — with nearly a million dollars already spent this
month:

```
$ python3 -c "
import work_queue, factory_config
config = {'budgets_usd': {'S': 10, 'M': 20, 'L': 40}, 'wip_cap': 3,
          'routing': {'mechanical': 'm', 'implementation': 'i',
                      'architecture_review': 'a'}}
print('resolve_cap:', factory_config.resolve_cap(config))
found = {f'WO-000{i}': {'wo': f'WO-000{i}', 'done': False, 'size': 'L',
                        'issue': 100+i, 'blockers': [],
                        'where': f'b.md:{i}'} for i in (1, 2, 3)}
batch, deferred, problems = work_queue.plan_batch(
    found, {101, 102, 103}, config, spent_usd=999999.0)
print('batch   :', [r['wo'] for r in batch])
print('deferred:', deferred)
print('problems:', problems)
"
resolve_cap: (None, ['config: factory.json names no positive monthly_cap_usd'])
batch   : ['WO-0001', 'WO-0002', 'WO-0003']
deferred: []
problems: ['config: factory.json names no positive monthly_cap_usd']
```

Three work orders planned, $120 projected, nothing deferred. The
`config:` problem is reported and `main` exits nonzero — but a batch is
what this tool produces, and it produced one.

`factory_config.load` does not catch this on the way in: it reports read
and parse problems only. A config that is valid JSON and merely says
nothing about the cap reaches `plan_batch` with no problems at all.

## Why the tests did not catch it

`tests/test_work_queue.py` covers both siblings and neither the hole:

- `test_an_unpriceable_size_is_dropped_and_reported`, commented
  "fail closed: never run a work order at an unknown price"
- `test_a_missing_wip_cap_refuses_to_guess`
- `test_the_monthly_cap_refuses_a_batch_before_it_is_paid_for` — which
  exercises a cap that resolves and is crossed

There is no test for a cap that does not resolve.

## Breakdown

- [x] `plan_batch` refuses to plan a batch it cannot price against a
      cap. Acceptance: a test asserts an empty batch and a `wq:` refusal
      problem when `resolve_cap` yields None, in the shape the `wip_cap`
      refusal already uses.
- [x] The refusal does not blind the report. Acceptance: a test asserts
      the near-miss deferrals `eligible` computed are still returned, as
      the `wip_cap` refusal already returns them.
- [x] The refusal reaches the consumer. Acceptance: a CLI-level test
      asserts `plan` over a cap-less config prints no planned work order
      and exits nonzero.
- [x] Full battery green, payload mirror and manifest regenerated.

## Notes

2026-08-27 — the refusal is placed where `resolve_cap` is called rather
than at the comparison, so `cap is not None` in the loop became dead and
was removed. Leaving it would have said the loop still handles a missing
cap when the function above it no longer lets one through, which is the
kind of stale guard that makes the next reader re-derive the invariant.

2026-08-27 — the second breakdown item's test
(`test_the_refusal_still_reports_the_near_misses`) is green before the
fix as well as after. It is kept because it pins what the refusal must
not break — the `wip_cap` refusal returns `eligible`'s deferrals and this
one must too — but `verification.md` records that it is not evidence of
the defect, so the run does not claim four regression tests where it has
three.

2026-08-27 — the refusal comes before the `wip_cap` check, so a config
that is broken in both ways reports the cap refusal and not the wip one.
That matches the existing reading order (the cap is resolved first) and
either single message is enough to send a reader to the config; both
underlying `config:` problems are reported regardless.

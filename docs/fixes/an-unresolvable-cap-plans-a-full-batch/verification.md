---
stage: verify
run: maintenance:an-unresolvable-cap-plans-a-full-batch
date: 2026-08-27
assumptions: []
---

# Verification: an unresolvable cap plans a full batch

Baseline on `origin/main` (622e7c0) is 1344 tests. This run adds four.

## 1 — the reported reproduction no longer reproduces

The exact payload from `defect.md` — no `monthly_cap_usd`, $999,999
already spent, three eligible L-band rows:

```
$ python3 -c "
import work_queue
config = {'budgets_usd': {'S': 10, 'M': 20, 'L': 40}, 'wip_cap': 3,
          'routing': {'mechanical': 'm', 'implementation': 'i',
                      'architecture_review': 'a'}}
found = {f'WO-000{i}': {'wo': f'WO-000{i}', 'done': False, 'size': 'L',
                        'issue': 100+i, 'blockers': [],
                        'where': f'b.md:{i}'} for i in (1, 2, 3)}
batch, deferred, problems = work_queue.plan_batch(
    found, {101, 102, 103}, config, spent_usd=999999.0)
print('batch   :', [r['wo'] for r in batch])
print('problems:', problems)
"
batch   : []
problems: ['config: factory.json names no positive monthly_cap_usd',
           'wq: no monthly cap could be resolved — refusing to plan a batch it cannot price']
```

Before the fix this printed all three work orders and the config problem
alone. PASS.

## 2 — the regression tests fail on the unfixed code

Three of the four new tests are RED against `origin/main`'s
`work_queue.py`:

```
FAIL: test_a_config_naming_no_cap_plans_nothing (TestMain)
FAIL: test_an_unresolvable_cap_is_not_an_unlimited_one (TestPlanBatch)
FAIL: test_an_unresolvable_cap_refuses_to_plan (TestPlanBatch)
```

The fourth, `test_the_refusal_still_reports_the_near_misses`, passes
before and after by design — it is not evidence of the defect; it pins
the behaviour the refusal must not break, the way the `wip_cap` refusal
also hands back `eligible`'s deferrals. Recorded here rather than
counted as a regression test. PASS.

## 3 — the refusal reaches the surface a consumer reads

The work-queue skill runs what `plan` prints, so the CLI leg is the one
that matters. Over a fixture tree whose `factory.json` names no cap and
whose breakdown carries a ready, priced, mirrored row:

```
$ python3 -m unittest tests.test_work_queue.TestMain.test_a_config_naming_no_cap_plans_nothing
Ran 1 test in 0.002s

OK
```

The test asserts exit code 1, that no `WO-0001  size:S` plan line is
printed, that the refusal sentence appears, and that the summary reads
`wq: 2 problem(s)`. PASS.

## 4 — a resolvable cap is unaffected, in both directions

The guard must not have turned into a refusal of everything:

```
$ python3 -c "
import work_queue
config = {'budgets_usd': {'S': 10, 'M': 20, 'L': 40}, 'wip_cap': 3,
          'routing': {}, 'monthly_cap_usd': 300}
found = {'WO-0001': {'wo': 'WO-0001', 'done': False, 'size': 'L',
                     'issue': 1, 'blockers': [], 'where': 'b.md:1'}}
print('under cap:', [r['wo'] for r in work_queue.plan_batch(found, {1}, config, 0.0)[0]])
print('over cap :', [r['wo'] for r in work_queue.plan_batch(found, {1}, config, 290.0)[0]])
"
under cap: ['WO-0001']
over cap : []
```

PASS — the existing cap tests
(`test_the_monthly_cap_refuses_a_batch_before_it_is_paid_for`,
`test_the_cap_counts_what_this_batch_already_planned`) still pass
unchanged.

## 5 — full battery

```
$ python3 -m unittest discover tests
Ran 1348 tests in 16.456s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
```

1348 = 1344 + 4. PASS.

## Not verified

- **Nothing runs against live GitHub.** The CLI test injects a recording
  runner; no `gh` call was made.
- **The real `.github/factory.json` is not exercised as a failing
  case** — it names a cap, so the refusal path is reached only through
  fixtures and injected config. That is the same seam every other
  `plan_batch` test uses.
- **`one_owner.py` is unchanged at 9 findings**, so this run neither
  added nor removed a second owner.

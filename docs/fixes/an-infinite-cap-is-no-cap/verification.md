---
stage: verify
run: maintenance:an-infinite-cap-is-no-cap
date: 2026-08-27
assumptions: []
---

# Verification: an infinite cap is no cap

## 1. An infinite cap no longer resolves — PASS

```
$ python3 -c "... factory_config.resolve_cap(cfg)"
(None, ['config: factory.json names no positive monthly_cap_usd'])
```

## 2. An infinite per-size budget no longer resolves — PASS

The same predicate backs the budget lookup, so the dispatch path cannot
price a work order against an infinite ceiling either.

```
$ python3 -c "... factory_config.resolve_budget('L', cfg)"
(None, ["config: factory.json names no positive budget for size 'L'"])
```

## 3. Detector F reports it — PASS

`config_problems` is what detector F prefixes and prints, so a config
that disables the breaker now fails CI instead of passing it.

```
$ python3 -c "... factory_config.config_problems(cfg)"
['budgets_usd.L must be a positive number', 'monthly_cap_usd must be a positive number']
```

## 4. Finite configs are unaffected, and the breaker still trips — PASS

The change narrows only the non-finite case; a real config resolves
exactly as before and a real overspend still pauses.

```
$ python3 -c "... resolve_cap(ok), config_problems(ok), decide(150, 100)"
finite config   (100, []) []
decide(150,100) PAUSE
```

## 5. Full battery green, payload mirrored — PASS

1344 tests on the merge base, 1348 here: the four added above.
`factory_config.py` is mirrored, so `update-manifest` ran and the
payload copy carries the fix.

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
$ python3 -m unittest discover tests
Ran 1348 tests in 16.217s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

## Not verified

No end-to-end cost-report run: `cost_report report` writes to
`$GITHUB_OUTPUT` and this run exercised `decide` and the resolvers
directly rather than through the CLI. The shipped `.github/factory.json`
was not inspected for an infinite amount — if one were there, the battery
above would have failed, and it did not.

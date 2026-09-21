---
stage: verify
run: maintenance:the-front-door-miscounts-its-own-tools
date: 2026-08-28
assumptions: []
---

# Verification — the front door miscounts its own tools

## 1. The router states no count its table owns

```
$ python3 -m unittest \
    tests.test_factory_cli.TestTheRouterCountsNothingByHand -v
test_the_number_is_still_one_help_away ... ok
test_the_pin_catches_a_digit_form_too ... ok
test_the_pin_catches_the_sentence_that_drifted ... ok
test_the_pin_leaves_ordinary_prose_alone ... ok
test_the_router_states_no_count_its_table_owns ... ok
----------------------------------------------------------------------
Ran 5 tests in 0.107s

OK
```

Before the fix, one of these five failed:

```
FAIL: test_the_router_states_no_count_its_table_owns
AssertionError: Lists differ: ['Fourteen root modules'] != []
```

**Result:** PASS

## 2. The pin is not vacuous

`test_the_pin_catches_the_sentence_that_drifted` holds the sentence as it
stood, verbatim, and asserts the checker finds it — so criterion 1 cannot
pass by looking for something that never matches.
`test_the_pin_catches_a_digit_form_too` covers the digit spelling, and
`test_the_pin_leaves_ordinary_prose_alone` asserts real sentences from the
file do not fire, so the cheapest way to satisfy the pin is not to stop
explaining the router. What the checker returns for each:

```
drifted sentence -> ['Fourteen root modules']
digit form       -> ['17 verbs']
ordinary prose   -> []
```

and the three tests, run on their own:

```
$ python3 -m unittest \
    tests.test_factory_cli.TestTheRouterCountsNothingByHand.test_the_pin_catches_the_sentence_that_drifted \
    tests.test_factory_cli.TestTheRouterCountsNothingByHand.test_the_pin_catches_a_digit_form_too \
    tests.test_factory_cli.TestTheRouterCountsNothingByHand.test_the_pin_leaves_ordinary_prose_alone
----------------------------------------------------------------------
Ran 3 tests in 0.000s

OK
```

**Result:** PASS

## 3. Removing the count costs the reader nothing

`test_the_number_is_still_one_help_away` runs `factory.main(["help"])`
and asserts the index prints one line per verb:

```
$ python3 factory.py help | grep -c '^  [a-z]'
17
$ python3 -c "import factory; print(len(factory.VERBS))"
17
```

**Result:** PASS

## 4. Nothing about the table changed

The existing derivation tests were not modified and still pass:

```
$ python3 -m unittest tests.test_factory_cli -v 2>&1 | tail -4
Ran 16 tests in 0.117s

OK
```

Eleven of those sixteen predate this run, including
`test_every_cli_bearing_root_module_has_exactly_one_verb`, which is what
makes seventeen the authoritative number rather than an observation.

**Result:** PASS

## 5. The three other hand-typed counts were checked, not assumed

```
$ python3 -c "import human_gates, factory_roles; \
    print(len(human_gates.GATES), len(factory_roles.ROLES))"
3 9
$ grep -rn "gh_read(" --include='*.py' . | grep -v '/tests/' \
    | grep -v 'factory/templates' | grep -v 'def gh_read' | wc -l
      14
```

`gate_digest.py` and `human_gates.py` say "three gates" — 3.
`factory_roles.py` says each role is encoded in "two files" — its two
path helpers. `cli.py` and `tests/test_cli.py` say `gh_read` replaced
"fourteen call sites" — 14 in production code. All accurate; none
touched.

**Result:** PASS

## 6. The repo battery

```
=== unittest ===
Ran 1349 tests in 21.905s

OK
=== lint ===
lint: 0 problem(s) across 24 skills
=== gates ===
gates: 0 problem(s)
=== selftest ===
selftest: ok
=== one_owner ===
one-owner: 9 problem(s)
```

1349 is 1344 on `origin/main` plus the 5 this run adds. `one_owner` is
unchanged at 9.

**Result:** PASS

## Not verified

```
Not run: a sweep of hand-typed counts outside the root Python modules.
```

**Result:** NOT RUN — the sweep behind criterion 5 covered root `*.py`
docstrings and comments. Counts in `docs/**`, `skills/**` and
`factory/templates/**` were not enumerated, so this run makes no claim
that the repo has no other stale count; it claims the root modules have
none besides the one fixed here.

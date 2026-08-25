---
stage: verify
run: maintenance:marker-diagnostics-that-lie
date: 2026-08-25
assumptions: ["Every block below is pasted from a command actually run on this branch at 432c41e, not written from expectation. Where a command's output disagreed with what the breakdown predicted, the artifact records the output and the deviation is logged in breakdown.md's Notes — never the other way round."]
---

# Verification: two marker diagnostics that state what is actually true

Criteria are `autorun-brief.md`'s six success criteria, plus the
acceptance criteria in `breakdown.md` not already covered by one of them.

## What changed

```
 one_owner.py            |  98 +++++++++++++++++++++++++++++-----
 tests/test_one_owner.py | 138 +++++++++++++++++++++++++++++++++++++++++++++---
 2 files changed, 216 insertions(+), 20 deletions(-)
```

Eleven test cases added, none deleted:

```
$ git diff ef8f1e2..HEAD -- tests/test_one_owner.py | grep -c "^+    def test_"
11
$ git diff ef8f1e2..HEAD -- tests/test_one_owner.py | grep -c "^-    def test_"
0
```

## C1 — a marker above a decorated definition attaches. **PASS**

`defect.md`'s reproduction, re-run against this branch. The same probe
produced the "before" half quoted in `defect.md`; its `_rent` call site
changed because this run added a parameter, so only diagnostic 1's half is
literally the same code.

```
--- diagnostic 1: a marker above a DECORATED definition
  undecorated  markers=1 problems=[]
  decorated    markers=1 problems=[]
```

Before, the decorated line read
`markers=0 problems=['one-owner: a.py:1 is a one-owner marker above no definition']`.

At the suite's boundary:

```
test_a_marker_above_a_decorated_definition_attaches_to_it (tests.test_one_owner.TestMarkers.test_a_marker_above_a_decorated_definition_attaches_to_it)
ADR-0061 asks for the carve-out at the definition it excuses. ... ok
```

## C2 — the between-decorator placement still attaches. **PASS**

The placement that worked before `attach` existed, and the reason the join
walks up from two lines rather than one:

```
test_a_marker_between_the_decorator_and_the_def_still_attaches (tests.test_one_owner.TestMarkers.test_a_marker_between_the_decorator_and_the_def_still_attaches)
The placement that works today, and the only one that worked ... ok
test_a_blank_line_still_ends_the_block_above_a_decorator (tests.test_one_owner.TestMarkers.test_a_blank_line_still_ends_the_block_above_a_decorator)
Locality survives the widening: the block above a decorated ... ok
```

The blank-line case is here deliberately: widening *where* a marker may sit
must not weaken the locality rule that makes the marker mean anything.

## C3 — a counterpart that exists but states no fact says so. **PASS**

```
--- diagnostic 2: a counterpart that EXISTS but states no fact
  fact sites: [('a.py', 'f')]
  other.py binds: ['other.g']
  _rent says: ['one-owner: a.py:1 names other.g, which is defined but states no fact this pass reads — name the definition that duplicates, or remove the marker']
```

Before, the same probe printed
`['one-owner: a.py:1 names other.g, which is not defined in this repo']`.

Through `check`, on a fixture tree, for both shapes that can be defined
without stating a fact — a function below the two-key floor, and a class,
which is never a fact site at all:

```
test_a_counterpart_that_exists_but_states_no_fact_says_so (tests.test_one_owner.TestCoverage.test_a_counterpart_that_exists_but_states_no_fact_says_so)
A FOLD does this to one side of a duplicate: the counterpart ... ok
test_a_counterpart_that_is_a_class_states_no_fact_either (tests.test_one_owner.TestCoverage.test_a_counterpart_that_is_a_class_states_no_fact_either)
No class is ever a fact site, which is exactly why the name ... ok
```

## C4 — a counterpart that exists nowhere is unchanged. **PASS**

The pre-existing case, untouched by this run and still asserting the old
string:

```
test_a_marker_pays_rent_or_it_is_a_finding (tests.test_one_owner.TestCoverage.test_a_marker_pays_rent_or_it_is_a_finding)
Over-coverage. A carve-out whose counterpart was deleted, ... ok
test_a_fully_covered_group_is_silent (tests.test_one_owner.TestCoverage.test_a_fully_covered_group_is_silent) ... ok
test_a_counterpart_this_repo_does_not_define (tests.test_one_owner.TestCoverage.test_a_counterpart_this_repo_does_not_define) ... ok
```

All three branches of the new three-way split are pinned: exists-nowhere
(unchanged string), exists-but-states-nothing (new string), and is-a-fact-
site (falls through to the group check, whose two strings are unchanged).

## C5 — the standing findings are byte-identical. **PASS**

Not eyeballed. `python3 one_owner.py` was captured on this branch and again
with `one_owner.py` and its suite checked out at ef8f1e2, and the two files
diffed:

```
after exit=1
before exit=1
=== diff before/after ===
IDENTICAL (       9 lines)
```

The nine lines are the eight standing findings and the summary, exactly as
quoted in `defect.md`'s baseline section.

## C6 — the battery is green. **PASS**

```
$ python3 -m unittest discover tests 2>&1 | tail -3
Ran 1366 tests in 15.354s

OK
$ python3 lint.py | tail -1
lint: 0 problem(s) across 24 skills
$ python3 gates.py | tail -1
gates: 0 problem(s)
$ python3 gates.py --selftest | tail -1
selftest: ok
```

The count is measured at both ends, not inferred from the diff. At ef8f1e2,
in a detached worktree:

```
Ran 1355 tests in 16.100s

OK
```

1355 → 1366 is the eleven new cases, none removed.

`gates.py --selftest` prints `selftest: ok`, not the `gates: 0 problem(s)`
the breakdown's acceptance criterion predicted; the criterion was written
from CLAUDE.md's phrasing without running the second command. Logged as a
deviation rather than quietly reworded.

## I1 — the pinned shape and both lines. **PASS**

```
test_the_three_shapes_carry_the_declared_fields (tests.test_one_owner.TestDataModel.test_the_three_shapes_carry_the_declared_fields)
`attach` was added by the marker-diagnostics-that-lie run, whose ... ok
test_a_decorated_definition_carries_both_of_its_lines (tests.test_one_owner.TestSameKeys.test_a_decorated_definition_carries_both_of_its_lines)
`ast.FunctionDef.lineno` is the `def` line. A reader looking at ... ok
test_an_undecorated_definition_attaches_at_its_own_line (tests.test_one_owner.TestSameKeys.test_an_undecorated_definition_attaches_at_its_own_line) ... ok
```

Two decorators on one function: `lineno` is 3 (the `def`), `attach` is 1
(the first `@`). For an assignment and for an undecorated function the two
are equal.

## I3 — the name census. **PASS**

```
test_every_shape_a_counterpart_can_name_is_collected (tests.test_one_owner.TestDefinedNames.test_every_shape_a_counterpart_can_name_is_collected) ... ok
test_a_name_bound_inside_a_function_is_not_a_module_name (tests.test_one_owner.TestDefinedNames.test_a_name_bound_inside_a_function_is_not_a_module_name)
`local` above is absent, and deliberately: `<module>.<name>` is ... ok
test_a_function_below_the_fact_floor_is_still_a_name (tests.test_one_owner.TestDefinedNames.test_a_function_below_the_fact_floor_is_still_a_name)
The whole point. One key is not a shape, so this states no ... ok
test_unparseable_source_names_nothing_and_raises_nothing (tests.test_one_owner.TestDefinedNames.test_unparseable_source_names_nothing_and_raises_nothing)
fact_sites already reports the broken module. A second report ... ok
```

## Cost of the second parse

`defined_names` parses each module a second time. Measured, warm, three
runs each, `one_owner.py` over this repo:

```
=== before (ef8f1e2), 3 runs, user time ===
python3 one_owner.py > /dev/null  0.76s user 0.16s system 15% cpu 6.055 total
python3 one_owner.py > /dev/null  0.22s user 0.03s system 92% cpu 0.271 total
python3 one_owner.py > /dev/null  0.22s user 0.03s system 94% cpu 0.255 total
=== after (branch), 3 runs, user time ===
python3 one_owner.py > /dev/null  0.27s user 0.02s system 96% cpu 0.310 total
python3 one_owner.py > /dev/null  0.28s user 0.03s system 90% cpu 0.346 total
python3 one_owner.py > /dev/null  0.28s user 0.03s system 94% cpu 0.326 total
```

Steady state 0.22s → 0.28s user. The first "before" run is a cold cache and
is quoted rather than dropped — dropping the inconvenient sample is how a
benchmark starts lying.

## What was NOT verified

- **No live instance exists to verify against.** `defect.md` measured one
  decorated definition across 28 root modules (`cli.py:170 harness_run`),
  carrying no marker, and no live marker names a non-fact counterpart. Both
  fixes are therefore verified entirely on fixtures and on the probe. That
  is the correct depth for a diagnostic that is currently unreachable in
  this tree, but it is not field evidence and is not claimed as any.
- **The `min()` over multiple decorators is pinned at two, not at one.**
  `test_a_decorated_definition_carries_both_of_its_lines` uses two
  decorators, so it would fail if the code took the *last* one. It does not
  distinguish `min(...)` from `decorator_list[0].lineno`, because nothing
  can — they are equal for source-ordered input, which is what the parser
  produces. The choice between them is a readability decision recorded in
  `architecture.md` D3, not a behaviour this suite could pin.
- **`ast.walk` reach for `defined_names` is pinned for a nested function
  and a nested class, not for every nesting depth.** The rule is
  "whatever `same-keys` can reach", and both use `ast.walk`, so depth is
  not a separate axis.
- **`python3 trigger_eval.py` and `python3 charter_replay.py` were not
  run.** They are real model runs that cost money, are never in CI, and
  touch nothing this change reaches.

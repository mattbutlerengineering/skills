---
stage: verify
run: maintenance:the-one-fake-is-not-the-only-one
date: 2026-08-30
---

# Verification — the one fake is not the only one

Every command below was run on this branch. Output is quoted, not
summarized.

## 1. The seam has one fake, and the roll-call is derived

`tests/test_fake_gh.py` parses every module under `tests/` for a class
with `__call__(self, args)` — the shape of `cli.gh_runner`'s port.

```
$ python3 -c "
import sys; sys.path.insert(0,'tests')
from test_fake_gh import runner_modules
for m, c in runner_modules(): print(f'{m}: {c}')"
fake_gh.py: FakeGh
```

It parses rather than greps, and the difference is visible in this very
tree: a plain `grep` finds a second hit, inside the string literal the
detector's own self-test parses.

```
$ grep -n "def __call__" tests/*.py
tests/fake_gh.py:61:    def __call__(self, args):
tests/test_fake_gh.py:166:                  "    def __call__(self, args):\n"
```

## 2. The detector is RED on the tree it was written for

Stashed to `origin/main` and run there:

```
$ git stash -q -u && python3 <the same walk> ; git stash pop -q
on origin/main: [('fake_gh.py', 'FakeGh'), ('test_work_queue.py', 'RecordingRunner'), ('test_work_queue.py', 'FailingRunner')]
```

And through the suite: `tests/test_work_queue.py` restored from
`origin/main` (`git show origin/main:… > …`), this run's test module
left in place, then put back.

```
$ python3 -m unittest tests.test_fake_gh
FAIL: test_the_seam_has_exactly_one_fake_and_it_is_fake_gh
AssertionError: Lists differ: [('fa[15 chars]eGh'), ('test_work_queue.py', 'RecordingRunner[39 chars]er')] != [('fa[15 chars]eGh')]
Ran 14 tests in 0.117s
FAILED (failures=1)
```

Thirteen of the fourteen passed at that point: those are the behaviour
pins, which were missing coverage rather than broken behaviour.

## 3. Every suite at the seam reaches it through the shared fake

Nine now, where the docstring named four:

```
$ grep -n "from fake_gh import" tests/*.py
tests/test_assembler.py:29:from fake_gh import FakeGh  # noqa: E402
tests/test_dashboard.py:172:    from fake_gh import FakeGh
tests/test_fake_gh.py:21:from fake_gh import FakeGh, default_error  # noqa: E402
tests/test_gate_digest.py:30:from fake_gh import FakeGh  # noqa: E402
tests/test_label_sync.py:20:from fake_gh import FakeGh  # noqa: E402
tests/test_rejection_mining.py:28:from fake_gh import FakeGh  # noqa: E402
tests/test_sweeps.py:24:from fake_gh import FakeGh  # noqa: E402
tests/test_validator.py:21:from fake_gh import FakeGh  # noqa: E402
tests/test_work_queue.py:19:from fake_gh import FakeGh  # noqa: E402
```

The docstring no longer carries the list at all — that is what went
stale — and says where the derived one lives instead.

## 4. The fold preserves every assertion

`tests/test_work_queue.py` is unchanged in what it asserts; only how it
says "here is what gh answers" changed. The suite is green and the same
size:

```
$ python3 -m unittest tests.test_work_queue
Ran 26 tests in 0.014s

OK
```

Both private classes are gone:

```
$ grep -c "RecordingRunner\|FailingRunner" tests/test_work_queue.py
0
```

The `CalledProcessError(1, "gh")` with no stderr is now passed through
`error=` explicitly, which is exactly what the shared fake's docstring
already asked a suite on a different `cli.detail` path to do.

## 5. The fake's three declared behaviours are asserted

They were asserted nowhere before this run.

```
$ python3 -m unittest tests.test_fake_gh -v 2>&1 \
    | grep 'ok$' | sed 's/ (tests.*)//'
test_a_callable_answer_sees_the_whole_argv ... ok
test_an_unmatched_argv_answers_the_empty_string ... ok
test_called_filters_the_record_by_prefix ... ok
test_the_longest_matching_prefix_wins ... ok
test_a_call_without_a_body_file_is_recorded_verbatim ... ok
test_the_recorded_call_carries_the_body_not_the_path ... ok
The detector, run against a class shaped like the ones this ... ok
`__call__(self, cmd)` is some other callable — a harness ... ok
test_the_seam_has_exactly_one_fake_and_it_is_fake_gh ... ok
test_a_suite_that_needs_another_cli_detail_path_states_it ... ok
test_the_default_is_a_called_process_error_carrying_stderr ... ok
test_a_failing_call_computes_its_answer_before_raising ... ok
test_a_failing_call_is_recorded_before_it_raises ... ok
test_only_the_failing_prefix_raises ... ok
```

Fourteen lines for fourteen tests. Two of them read as prose because
unittest prints a test's docstring first line where it has one: those
are `test_the_rule_can_see_a_private_fake` and
`test_the_rule_does_not_fire_on_a_callable_that_is_not_the_port`.

`test_a_failing_call_computes_its_answer_before_raising` is the one that
would have caught `FailingRunner`: it injects a callable answer and
asserts the callable ran before the raise.

## 6. The full battery

```
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
$ python3 -m unittest discover tests
Ran 1358 tests in 16.445s

OK
$ python3 one_owner.py | tail -1
one-owner: 9 problem(s)
```

Baseline on `origin/main` is 1344; this run adds fourteen, all in
`tests/test_fake_gh.py`. `one_owner.py` reports the same 9 as
`origin/main` — no second owner introduced, and none removed either,
because it excludes `tests/**` from its universe by a recorded
assumption. That exclusion is why this duplication needed a human to
find it, and it is already a backlog seed from
`maintenance:one-fact-one-owner`.

## What was NOT verified

- **No production module changed.** This run touches `tests/` only, so
  no manifest regeneration is owed and none was run. Confirmed by the
  diff: three files, all under `tests/`, plus the run artifacts.
- **The detector's rule is a signature, not a proof.** A private fake
  that spells its parameter something other than `args`, or that is a
  closure rather than a class, is invisible to it. That is stated in
  `defect.md`'s assumptions and in the test's own docstring; the rule
  identifies exactly the shape it is named after, and today across all
  of `tests/` that signature occurs in exactly the places it should.
- **The six suites that already used the shared fake were not
  re-examined** for whether they lean on behaviour the fake does not
  declare. They are green, which is the only claim made about them.

---
stage: diagnose
run: maintenance:a-shadowed-definition-is-invisible
date: 2026-08-30
assumptions: []
---

# Defect: a shadowed definition deletes tests and the suite says OK

## What happens

Python rebinds a name without complaint. A module that defines
`class TestScaffoldSync` twice simply keeps the second; `unittest`
discovery only ever sees the last binding, and every test in the first
class stops running.

Nothing reports it. Not the interpreter, not `unittest`, not `lint.py`,
not `gates.py`. **The suite reports `OK`.**

## How it was found

It happened here, mid-run, during the fix in
`docs/fixes/json-that-is-not-utf8/`. A second `class TestScaffoldSync`
was appended to `tests/test_gates.py`, silently deleting the three
tests in the original class.

The only signal was arithmetic: base was 1344 and six tests had been
added, so the total should have been 1350. It said 1347.

If nobody does that subtraction — and nothing in CI does — the loss is
permanent and invisible. A detector's tests can quietly stop running
and the gate keeps reporting green forever.

## Reproduction

Append a duplicate class to `tests/test_gates.py`:

```python
class TestScaffoldSync(unittest.TestCase):
    def test_planted(self):
        self.assertTrue(True)
```

```
$ python3 -m unittest tests.test_gates
Ran 161 tests in 0.348s

OK
```

163 before, 161 after: one test added, three destroyed, verdict
unchanged. That `OK` is the whole defect.

## Is it live today?

No. Every tracked Python file was swept — module-level names and
per-class method names, all 98 files git tracks:

```
universe: 98
problems: 0
```

So this is a latent hazard, not a present bug. It is worth a check
anyway, for the reason above: the failure mode is a **green** suite,
which means the usual signal that something is wrong never arrives. A
hazard that CI cannot report is exactly the kind worth spending a check
on, and this one was reached by accident inside a single review.

## Why the file universe is not rglob

`rglob("*.py")` finds 250 Python files here; git tracks 98. The
difference is stale `.claude/worktrees/agent-*` checkouts — months-old
full copies of the tree, hidden by a **local, uncommitted**
`.git/info/exclude`, so no committed file can be relied on to hide
them. A walking check would report a shadowed definition inside a copy
of a file the tracked tree has since fixed.

`one_owner.source_files` already states this and already uses
`git ls-files`. This check follows it — with one difference: one_owner
excludes `tests/`, and `tests/` is precisely the scope that needs this
check, because a shadowed *test* class is the case that fails silently.

---
stage: capture
run: maintenance:the-one-fake-is-not-the-only-one
date: 2026-08-30
re-entry: implement
assumptions:
  - Folding the two private fakes preserves every assertion. Both are
    argv-recording runners with canned answers, which is exactly what
    FakeGh is; the tests assert on the recorded calls and on the
    problem strings, never on the fake's own type.
  - A test module that defines a callable taking (self, args) is
    reaching cli.gh_runner's seam with its own fake. Across all of
    tests/ that signature appears three times today — the shared fake
    and the two private ones — so the rule identifies exactly the
    thing it is named after and nothing else.
---

# The one fake is not the only one

## What is wrong

`tests/fake_gh.py` opens:

```
"""The one fake gh at cli.gh_runner's seam.

cli.gh_runner promises "tests inject a fake runner so they never touch
the network"; this is that fake, shared by every suite at the seam
(test_validator, test_sweeps, test_label_sync, test_gate_digest). A
suite declares WHAT gh says — canned stdout keyed by argv prefix —
never HOW a fake behaves.
```

Both halves of that are false.

## Reproduction

Seven suites import it, not four:

```
$ grep -n "from fake_gh import" tests/*.py
tests/test_assembler.py:29:from fake_gh import FakeGh  # noqa: E402
tests/test_dashboard.py:172:    from fake_gh import FakeGh
tests/test_gate_digest.py:30:from fake_gh import FakeGh  # noqa: E402
tests/test_label_sync.py:20:from fake_gh import FakeGh  # noqa: E402
tests/test_rejection_mining.py:28:from fake_gh import FakeGh  # noqa: E402
tests/test_sweeps.py:24:from fake_gh import FakeGh  # noqa: E402
tests/test_validator.py:21:from fake_gh import FakeGh  # noqa: E402
```

And it is not the one fake. `tests/test_work_queue.py` keeps two of its
own at the same seam, used by nine call sites:

```
$ grep -n "def __call__" tests/*.py
tests/fake_gh.py:54:    def __call__(self, args):
tests/test_work_queue.py:45:    def __call__(self, args):
tests/test_work_queue.py:57:    def __call__(self, args):
```

## The divergence has already restarted

`fake_gh.py` exists because "the four suites' private fakes had diverged
on three behaviors", and it states the choices. The first:

```
- Record, then compute, then raise. Every call lands in `calls` first,
  its canned answer is computed, and only then does a failing prefix
  raise — a failed call is visible with exactly the shape a successful
  one would have, which preserves the most information for assertions.
```

`tests/test_work_queue.py:57` does not do that:

```python
    def __call__(self, args):
        self.calls.append(list(args))
        raise self.error
```

It records and raises. Nothing is computed. That is one of the three
behaviours the shared fake was written to settle, diverging again in a
file the settlement never reached.

## The failure scenario

A maintainer changes one of the three declared behaviours — say
`--body-file` starts resolving relative paths, or the default error
grows a field. They read the docstring, see four suites named, check
those four, and ship. Three other suites were never looked at, and
`test_work_queue.py` is not affected at all because it never used the
shared fake — so its own idea of how a failing gh behaves drifts further
from everyone else's, silently, which is the exact condition the file's
own second paragraph describes as the problem it solved.

## And nothing tests the fake

```
$ grep -rn "fake_gh\." tests/*.py | grep -v "^tests/fake_gh.py"
$ echo "exit=$?"
exit=1
```

Seven suites depend on it. Its three declared behaviours are asserted
nowhere. A change to any of them fails somewhere downstream, in a test
whose name is about work orders or gate digests, or it fails nowhere at
all.

## Re-entry

`implement`. Both private fakes are argv-recording runners with canned
answers, which is what `FakeGh` already is.

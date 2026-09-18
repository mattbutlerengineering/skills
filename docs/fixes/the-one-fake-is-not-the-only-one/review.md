---
stage: review
run: maintenance:the-one-fake-is-not-the-only-one
date: 2026-08-30
---

# Review — the one fake is not the only one

## What was examined

The whole diff: `tests/fake_gh.py` (the corrected roll-call),
`tests/test_work_queue.py` (the fold), and the new
`tests/test_fake_gh.py`. Three passes: correctness, design, security.

## Findings

### Major — 1, fixed during implement

**The self-test that proves the detector works had its own copy of the
detector.** `test_the_rule_can_see_a_private_fake` originally parsed a
synthetic class with an inline `ast.walk` comprehension rather than
calling `runner_modules`, because `runner_modules` was hardcoded to
`tests/`.

*Failure scenario.* The rule is changed — it starts matching
`__call__(self, argv)`, or it learns to look inside functions. The
inline copy in the self-test is not changed with it, so the self-test
keeps passing against a rule that no longer exists, and the one test
whose job is to prove the detector is not vacuous becomes exactly that.

The irony is the point: a run about a duplicated fake shipped a
duplicated walk.

*Fixed.* `runner_modules(directory=TESTS)` takes the directory, and both
self-tests call it against a `TemporaryDirectory`. One walk, three
callers.

### Minor — 2, both accepted

**`unreachable()` narrows the failure from every call to `issue`-prefixed
calls.** The class it replaced raised unconditionally. Checked rather
than assumed: `work_queue` makes exactly one gh call.

```
$ grep -n "gh_read(\|run(\[" work_queue.py
180:    read = gh_read(list(LIST_ARGS), "gh issue list", label="wq",
$ sed -n '/^LIST_ARGS/,+1p' work_queue.py
LIST_ARGS = ["issue", "list", "--label", READY_LABEL, "--state", "open",
             "--json", "number"]
```

A prefix that names the call is more legible than the empty prefix that
would match everything, and if `work_queue` grows a second gh call the
narrower fake is the one that will show the difference.

**Parsing every module under `tests/` on each of the three roll-call
tests.** Forty-odd modules, three times. Measured at 0.118s for the
whole suite, against a 15.6s full battery. Caching it would be
premature.

## Observations — not findings

**The rule is a signature, not a proof.** A private fake spelled
`__call__(self, argv)`, or written as a closure, is invisible to it.
`test_the_rule_does_not_fire_on_a_callable_that_is_not_the_port` pins
the other side of that trade deliberately: matching every `__call__`
would report `test_dashboard`'s `FakeServer` and `test_cli`'s
`FakeProcess` as private gh fakes, and a rule that cries wolf is one the
next reader learns to ignore. The narrow rule catches the shape that
actually recurred; `defect.md`'s assumptions record the limit.

**`one_owner.py` cannot see any of this, and that is already known.** It
excludes `tests/**` by a recorded assumption, and a backlog seed from
`maintenance:one-fact-one-owner` asks for that exclusion to be decided
against a re-derived count. This run is evidence for that seed rather
than a reason to reopen it here — it found a genuine second owner in
`tests/` that the pass is blind to by design.

**`tests/test_dashboard.py:172` imports the fake inside a function**
rather than at module scope, which is why the import survey in
`verification.md` §3 shows it indented. Left alone: it is how that suite
manages an optional import, not a divergence at the seam.

## Security

Nothing. `tests/` only, no production module changed, no network reached
— the change makes one more suite unable to reach it. No manifest
regeneration is owed and none was run.

## Fix / defer

| Finding | Severity | Decision |
| --- | --- | --- |
| The self-test carried its own copy of the detector | major | fixed during implement |
| `unreachable()` fails on the `issue` prefix, not every call | minor | accepted, `work_queue` makes exactly one gh call |
| The roll-call tests re-parse `tests/` | minor | accepted, 0.118s |
| The rule is a signature, not a proof | observation | recorded in `defect.md` assumptions and pinned from both sides |

No critical findings. The battery was re-run after the major fix and is
green (`verification.md` §6).

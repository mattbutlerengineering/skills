---
stage: verify
run: maintenance:a-shadowed-definition-is-invisible
date: 2026-08-30
assumptions: []
---

# Verification: a shadowed definition is invisible

## 1. The check catches the real bug that motivated it — PASS

Planted the exact mistake made during the previous run — a second
`class TestScaffoldSync` appended to `tests/test_gates.py`:

```
AssertionError: Lists differ: ['shadow: tests/test_gates.py:2126 ...'] != []

'shadow: tests/test_gates.py:2126 redefines TestScaffoldSync,
 shadowing the definition at line 604'
FAILED (failures=1)
```

The message locates the **rebinding**, not the lost definition — line
2126 is the line to delete. It names the shadowed line too, so the
reader can see what was lost without searching.

## 2. …while the suite it breaks still says OK — PASS

Same plant, same moment, the suite that actually lost the tests:

```
$ python3 -m unittest tests.test_gates
Ran 161 tests in 0.348s

OK
```

163 clean, 161 planted: one test added, three destroyed, `OK` either
way. This is the criterion that justifies the whole run — without the
new check, nothing anywhere reports this.

Both mutations reverted; `git diff --stat -- tests/test_gates.py` is
empty.

## 3. The grammar is right at the edges — PASS

Seven unit tests over the pure function, each an edge that a naive
"count the names" check gets wrong:

| Case | Verdict |
|---|---|
| rebound module-level class | problem, located at the rebinding |
| rebound method | problem, named `Class.method` |
| same name in two different classes | **not** a problem — one body is one scope |
| module function and method sharing a name | **not** a problem |
| `if/else` conditional definition | **not** a problem — nested in the `if`, never a sibling in `body`, so out of scope by construction rather than by a special case |
| `@property` + `@v.setter` | **not** a problem — the one same-scope rebinding Python intends |
| three definitions of one name | **two** problems, not one |
| unparsable source | a `cannot be parsed` problem, not a traceback |

## 4. The repo is clean today — PASS

All 98 tracked Python files, module scope and class scope:

```
universe: 98
problems: 0
```

An empty universe is asserted to be a failure, not a pass — a broken
`git ls-files` must never read as "no shadowed definitions", the same
posture `one_owner.source_files` takes.

## 5. Full battery — PASS

Base `main` is 1344; this branch is 1352. Eight added, none lost —
and this time the arithmetic is checked by a test rather than by hand.

```
$ python3 -m unittest discover tests
Ran 1352 tests in 20.209s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills

$ python3 gates.py
gates: 0 problem(s)

$ python3 gates.py --selftest
selftest: ok
```

No payload change: the new file is a test, and `factory_init.MIRRORS`
does not carry it (asserted, not assumed — `False`). No
`update-manifest` needed.

## What is NOT verified

- **Non-definition rebindings are out of scope.** A module-level
  constant assigned twice (`X = 1 ... X = 2`) is not reported. It is a
  much noisier signal — legitimate reassignment is ordinary Python —
  and it does not have the silent-test-loss consequence that motivates
  this check.
- **Imports that shadow a definition** (`from x import go` after
  `def go()`) are not reported, for the same reason.
- The check runs in the test suite, not in `gates.py`, so a downstream
  stamped repo does not inherit it. See `review.md` §1.

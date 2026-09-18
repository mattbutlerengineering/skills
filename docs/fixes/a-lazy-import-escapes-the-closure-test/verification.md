---
stage: verify
run: maintenance:a-lazy-import-escapes-the-closure-test
date: 2026-08-30
assumptions: []
---

# Verification: a lazy import escapes the payload closure test

## 1. The derivation finds all three, and hand-types none — PASS

```
derived: ['assembler', 'human_gates', 'label_sync'] | unfollowed: []
```

`label_sync` comes from the string literal; `assembler` and
`human_gates` from `LABEL_DECLARERS`, reached by resolving the loop
variable `name` back through `for name, pull in sorted(
LABEL_DECLARERS.items())`. Nothing in the test names a module.

## 2. A module dropping out of MIRRORS fails the test — PASS

Removed `("label_sync.py", "tools/factory/label_sync.py", identity)`
from `factory_init.MIRRORS`:

```
AssertionError: Lists differ: ['label_sync'] != []
gates.py lazily imports a module MIRRORS does not carry: in a stamped
repo the import fails, `except ImportError` swallows it, and the
detector goes silent instead of red
FAILED (failures=1)
```

## 3. A new lazy import of an unshipped module fails the test — PASS

Added `importlib.import_module("plane_drift")` to detector J:

```
AssertionError: Lists differ: ['plane_drift'] != []
FAILED (failures=1)
```

`plane_drift` is the real example CLAUDE.md names as deliberately
root-only, so this is the exact mistake the invariant exists to prevent.

## 4. An import shape the derivation cannot follow fails LOUDLY — PASS

Changed the literal to a computed expression,
`importlib.import_module("label_" + "sync")`:

```
AssertionError: Lists differ: ["gates.py:837 import_module('label_' + 'sync')"] != []
FAILED (failures=1)
```

This is the criterion that keeps the test honest. Without it a third
import shape would narrow the derived set to nothing and the assertion
would pass against an empty universe — the same silence the run is
closing. The message says to teach the test the new shape rather than
work around it.

The empty case is also guarded directly: `assertTrue(names, "derived no
lazily imported modules — the derivation is broken, not gates.py
clean")`.

## 5. A hiccup worth recording: a mutation that did not mutate

The first run of criterion 2 reported `OK`, and it was wrong. The edit
targeted `('label_sync.py', ...)` in single quotes; the source uses
double quotes, so `str.replace` matched nothing and changed no file. The
confirming `grep -c "label_sync.py'"` used the same wrong quote and
returned `0` — which reads as "removed" but actually meant "never
present in that form".

Caught by disbelieving a green mutation. Redone with an asserted
`s.count(old) == 1` before the replace, which is what the other two
mutations already did.

This is the second time this run pattern has produced a false-negative
mutation (`docs/fixes/a-call-site-list-that-drifted/verification.md` §3
records the first, an `_ = row_done` reference that was never a call).
The lesson is the same both times: **a mutation that produces a pass is
not evidence until the mutation itself is proven to have landed.**

## 6. Full battery — PASS

Base `main` is 1344; this branch is 1345. One test added.

```
$ python3 -m unittest discover tests
Ran 1345 tests in 17.818s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills

$ python3 gates.py
gates: 0 problem(s)

$ python3 gates.py --selftest
selftest: ok
```

All three mutations reverted; `git status --short` shows only
`tests/test_factory_init.py`.

No payload change — the only edited file is a test, which
`factory_init.MIRRORS` does not carry. No `update-manifest`.

## What is NOT verified

- Only `gates.py` is scanned. It is the only mirrored tool that reaches
  `importlib` at all (swept: no other payload module mentions
  `importlib` or `__import__`), so widening the scan today would add a
  loop over one item. If a second tool grows a lazy import, this test
  will not see it — noted in `review.md` §3.
- The test proves the module *ships*, not that it imports successfully
  in a stamped tree. That is
  `test_every_mirrored_tool_imports_from_the_payload_tree`'s job for
  static imports, and `test_stamped_repo_passes_its_own_gates`
  end-to-end.

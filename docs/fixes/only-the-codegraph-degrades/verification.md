---
stage: verify
run: maintenance:only-the-codegraph-degrades
date: 2026-08-27
assumptions: []
---

# Verification: only the codegraph degrades

Baseline on `origin/main` (622e7c0) is 1344 tests. This run adds six.

## 1 — the reported reproduction no longer reproduces

The same four probes from `defect.md`, unchanged, against the fixed
module:

```
=== A. a non-UTF-8 CONTEXT.md ===
  no exception
=== B. a non-UTF-8 cited ADR ===
  no exception
=== C. the SAME bytes in a .py file the row names ===
  - demo.py — (could not be parsed: UnicodeDecodeError)
=== D. an unreadable CONTEXT.md (chmod 000) ===
  no exception
```

A and B and D raised `UnicodeDecodeError` / `PermissionError` before
this change. PASS.

## 2 — the pack says what it could not read

The whole pack, with an undecodable CONTEXT.md, an undecodable cited
ADR, and the same bytes in the `.py` file the row names:

```
## Orientation pack: WO-0015

### CONTEXT.md

(CONTEXT.md could not be read: UnicodeDecodeError)
### ADR-0032: 0032-factory-dispatch-plane

(ADR-0032 could not be read: UnicodeDecodeError)
### Codegraph summary

- demo.py — (could not be parsed: UnicodeDecodeError)
```

Three file kinds, three notes, one prompt still built. The ADR keeps its
heading, so a reader can tell an unreadable citation from an absent one.

(The demonstration names WO-0015 — orientation_pack.py's own work order,
which has a real breakdown row — rather than the invented id the tests
use as a fixture, so that quoting the output here does not itself create
a dangling work-order citation for detector C. The pack body is
identical either way; only the heading differs.) PASS.

## 3 — the regression tests fail on the unfixed code

All six are RED against `origin/main`'s `orientation_pack.py` with the
new test file in place, and as *errors* rather than failures, which is
the shape of the defect — a traceback, not a wrong answer:

```
$ git show origin/main:orientation_pack.py > orientation_pack.py
$ python3 -m unittest tests.test_orientation_pack.TestAFileThePackCannotReadIsANoteNotACrash
ERROR: test_a_context_md_the_process_may_not_read_is_a_note
ERROR: test_an_undecodable_adr_keeps_its_heading_and_gains_a_note
ERROR: test_an_undecodable_context_md_is_a_note
ERROR: test_the_assembler_prompt_still_builds
ERROR: test_the_rest_of_the_pack_survives_an_unreadable_context_md
ERROR: test_the_same_bytes_degrade_whether_they_are_code_or_prose
Ran 6 tests in 0.009s

FAILED (errors=6)
```

PASS.

## 4 — the assembler CLI no longer takes the traceback

`assembler.py` contains no `except` anywhere, so a raise out of the pack
is the process exit — the consequence `_python_structure`'s docstring
names. `test_the_assembler_prompt_still_builds` drives
`assembler.assemble_prompt` over a tree with an undecodable CONTEXT.md:

```
$ python3 -m unittest tests.test_assembler
Ran 45 tests in 0.035s

OK
```

PASS.

## 5 — losing a file degrades the prompt, it does not empty it

`test_the_rest_of_the_pack_survives_an_unreadable_context_md` asserts
that with CONTEXT.md unreadable the cited ADR's body and the codegraph
summary are both still present:

```
$ python3 -m unittest tests.test_orientation_pack
Ran 30 tests in 0.025s

OK
```

PASS.

## 6 — the payload mirror and the manifest agree

`orientation_pack.py` is in `factory_init.MIRRORS`, so the payload copy
and the checksum manifest were regenerated:

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)

$ diff orientation_pack.py factory/templates/tools/factory/orientation_pack.py
$ python3 -m unittest tests.test_factory_init
Ran 52 tests in 1.236s

OK
```

Byte-identical, and detector E is green in the gate run below. PASS.

## 7 — the full battery

```
$ python3 -m unittest discover tests
Ran 1350 tests in 16.266s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills

$ python3 gates.py
gates: 0 problem(s)

$ python3 gates.py --selftest
selftest: ok
```

1344 + 6 = 1350. PASS.

## 8 — the free pre-pass is unmoved

```
$ python3 one_owner.py
one-owner: 9 problem(s)
```

Unchanged, and none of the nine names `orientation_pack.py`. PASS.

## Not verified

- **A real dispatch.** No work order was assembled against GitHub; the
  pack and the prompt were built in tempfile trees, which is how this
  module has always been tested (`root` is a repo tree, not an injected
  reader).
- **The permission branch under root.** `test_a_context_md_the_process_
  may_not_read_is_a_note` checks whether a mode-000 file is actually
  unreadable by this process and skips itself if not, so a CI container
  running as root would skip it rather than fail. It ran and passed
  locally; the `OSError` arm is otherwise unexercised there, and the
  undecodable cases cover the same `except` clause through `ValueError`.
- **Product repos in the field.** Whether any adopted repo currently has
  a non-UTF-8 CONTEXT.md is unknown and unknowable from here. The fix
  removes the failure mode; it does not survey for instances.

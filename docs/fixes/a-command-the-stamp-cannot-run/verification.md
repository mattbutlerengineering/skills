---
stage: verify
run: maintenance:a-command-the-stamp-cannot-run
date: 2026-08-27
assumptions: []
---

# Verification: a command the stamp cannot run

Baseline on `origin/main` (622e7c0) is 1344 tests. This run adds four.

## 1 — the reported reproduction no longer reproduces

The same two recipes appended to the real root Makefile, through the
real `product_makefile`:

```
=== the two new recipes as they land in the PAYLOAD Makefile ===
'\tpython3 tools/factory/work_queue.py plan'
'\tpython3 tools/factory/label_sync.py --apply'
```

Both were copied through verbatim before this change. PASS.

## 2 — the respelling now covers the whole payload

Every root file `MIRRORS` moves under `tools/factory/`, checked by
asking `product_form` directly:

```
=== which mirrored tools product_form respells ===
  gates.py                 respelled
  protocol.py              respelled
  knowledge_plane.py       respelled
  cli.py                   respelled
  factory_config.py        respelled
  cost_ledger.py           respelled
  label_sync.py            respelled
  validator.py             respelled
  assembler.py             respelled
  budget_guard.py          respelled
  handoff.py               respelled
  orientation_pack.py      respelled
  cost_report.py           respelled
  human_gates.py           respelled
  gate_digest.py           respelled
  rejection_mining.py      respelled
  work_queue.py            respelled
```

Seven before, seventeen now, and the list is `MIRRORS` rather than a
copy of it. PASS.

## 3 — the regression test fails on the unfixed code

`test_every_root_tool_mirrors_moves_is_respelled` is RED against
`origin/main`'s `factory_init.py`, once per pass-through tool:

```
$ git show origin/main:factory_init.py > factory_init.py
$ python3 -m unittest tests.test_factory_init.TestTheRespellingHasOneOwner
FAIL: test_every_root_tool_mirrors_moves_is_respelled (tool='cli.py')
FAIL: test_every_root_tool_mirrors_moves_is_respelled (tool='cost_ledger.py')
FAIL: test_every_root_tool_mirrors_moves_is_respelled (tool='factory_config.py')
FAIL: test_every_root_tool_mirrors_moves_is_respelled (tool='handoff.py')
FAIL: test_every_root_tool_mirrors_moves_is_respelled (tool='human_gates.py')
FAIL: test_every_root_tool_mirrors_moves_is_respelled (tool='knowledge_plane.py')
FAIL: test_every_root_tool_mirrors_moves_is_respelled (tool='label_sync.py')
FAIL: test_every_root_tool_mirrors_moves_is_respelled (tool='orientation_pack.py')
FAIL: test_every_root_tool_mirrors_moves_is_respelled (tool='protocol.py')
FAIL: test_every_root_tool_mirrors_moves_is_respelled (tool='work_queue.py')
Ran 4 tests in 0.002s

FAILED (failures=10)
```

PASS.

## 4 — the other three tests are pins, not reproductions

Stated plainly because it would otherwise read as four reproductions:
`test_a_file_mirrors_does_not_move_is_left_alone`,
`test_every_root_makefile_command_is_respelled_or_dropped` and
`test_the_payload_makefile_names_no_root_level_tool` pass against
`origin/main` too. They have to — today's root Makefile invokes only the
seven tools the old tuple carried, which is exactly why the defect is
latent rather than live. Their job is to fail on the day someone adds a
target for an eighth. The suite as a whole is therefore RED on the
unfixed code (failures=10 above), and one of its four tests is the
reproduction:

```
$ python3 -m unittest tests.test_factory_init.TestTheRespellingHasOneOwner
Ran 4 tests in 0.001s

OK
```

PASS.

## 5 — the completed hand-typed list is a completeness fix, not a defect

`TestProductForm.test_each_factory_tool_moves_under_tools_factory`
listed six of the seven respelled tools — `budget_guard.py` was absent.
It is renamed and completed here, and it passes against `origin/main`
either way, because the *tuple* had `budget_guard.py` even though the
test's copy did not. Recorded as a third copy of the same fact, not as a
second bug:

```
$ git show origin/main:factory_init.py > factory_init.py
$ python3 -m unittest tests.test_factory_init.TestProductForm
Ran 3 tests in 0.000s

OK
```

PASS.

## 6 — no behaviour change today

The proof that this is structural: regenerating the payload leaves the
generated Makefile and the checksum manifest untouched.

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)

$ git status --short
 M factory_init.py
 M tests/test_factory_init.py
?? docs/fixes/a-command-the-stamp-cannot-run/
```

`factory/templates/Makefile` and `factory/manifest.json` are absent from
that list. PASS.

## 7 — the full battery

```
$ python3 -m unittest discover tests
Ran 1348 tests in 16.151s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills

$ python3 gates.py
gates: 0 problem(s)

$ python3 gates.py --selftest
selftest: ok
```

1344 + 4 = 1348. PASS.

## 8 — the free pre-pass is unmoved

```
$ python3 one_owner.py
one-owner: 9 problem(s)
```

Unchanged at nine, and none of them names `factory_init.py` — which is
worth saying, because deleting `_PRODUCT_TOOLS` removed a duplicate this
pass never saw: it looks for equal constants and shared payload keys,
and a proper subset of a table's first column is neither. PASS.

## Not verified

- **A real stamp into a real product repo.** No `stamp` was executed
  against an external tree; the payload Makefile was compared as bytes
  instead, which is the stronger check for this change (identical output
  means no stamped repo can observe it).
- **The remaining hand-enumerated lists.** `TestLockstep`'s target
  constants in `tests/test_gates.py` are still typed by hand, so a new
  Makefile target is compared to nothing there. Out of scope — that file
  is contended by two open PRs — and recorded in `review.md` as open
  with its owner.

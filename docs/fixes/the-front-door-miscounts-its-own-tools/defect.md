---
stage: capture
run: maintenance:the-front-door-miscounts-its-own-tools
date: 2026-08-28
re-entry: implement
assumptions:
  - The count is removed rather than corrected. Correcting it to
    seventeen re-arms the same drift for the next tool, and the number
    is one `python3 factory.py help` away from any reader who wants it.
    Everything else in this file is derived on purpose.
  - The pin belongs in the test, not in the router. factory.py states
    that any logic landing there is logic that stopped being testable
    where it lives, and the mechanical scan of CLI-bearing modules is
    already in tests/test_factory_cli.py.
---

# Defect — the router's docstring undercounts the tools it routes to

## Summary

`factory.py`'s module docstring opens:

> factory: the one front door over the root tools' CLI legs (issue
> #237). **Fourteen root modules** carry a CLI and every one is invoked
> by filename; this is the index that did not exist and a dispatcher
> over the mains that already do.

`factory.VERBS` has seventeen entries, and `tests/test_factory_cli.py`
asserts that set equals a mechanical scan of every root module carrying
an `if __name__ == "__main__":` guard. So the number is not approximately
right or a matter of definition — the file's own table, pinned by its own
test, says seventeen.

```
$ python3 -c "import factory; print('VERBS:', len(factory.VERBS))"
VERBS: 17
```

The same number is echoed in the test file, in the docstring explaining
why the convention column is derived in the test rather than in the
router:

> The derivation lives in the test, not in the router: factory.py runs on
> every push and must import one module per invocation, not **fourteen**.

## Why this is the one place it could happen

The module's stated discipline is that it restates nothing:

> A ROUTER, NOT A SEAM: every verb delegates to a module's main() and the
> router owns no knowledge of its own. The verb IS the module's name
> (underscores hyphenated) — one vocabulary, not two; **the index line IS
> the module's own docstring first line, read at print time**; and
> tests/test_factory_cli.py pins the verb table to a mechanical scan of
> the CLI-bearing root modules, so adding or retiring a tool breaks the
> build until the table follows.

Every fact in the file is derived — the verb from the module name, the
index line from the module's docstring at print time, the table from a
filesystem scan, and (per ADR-0054) even the calling convention from each
main's signature. The count in the opening sentence is the single
hand-typed fact, and it is the one that drifted.

Nothing catches it. The test file derives the *set* and never reads the
prose beside it.

## Reproduction

```
$ python3 -c "import factory; print(len(factory.VERBS))"
17
$ grep -c . /dev/null; grep -o 'Fourteen root modules' factory.py
Fourteen root modules
$ python3 factory.py help | grep -c '^  [a-z]'
17
```

## Impact

Bounded and documentary — no verb is missing, no dispatch is wrong, and
`python3 factory.py help` has always printed all seventeen. What is wrong
is the first sentence a reader or an agent meets when orienting on the
factory's tool surface, and it is wrong by twenty-one percent in the
direction of "there is less here than there is".

## Checked and not a finding

Three other hand-typed counts in the root modules were checked against
the structures they describe, and all three are accurate:

- `cli.py:345` and `tests/test_cli.py:137` — "fourteen call sites" for
  `cli.gh_read`. Counted: 14 in production code (assembler 1, dashboard
  3, gate_digest 2, label_sync 1, rejection_mining 3, sweeps 2,
  validator 1, work_queue 1). Correct, and `cli.py` is contended.
- `gate_digest.py:5`, `human_gates.py:36` and `human_gates.py:47` —
  "three gates". `len(human_gates.GATES)` is 3. Correct.
- `factory_roles.py:3` — "two files each role is encoded in" (agent stub
  plus charter). Correct; `charter_path` and `agent_path` are the two.

So this is one stale count, not a class of them — and that is worth
saying, because a run that reported "the repo hand-types counts" would be
claiming something the sweep does not support.

## Fix

Remove the count from `factory.py`'s opening sentence rather than
correcting it, since correcting it re-arms the same drift for the next
tool. Correct the echo in the test file's prose. Add a pin: the router's
docstring must state no count of the modules, tools, or verbs its table
owns, with a non-vacuity check that the pin catches the exact sentence
that drifted.

## Breakdown

- [x] The router states no count the table owns. Criterion: a check over
      `factory.__doc__` finds no `<number> modules|tools|verbs` phrase.
- [x] The pin is not vacuous. Criterion: the same check, over the literal
      sentence that was in the file, finds it.
- [x] The test file's prose agrees. Criterion: the sentence explaining
      why the convention column is derived no longer names a stale count,
      and the only occurrences of the word left in the file are the pin's
      own number-word alternation and the class docstring recording what
      drifted — both statements about the pin, not counts of the table.
- [x] Nothing about the table changed. Criterion: the existing
      mechanical-scan tests still pass unmodified, and `VERBS` still has
      seventeen entries covering every CLI-bearing root module.

---
stage: review
run: maintenance:marker-diagnostics-that-lie
date: 2026-08-25
assumptions: ["Scaled as the protocol's Run scale section asks for a scoped maintenance fix: three passes over this run's diff only, with the Verify regression as the floor rather than re-run. The pass went past the two routed diagnostics into the surrounding file, which is what surfaced F1 and F3 — both defects this run introduced and neither reachable from the seed."]
---

# Review: two marker diagnostics that state what is actually true

## What was examined

`git diff 5d993dc..HEAD` — `one_owner.py` and `tests/test_one_owner.py`,
227 insertions and 23 deletions, plus the run artifacts. Three passes:
correctness, design, security.

Not re-examined: anything Verify already settled. Its evidence is the
floor, not a thing to repeat.

## F1 — the shape's own comment still named the old join key. **Major. Fixed.**

`one_owner.py:73-75` documented `FactSite` as:

```
# What one module states, at one place. `identity` is the grouping key
# and `lineno` is the definition's own line — the join key a marker
# above it is attached by.
```

After this run `attach` is the join key. The new comment was appended
below the old one, so the block said both things — and the wrong half came
first, at the exact place a reader goes to learn the shape.

**Failure scenario.** The next author needs the line a comment block above
a definition ends at. They read the first sentence, join against `lineno`,
and re-create the defect this run exists to remove — with a passing suite,
because no case pins `lineno` as a join key.

**Fix.** The two comments are one comment now, and it says which field is
which: `lineno` is where a problem string points a reader, `attach` is the
join key, and they differ only for a decorated definition.

## F2 — `defined_names` stated its reach rule backwards. **Minor. Fixed.**

As written the docstring said reach is "matched to what can BECOME a fact
site, so the two answers cannot disagree". Both halves are wrong.

*Matched* is wrong: the function exists precisely to be **broader** than
`fact_sites`. A one-key function is defined and states no fact — that gap
between the two sets is the whole new branch.

*Cannot disagree* is wrong in the other direction: `defined_names` is not
complete, and F4 below names where.

**Fix.** The rule now reads as a superset invariant — a name `fact_sites`
finds and `defined_names` misses would be reported as deleted while the
pass looks straight at it — and the invariant is checked mechanically over
every root module, not asserted:

```
root modules checked: 28
fact-site names absent from defined_names: []
```

## F3 — the scripted insertion damaged two blank-line boundaries. **Minor. Fixed.**

Two blank lines before `test_a_decorated_definition_carries_both_of_its_lines`
inside `TestSameKeys`, and one — not two — before `class TestDefinedNames`.
Both are artefacts of inserting text at a class boundary anchor, and
neither is caught by anything: `lint.py` lints skills, not Python, and this
repo runs no Python style checker.

**Failure scenario.** None at runtime; the cost is a file that stops
looking like the file it is, one insertion at a time, with no gate to
notice. Recorded as a finding rather than fixed silently because "the
tooling didn't catch it" is the reason it survives.

**Fix.** Both boundaries corrected, then the whole file audited rather
than just the two spots:

```
=== blank-line audit: every class/def boundary in the diff region ===
problems: none
```

Line length was checked the same way — ten over-79-column lines at
5d993dc, ten at HEAD, so this run added none and touched none.

## F4 — `ast.AnnAssign` is invisible to both readers. **Minor. Deferred.**

A module-level `TIMEOUT: int = 30` is an `ast.AnnAssign`, not an
`ast.Assign`. `defined_names` does not collect it, so a marker naming one
still gets "which is not defined in this repo" — the exact false message
this run removes elsewhere.

**Failure scenario.** Concrete and reachable by writing ordinary Python:
annotate a module-level constant, write a carve-out naming it, and the
pass reports it as deleted.

**Why deferred, not fixed.** Zero of the 28 root modules bind a name that
way today:

```
module-level node kinds across 28 root modules:
Counter({'FunctionDef': 331, 'Assign': 171, 'Import': 109, 'ImportFrom': 92, 'Expr': 28, 'If': 18, 'ClassDef': 2})
```

And more decisively: `fact_sites` is blind to `AnnAssign` too, so an
annotated constant can never be a duplicate the pass finds — a marker
naming one is pointless whatever the message says. Widening only
`defined_names` would make the pair *more* asymmetric, not less. The
coherent change teaches both readers about the node, with its own
acceptance criteria, and that is a different run.

The gap is now named in `defined_names`' docstring rather than left for
someone to rediscover. Owed to Operate as a seed; this run stops at Ship
and appends nothing to `docs/backlog.md`.

## F5 — `<module>.<name>` cannot address a nested definition. **Observation, not a finding.**

`_ident` is `f"{Path(path).stem}.{name}"`, and both `fact_sites` and
`defined_names` reach nested definitions through `ast.walk`. So two
definitions with one name in one module are one identity. Real instances:

```
lint.py {'problems_for': 3}
charter_replay.py {'run': 2}
```

All five are nested closures; none is module-level.

**Not a finding against this change.** The ambiguity is `fact_sites`'
`ast.walk`, which predates this run, and `defined_names` inherits it
deliberately — diverging would break F2's superset invariant. It is
recorded here so a future reader does not attribute it to the new
function. Owed to Operate as a seed alongside F4.

## Correctness pass — what was checked and held

- **The two-start walk cannot steal a marker from another site.** The
  regions the two walks cover are the block above the first decorator and
  the block between decorator and `def`. A comment block between two
  definitions is walked only by the later one, which is the pre-existing
  behaviour; the new walk adds no overlap. Pinned at the boundary by
  `test_a_blank_line_still_ends_the_block_above_a_decorator`.
- **`min(..., default=node.lineno)` on an empty decorator list** returns
  the `def` line, so an undecorated function's two fields are equal. Pinned
  by `test_an_undecorated_definition_attaches_at_its_own_line`.
- **The three-way branch is exhaustive and ordered correctly.** A
  counterpart that is a fact site still reaches the group check unchanged;
  its two strings are pinned by cases this run did not touch.
- **`check`'s accumulator.** `defined` is seeded as a set and unioned per
  file inside the same loop that already reads each source, so no file is
  opened twice.

## Design pass

The change matches `architecture.md` with two logged deviations
(`breakdown.md` Notes): `min`'s `default=` in place of an emptiness
conditional, and a keyword default on the `site(...)` test helper. Neither
alters a contract.

No new module, no new import, no new dependency. `one_owner.py` is not in
`factory_init.MIRRORS`, so nothing mirrors and no manifest regenerates —
confirmed rather than assumed:

```
$ python3 -c "import factory_init; print(any('one_owner' in str(m) for m in factory_init.MIRRORS))"
False
```

## Security pass

Nothing. No new input boundary, no subprocess, no file write, no
network. `defined_names` parses source that `fact_sites` has already
parsed in the same loop, from the same git-derived universe.

## State after the fixes

```
Ran 1355 tests in 15.551s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
one_owner output IDENTICAL to 5d993dc (10 lines)
```

No critical findings. F1–F3 fixed in this run; F4 and F5 deferred with the
reasons above and owed to Operate as seeds.

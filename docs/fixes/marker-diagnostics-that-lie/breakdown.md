---
stage: decompose
run: maintenance:marker-diagnostics-that-lie
date: 2026-08-24
assumptions: ["Two milestones, not one, even though both fixes land in one PR. They share no code and no test: M1 is a join key, M2 is a name census. Cutting them apart means each can be reverted alone if a reviewer disagrees with only one, and means the suite says which one broke."]
---

# Breakdown: two marker diagnostics that state what is actually true

No work orders and no tracker mirror: this is a maintenance run, not a
dispatch. Issue #336 tracks the run as a whole.

## M1 — a marker above a decorated definition attaches

**Demonstrable at the boundary:** `markers` returns the marker and no
problem for the decorated module in `defect.md`'s reproduction.

- [x] **I1 — `FactSite` carries the attach line.**
  Add `attach` between `lineno` and `name`. `fact_sites` fills it from
  `min(d.lineno for d in node.decorator_list)` when that list is non-empty,
  else `node.lineno`; the `same-value` construction passes `node.lineno`
  for both. Update `TestDataModel`'s pin and the `site(...)` helper.
  *Acceptance:* `FactSite._fields` is
  `("kind", "path", "lineno", "attach", "name", "identity")`; a decorated
  function's site has `attach` at the `@` line and `lineno` at the `def`
  line; every other existing test passes untouched.

- [x] **I2 — `markers` walks up from both lines.** *(blocked by I1)*
  Walk from `site.lineno - 1` and from `site.attach - 1`.
  *Acceptance:* the decorated module from `defect.md` yields one marker and
  zero problems; a marker placed *between* the decorator and the `def`
  still yields one marker and zero problems; an undecorated module's
  behaviour is byte-identical; a marker two lines above a decorated
  definition with a blank line between still fails to attach, because a
  blank line ends the block.

## M2 — a counterpart that exists is not reported as deleted

**Demonstrable at the boundary:** `_rent`'s message for `defect.md`'s
`other.g` names the real problem.

- [x] **I3 — `defined_names(path, source)`.**
  Module-level `ast.Assign` targets from `tree.body`; every `FunctionDef`,
  `AsyncFunctionDef` and `ClassDef` from `ast.walk`. Returns a set of
  `<module>.<name>`; empty set for source that will not parse.
  *Acceptance:* a module binding a constant, a top-level function, a
  nested function and a class yields all four; a module that reads one key
  still yields its function name; unparseable source yields an empty set
  and raises nothing.

- [x] **I4 — `_rent` splits the counterpart branch three ways.** *(blocked by I3)*
  New `defined` parameter before `adr_ids`; `check` passes the union of
  `defined_names` over every file it read.
  *Acceptance:* a counterpart that exists but states no fact yields the new
  string; a counterpart that exists nowhere yields "which is not defined in
  this repo", unchanged; a counterpart that is a fact site reaches the
  group check and its strings are unchanged.

## M3 — the tool's own output is unchanged

- [x] **I5 — the standing findings are byte-identical.** *(blocked by I2, I4)*
  *Acceptance:* `python3 one_owner.py` prints exactly the eight problems and
  the `one-owner: 8 problem(s)` summary quoted in `defect.md`, and exits 1;
  `python3 -m unittest discover tests` green; `python3 lint.py` reports
  `lint: 0 problem(s)`; `python3 gates.py && python3 gates.py --selftest`
  reports `gates: 0 problem(s)` twice.

## Notes

*(dated deviations from the design go here)*

**2026-08-24 — I1, the test helper takes a default.** `architecture.md`
says the `site(...)` helper "gains the parameter"; implemented as
`attach=None` falling back to `lineno` rather than a required positional.
Every site those helpers build by hand is undecorated, so the default IS
the invariant, and threading a duplicate line number through `value(...)`
and `keys(...)` at nineteen call sites would have said nothing.

**2026-08-24 — I1, `min(..., default=node.lineno)`.** `architecture.md`
shows a conditional on a non-empty `decorator_list`; `min`'s own `default=`
expresses the same thing in one expression, so the empty case is not a
branch a reader has to check.

**2026-08-24 — I4, `_rent`'s old local is renamed.** The existing
`defined` local (built from fact sites) becomes `stated`, and `defined`
is now the new parameter. Renaming rather than inventing a third word:
the two sets answer "states a fact" and "exists", and the branch reads as
those two questions in that order.

**2026-08-24 — I5, the selftest's summary line.** The acceptance criterion
said `gates.py --selftest` reports `gates: 0 problem(s)`; it reports
`selftest: ok`. The criterion was written from CLAUDE.md's phrasing without
running the second command. Corrected here rather than in the criterion, so
the artifact records what the command actually says.

**2026-08-24 — I5, byte-identity was diffed, not read.** The eight standing
findings are compared as files (`diff before.txt after.txt`) against the
tool built at this run's last pre-code commit, not eyeballed. Both exit 1.

**2026-08-25 — the branch was rebased at Ship.** It had been cut from the
tip of the open `one-labels-walk` branch rather than from `main`, which
would have stacked this PR on that one. Rebased onto `origin/main`
(622e7c0); the seven commits replayed with no conflict, every measurement
in `verification.md` was re-derived against the new base, and the standing
findings went from eight to nine because PR #335's fold is not in it.

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

- [ ] **I1 — `FactSite` carries the attach line.**
  Add `attach` between `lineno` and `name`. `fact_sites` fills it from
  `min(d.lineno for d in node.decorator_list)` when that list is non-empty,
  else `node.lineno`; the `same-value` construction passes `node.lineno`
  for both. Update `TestDataModel`'s pin and the `site(...)` helper.
  *Acceptance:* `FactSite._fields` is
  `("kind", "path", "lineno", "attach", "name", "identity")`; a decorated
  function's site has `attach` at the `@` line and `lineno` at the `def`
  line; every other existing test passes untouched.

- [ ] **I2 — `markers` walks up from both lines.** *(blocked by I1)*
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

- [ ] **I3 — `defined_names(path, source)`.**
  Module-level `ast.Assign` targets from `tree.body`; every `FunctionDef`,
  `AsyncFunctionDef` and `ClassDef` from `ast.walk`. Returns a set of
  `<module>.<name>`; empty set for source that will not parse.
  *Acceptance:* a module binding a constant, a top-level function, a
  nested function and a class yields all four; a module that reads one key
  still yields its function name; unparseable source yields an empty set
  and raises nothing.

- [ ] **I4 — `_rent` splits the counterpart branch three ways.** *(blocked by I3)*
  New `defined` parameter before `adr_ids`; `check` passes the union of
  `defined_names` over every file it read.
  *Acceptance:* a counterpart that exists but states no fact yields the new
  string; a counterpart that exists nowhere yields "which is not defined in
  this repo", unchanged; a counterpart that is a fact site reaches the
  group check and its strings are unchanged.

## M3 — the tool's own output is unchanged

- [ ] **I5 — the standing findings are byte-identical.** *(blocked by I2, I4)*
  *Acceptance:* `python3 one_owner.py` prints exactly the eight problems and
  the `one-owner: 8 problem(s)` summary quoted in `defect.md`, and exits 1;
  `python3 -m unittest discover tests` green; `python3 lint.py` reports
  `lint: 0 problem(s)`; `python3 gates.py && python3 gates.py --selftest`
  reports `gates: 0 problem(s)` twice.

## Notes

*(dated deviations from the design go here)*

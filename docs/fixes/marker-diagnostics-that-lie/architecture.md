---
stage: architect
run: maintenance:marker-diagnostics-that-lie
date: 2026-08-24
assumptions: ["Chosen without live interview: this run is autorun-driven, so each option below is decided against something already recorded — ADR-0061's rule that a carve-out lives at the definition it excuses, the prior run's Data model table, and the existing problem-string register — with the citation given so the operator can overturn a call by reading rather than re-deriving.", "NO ADR is offered. The architect skill's bar is all three of hard to reverse, surprising without context, and the result of a real trade-off. Adding a field to an in-memory namedtuple and rewording one problem string is reversible by `git revert`, and the change APPLIES ADR-0061 rather than amending it — the pass currently refuses to honour markers that already satisfy it. What does need writing down is the supersession of one line in a previous run's Data model table, and that is what this artifact is for.", "The two-walk attach rule (D2) preserves a placement that only exists as a workaround for the bug being fixed. Kept deliberately: un-attaching it would convert working carve-outs into the exact false message this run exists to stop emitting."]
---

# Architecture: two marker diagnostics that state what is actually true

## Approach

Two independent one-function fixes in `one_owner.py`, sharing nothing but
the module. Each replaces a false statement with a true one; neither
changes what the pass *finds*.

1. **Diagnostic 1** is a join defect. `markers` needs to know where a
   definition begins *on the page*, and it has been using where the
   definition begins *in the AST*. For a decorated definition those are
   different lines. Fix: carry both on `FactSite`.
2. **Diagnostic 2** is a missing input. `_rent` asks "does this name
   exist?" and has only a set of names that *state facts* to answer it
   with. Fix: give it a second set — every name the tree binds — and
   split the branch three ways.

The pass's findings are unchanged by construction: `fact_sites` is not
touched apart from filling one new field, and the three live markers in
this tree all name `git_runner` bindings, which are fact sites and take
neither new branch. `defect.md` records the eight-problem baseline this run
must reproduce byte for byte.

## Components

### `one_owner.FactSite` — one new field

`attach`: the line a contiguous comment block above this definition would
end at. For an assignment, and for an undecorated function, it equals
`lineno`. For a decorated function it is the first decorator's line.

This **supersedes one line** of `docs/fixes/one-fact-one-owner/architecture.md:276`.
That artifact is the record of what was decided then and is not rewritten;
the table there stays as written and this section is the amendment.

### `one_owner.fact_sites` — fills the field, decides nothing

Two construction sites (one_owner.py:182 for `same-value`, :190 for
`same-keys`). The `same-value` site passes `node.lineno` for both fields —
an `ast.Assign` has no `decorator_list`, so there is no second line to
carry, and saying so here is cheaper than a reader looking for the case.

Its return contract, sort order and problem strings are unchanged.

### `one_owner.markers` — walks up from both lines

```python
    for site in sites:
        for start in (site.lineno, site.attach):
            lineno = start - 1
            while lineno in comments:
                owner_of[lineno] = site
                lineno -= 1
```

For an undecorated site the two starts are equal and the second walk is
idempotent. For a decorated one they are the two placements a human might
choose, and both attach. Everything downstream — the grammar check, the
empty-reason check, the `Marker` shape — is untouched.

### `one_owner.defined_names` — new, small, answers one question

Every `<module>.<name>` a module binds, whether or not it states a fact.
This is a *different question* from `fact_sites`', not a second copy of it:
`fact_sites` asks what a module states, `defined_names` asks what it names.

Reach is matched to what can become a fact site, deliberately:

- module-level `ast.Assign` targets — `tree.body` only, because that is the
  only place `fact_sites` looks for `same-value`;
- every `FunctionDef` / `AsyncFunctionDef` and every `ClassDef` — via
  `ast.walk`, because `fact_sites`' `same-keys` walk is `ast.walk` too, so a
  *nested* function can be a fact site and must not read as undefined.

A class is included even though no class is ever a fact site. That is the
point: a marker naming one should hear "states no fact", not "does not
exist".

It returns names only, no problems. A module that will not parse is already
reported by `fact_sites`; `_standalone_comments` sets the precedent of
staying silent for exactly that reason (one_owner.py:262).

### `one_owner._rent` — one branch becomes three

```python
    for marker in marks:
        if marker.counterpart not in defined:        # exists nowhere
        elif marker.counterpart not in stated:       # exists, states no fact
        else:                                        # the group check, as today
```

`stated` is today's set, built from fact sites; `defined` is the new one.
The ADR-citation check below it is untouched.

### `tests/test_one_owner.py` — the pinned shape and the helper

`TestDataModel` (tests/test_one_owner.py:968) pins `FactSite._fields` as
"architecture.md's Data model" and must be updated with the shape, in the
same commit. Its docstring cites this artifact for the amended field. The
`site(...)` helper at :77 gains the parameter.

## Data model

`FactSite` only, amended:

```
FactSite  = (kind, path, lineno, attach, name, identity)
              lineno   1-based, the definition's own line — what a
                       problem string points a reader at
              attach   1-based, where a comment block above this
                       definition ends — the marker join key.
                       == lineno unless the definition is decorated.
```

`Marker` and `Group` are unchanged. There is still no storage, no state
file and no baseline.

## Interfaces & contracts

### `defined_names(path, source) -> set[str]`

- **Input:** repo-relative posix path, module source text.
- **Output:** `{"<module>.<name>", ...}`. Empty set for source that will not
  parse — never an exception, never a problem string.
- **Failure mode:** silence on `SyntaxError`, because `fact_sites` reports
  that module. Two reports of one broken file is noise, and the second one
  arrives from the function least able to explain it.

### `_rent(found_groups, marks, sites, defined, adr_ids) -> list[str]`

- **New parameter** `defined`, positioned before `adr_ids`: the union of
  `defined_names` over every file `check` read.
- **Contract:** for each marker, exactly one of the three counterpart
  branches fires, plus the independent ADR-citation check.
- `_rent` is private; the suite asserts its strings through `check`.

### The new problem string

```
one-owner: {path}:{lineno} names {counterpart}, which is defined but states no fact this pass reads — name the definition that duplicates, or remove the marker
```

Same register as its siblings: what is wrong, then what to do. It replaces
"which is not defined in this repo" *only* for a counterpart that exists;
a counterpart that exists nowhere still gets the old string unchanged.

## Stack & dependencies

Stdlib `ast`, already imported. No new imports, no new module, nothing
mirrored: `one_owner.py` is not in `factory_init.MIRRORS`, so there is no
payload copy, no `update-manifest`, and no manifest conflict added to the
eight open PRs.

## Decisions & alternatives

**D1 — where the attach line lives. Chosen: a new `FactSite` field.**
- *Change `lineno` to the first decorator's line instead.* Rejected:
  `lineno` is what a reader is pointed at by the group report
  (one_owner.py:235) and by both `_coverage` strings (:351, :358). Making it
  the decorator line would print `cli.py:169` beside the name
  `harness_run`, moving the report off the thing it names to fix a join.
- *Compute the attach map inside `markers` with its own AST walk.*
  Rejected: a second walk over the same shape, inside the one module whose
  job is to report exactly that. `fact_sites` already has the tree open.

**D2 — which placements attach. Chosen: both.**
- *Attach only from the first decorator's line.* Rejected: the placement
  between a decorator and its `def` attaches today — it is the workaround
  the seed names — and quietly un-attaching it would turn working carve-outs
  into "marker above no definition". That is the message this run exists to
  stop emitting falsely; emitting it at a new set of authors is not a fix.

**D3 — `min(d.lineno for d in ...)` over `decorator_list[0].lineno`.**
`decorator_list` is source-ordered, so the two are equal. `min` is taken
because it carries its own proof: the reader does not have to know the
ordering guarantee to see that the earliest decorator wins.

**D4 — where "exists at all" comes from. Chosen: a new `defined_names`.**
- *Widen `fact_sites` to return a triple.* Rejected: its `(sites, problems)`
  arity is used at every call site and pinned by the suite; carrying an
  unrelated third answer to save a parse is a worse trade than the parse.
- *A regex over the source.* Rejected: this tool parses, everywhere, and a
  name census that disagrees with the AST in a corner is a diagnostic that
  lies — the class this run is closing.

**D5 — three branches, not two.** A counterpart that exists but states no
fact could have fallen through to the existing group check, which would say
"nothing duplicates it — remove the marker". True, but it withholds the one
fact the author needs: the counterpart is *there*, and the pass cannot see a
fact in it. The three-way split says which of the two situations holds.

## ADRs

None offered — see the frontmatter assumption. ADR-0061 is applied, not
amended: it says a deliberate second owner is recorded with a marker at the
definition it excuses, and this run makes the pass honour such a marker when
the definition is decorated.

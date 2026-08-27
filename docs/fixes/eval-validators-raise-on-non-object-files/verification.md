---
stage: verify
run: maintenance:eval-validators-raise-on-non-object-files
date: 2026-08-27
---

# Verification: the eval validators report instead of raising

Three criteria from `autorun-brief.md`, plus the three work-item
acceptance criteria in `defect.md`. Evidence is quoted output.

## 1. No validator raises for any JSON top-level value

**Criterion:** object, array, string, number, boolean and null all
return problem strings; nothing raises.

Before (from `defect.md`), `validate` raised on `None`/`5`/`True` and
`validate_output` and `fixture_refs` raised on all four probed values.
After:

```
  None         validate=1 validate_output=1 fixture_refs=[]
  5            validate=1 validate_output=1 fixture_refs=[]
  True         validate=1 validate_output=1 fixture_refs=[]
  []           validate=1 validate_output=1 fixture_refs=[]
  'version'    validate=1 validate_output=1 fixture_refs=[]
  ['version']  validate=1 validate_output=1 fixture_refs=[]
```

The regression test drives a wider set than this probe —
`None, 0, 5, True, False, "", "version", [], ["version"], [{"id": "x"}]`
— including the falsy values (`0`, `False`, `""`) that a truthiness-based
guard would have mishandled.

**Pass.**

## 2. The problem names the real defect, not a derived one

**Criterion:** one problem identifying the shape; the 26-problem
coverage cascade is gone.

RED, before the fix — the string case did not raise, which is what made
it the dangerous one:

```
  file="version"   -> 26 problem(s); first: evals/routing.json covers skill 'next' in only 0 case(s), need >= 3
```

After, through the same `eval_schema.load()` entry point on real files:

```
  file=null        -> cases=[] problems=['evals/routing.json is not a JSON object']
  file=5           -> cases=[] problems=['evals/routing.json is not a JSON object']
  file="version"   -> cases=[] problems=['evals/routing.json is not a JSON object']
  file=[]          -> cases=[] problems=['evals/routing.json is not a JSON object']
  file=true        -> cases=[] problems=['evals/routing.json is not a JSON object']
```

`cases=[]` in every row matters independently: `load_case_set` must not
let a caller half-run an invalid set.

**Pass.**

## 3. End to end, through the CI gate itself

**Criterion:** `python3 lint.py` behaves per the repo's problem-string
convention on a corrupted eval file.

`evals/routing.json` replaced with `null`, run in two worktrees — the
unfixed baseline at `main` and this run:

```
===== baseline (622e7c0) =====
  exit code: 1
      if "version" not in data:
         ^^^^^^^^^^^^^^^^^^^^^
  TypeError: argument of type 'NoneType' is not a container or iterable
===== run-evalschema (5268947) =====
  exit code: 1
  LINT: evals/routing.json is not a JSON object
  lint: 1 problem(s) across 24 skills
```

**Pass — and read the exit codes carefully.** Both are `1`. This fix does
**not** turn a green build red; the build was already red. What changes
is that the failure is now reported in the repo's problem-string
vocabulary instead of a stack trace. No false-green case was found in any
probed shape, and none is claimed.

## 4. The loader guarantees validators receive an object

**Criterion:** added mid-run — see `defect.md` Notes. Review found the
same defect in `charter_replay.validate`, and its string case is worse
than the routing one: it returns **no problems at all**, so a bare-string
file reads as a *valid* case set and the crash lands in the loader's
`data.get("cases")`.

RED, driving `load_case_set` with a validator that does not guard shape
(standing in for charter_replay's):

```
    return ([], problems) if problems else (data.get("cases", []), [])
                                            ^^^^^^^^
AttributeError: 'str' object has no attribute 'get'

Ran 3 tests in 0.004s

FAILED (errors=6)
```

GREEN after moving the guard ahead of the `validate` call, and with it
the charter path end to end — through `charter_replay.load_cases`, with
`charter_replay.py` itself unmodified:

```
  null        -> cases=[] problems=['charter/cases.json is not a JSON object']
  5           -> cases=[] problems=['charter/cases.json is not a JSON object']
  "version"   -> cases=[] problems=['charter/cases.json is not a JSON object']
  []          -> cases=[] problems=['charter/cases.json is not a JSON object']
```

A test also pins that the validator is *not invoked* for a non-object, so
"a validator may assume a dict" is a guarantee rather than a convention,
and that a valid object still reaches it unchanged.

**Pass.**

## 5. The battery is green

```
Ran 1352 tests in 15.390s

OK
--- lint ---
lint: 0 problem(s) across 24 skills
--- gates ---
gates: 0 problem(s)
selftest: ok
--- one-owner (pre-pass, not a gate) ---
one-owner: 9 problem(s)
```

1352 is 1344 on `main` plus this run's eight regression tests. one-owner
is 9, the standing baseline — unchanged. `eval_schema.py` is not in
`factory_init.MIRRORS`, so no manifest regeneration was needed;
`gates.py` 0 problems includes detector E, which is what would have
complained had that been wrong.

## Not verified, and why

- **`trigger_eval.py`'s call path was not executed** — it costs real
  model spend and this session never runs it. It reaches the defect
  through `eval_schema.load`, which criteria 1–3 exercise directly, so
  the fix covers it by construction; that is reasoning, not a
  measurement. The charter path is no longer in this category:
  criterion 4 drives `charter_replay.load_cases` for real, which needs no
  model spend because loading a case set is not replaying one.
- **`charter_replay.validate` called *directly* still raises** on
  `None`/number/bool, and still returns zero problems for a string. Only
  the loader path is fixed. That is a deliberate deferral with a reason,
  recorded as finding 2 in `review.md`.
- **No corrupted *output*-eval file was run through `lint.py`.**
  `check_output_evals` walks `evals/output/`, and the unit-level
  evidence for `validate_output` and `fixture_refs` is in criterion 1.
  The end-to-end demonstration covers the routing path only.
- **Nothing about whether this shape has ever actually occurred.** The
  defect is a contract violation reachable from a plausible corruption,
  not an incident being cleaned up. No claim is made that it has bitten
  anyone.

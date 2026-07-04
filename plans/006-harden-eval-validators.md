# Plan 006: Make the eval validators diagnose malformed input instead of crashing

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 79b08fc..HEAD -- eval_schema.py lint.py tests/test_eval_schema.py tests/test_lint_checkers.py`
> If `eval_schema.py` or `lint.py` changed since this plan was written,
> compare the "Current state" excerpts against the live code before
> proceeding; on a mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `79b08fc`, 2026-07-03

## Why this matters

`eval_schema.py` is the tool that *catches* malformed eval files, and `lint.py`
runs it in CI on every push. But three plausible hand-authoring mistakes in
`evals/routing.json` or `evals/output/<slug>.json` make the validators raise an
uncaught exception instead of returning a problem string — so the lint aborts
with a stack trace and a non-`LINT:` non-zero exit, exactly when it should be
telling the author what's wrong. A validator that crashes on bad input has
failed at its one job. This makes every malformed-input path return a clean
diagnostic.

## Current state

Three defects, all confirmed at `79b08fc`:

**(1) A present-but-`null` collection crashes iteration.** `dict.get(k, default)`
returns the default *only when the key is absent* — `{"cases": null}` returns
`None`, and the next comprehension raises `TypeError: 'NoneType' object is not
iterable`.

- `eval_schema.py:104` (routing, via `validate`):
```python
    cases = data.get("cases", [])
    ids = [c.get("id") for c in cases]          # TypeError if cases is None
```
- `eval_schema.py:81` (output, via `validate_output`):
```python
    evals = data.get("evals", [])
    ids = [e.get("id") for e in evals]          # TypeError if evals is None
```
- `lint.py:111-115` — the lint caller iterates the same field a **second** time
  for the fixture-existence stat, independent of `validate_output`:
```python
            + [f"{label} eval {e.get('id')!r} run_fixture "
               f"{e.get('run_fixture')!r} does not exist"
               for e in data.get("evals", [])     # TypeError if evals is None
               if e.get("run_fixture")            # AttributeError if e not a dict
               and not (root / e["run_fixture"]).is_dir()]
```

**(2) A non-object entry crashes `.get`.** If a case/eval list element is a JSON
scalar (e.g. `"cases": ["oops"]`), `c.get(...)`/`e.get(...)` raises
`AttributeError: 'str' object has no attribute 'get'` — in `validate`
(`eval_schema.py:105`), `validate_output` (`eval_schema.py:82,88`), and the lint
caller (`lint.py:114`).

**(3) `sorted()` over a mixed `None`+`str` set crashes.** When ≥2 cases lack an
`id`, the duplicate set contains `None`; if a `str` id is also duplicated,
`sorted()` compares `None < str` and raises `TypeError`. Both dup-id checks:
```python
    # eval_schema.py:87 (validate_output) and :107-108 (validate)
    for i in sorted({i for i in ids if ids.count(i) > 1})
```

The intended contract is set in `load` (`eval_schema.py:131-144`) and the module
docstring: validators **return problem strings**; they never raise. The existing
tests exercise only the absent-key and well-formed cases
(`tests/test_eval_schema.py` — the duplicate-id test at ~`:49-54` uses two
well-formed string ids; the missing-field tests use dicts), so none of these
branches is covered.

**Convention to match**: every problem string is prefixed with `label` and
reads as a flat human sentence — see the existing strings in `validate`
(`eval_schema.py:106-127`). New problems must follow the same
`f"{label} ..."` shape. Tests assert the **exact** string through the public
function (see `tests/test_eval_schema.py` and `tests/test_lint_checkers.py`).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests   | `python3 -m unittest discover tests` | `OK`, exit 0 |
| One module | `python3 -m unittest tests.test_eval_schema` | `OK`, exit 0 |
| Lint    | `python3 lint.py` | `lint: 0 problem(s) across 13 skills`, exit 0 |

## Scope

**In scope**:
- `eval_schema.py` — `validate`, `validate_output`, and a small shared guard
  helper if you add one.
- `lint.py` — only the `check_output_evals` `run_fixture` comprehension
  (`:111-115`).
- `tests/test_eval_schema.py` (add cases), `tests/test_lint_checkers.py` (add
  one case).

**Out of scope** (do NOT touch):
- `results_path`, `valid_results_link`, `load`, `KINDS`, `OUTPUT_FIELDS` — the
  bug is only in the two validators and the one lint loop.
- Any other checker in `lint.py`, `protocol.py`, `trigger_eval.py`.
- The `evals/routing.json` / `evals/output/*.json` data files themselves.

## Git workflow

- Branch: `fix/harden-eval-validators` off `main`.
- Conventional Commits, e.g. `fix: eval validators diagnose malformed input instead of raising`.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Guard the collection reads and non-dict entries in `eval_schema`

In `validate` and `validate_output`, replace the bare `data.get("cases", [])` /
`data.get("evals", [])` with a guarded read that (a) returns `[]` and a problem
when the value is present but not a list, and (b) ignores non-dict entries when
building `ids` and iterating fields, emitting a problem per bad entry. A small
shared helper keeps both validators consistent, e.g.:

```python
def _items(data, key, label):
    """(list-of-dict-entries, problems). Non-list -> [] + one problem;
    non-dict entries are dropped with a problem each, so no .get() ever
    hits a non-dict."""
    raw = data.get(key)
    if raw is None:
        return [], []                      # absent/null: empty, no problem
    if not isinstance(raw, list):
        return [], [f"{label} {key} is not a list"]
    problems = [f"{label} {key} entry #{n} is not an object"
                for n, e in enumerate(raw) if not isinstance(e, dict)]
    return [e for e in raw if isinstance(e, dict)], problems
```

Then `validate` uses `cases, shape = _items(data, "cases", label)` and prepends
`shape` to its returned problems (mirror in `validate_output` with `"evals"`).
Note: absent/`null` returns `[]` with **no** problem — an eval set legitimately
may omit the key, and `validate`'s existing coverage checks already fire on an
empty `cases`. Only a **present non-list** is a problem.

**Verify**: `python3 -m unittest tests.test_eval_schema` → `OK` (existing tests
still pass; behavior for well-formed and absent-key input is unchanged).

### Step 2: Fix the mixed-type duplicate-id sort in both validators

In `validate` (`eval_schema.py:107-108`) and `validate_output`
(`eval_schema.py:87`), make the sort total-order-safe:

```python
    for i in sorted({i for i in ids if ids.count(i) > 1},
                    key=lambda i: (i is None, str(i)))
```

(This keeps `None`-vs-`str` from being compared directly; the existing behavior
for all-string ids is unchanged because `str(i)` preserves their order and the
`(False, ...)` tuple prefix is constant among them.)

**Verify**: `python3 -m unittest tests.test_eval_schema` → `OK`.

### Step 3: Guard the lint caller's second iteration

In `lint.py` `check_output_evals` (`:111-115`), the `run_fixture` comprehension
iterates `data.get("evals", [])` independently and calls `e.get(...)`. Make it
iterate only dict entries of a list so a malformed file reported by
`validate_output` doesn't also crash the stat loop:

```python
            + [f"{label} eval {e.get('id')!r} run_fixture "
               f"{e.get('run_fixture')!r} does not exist"
               for e in (data.get("evals") if isinstance(data.get("evals"), list) else [])
               if isinstance(e, dict) and e.get("run_fixture")
               and not (root / e["run_fixture"]).is_dir()]
```

**Verify**: `python3 lint.py` → `lint: 0 problem(s) across 13 skills`, exit 0
(the real `evals/output/*.json` are well-formed, so output is unchanged).

### Step 4: Add tests and run full gates

See Test plan. Then:

```bash
git add eval_schema.py lint.py tests/test_eval_schema.py tests/test_lint_checkers.py
git commit -m "fix: eval validators diagnose malformed input instead of raising"
```

## Test plan

Add to `tests/test_eval_schema.py` (model after the existing dup-id / missing-field
tests — they call `eval_schema.validate(...)` / `validate_output(...)` and assert
membership/equality on the returned list):

- `validate` with `{"version": 1, "cases": None}` → returns a list containing
  `"<label> cases is not a list"`; **no exception**.
- `validate` with `{"version": 1, "cases": ["oops"]}` → contains
  `"<label> cases entry #0 is not an object"`; no exception.
- `validate` with two id-less cases plus one duplicated string id
  (e.g. `[{}, {}, {"id": "a", ...}, {"id": "a", ...}]`) → returns a list (the
  `"a"` duplicate reported), **no `TypeError`** from the sort.
- `validate_output` with `{"skill_name": "decompose", "evals": None}` →
  contains `"<label> evals is not a list"`; no exception.
- `validate_output` with a scalar entry in `evals` → contains the
  `"evals entry #0 is not an object"` problem; no exception.

Add to `tests/test_lint_checkers.py` (model after the existing
`check_output_evals` fixture-tree test — it writes an `evals/output/<slug>.json`
into a temp root and asserts on the returned problems):

- an output-eval file whose `evals` is `null` → `check_output_evals` returns a
  problem list (from `validate_output`), and **does not raise**.

Verification: `python3 -m unittest discover tests` → all pass, including the new
cases; every new test asserts the function *returns* (never `assertRaises`).

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 -m unittest discover tests` exits 0; the new validator/lint tests exist and pass
- [ ] `python3 lint.py` exits 0 with `lint: 0 problem(s) across 13 skills`
- [ ] `python3 -c "import eval_schema as e; e.validate({'version':1,'cases':None},[],'x'); e.validate_output({'evals':None},'s','x')"` prints nothing and exits 0 (no traceback)
- [ ] `git status --short` shows only the four in-scope files modified

## STOP conditions

Stop and report back (do not improvise) if:

- The excerpts in "Current state" don't match the live `eval_schema.py` /
  `lint.py` (the code drifted — the guard may already exist, or the functions moved).
- Making the guarded read changes the output of `python3 lint.py` on the real
  data files (it should stay `0 problem(s)` — a change means a real eval file is
  now flagged, which is a data problem, not this plan's job).
- A step's verification fails twice after a reasonable fix attempt.

## Maintenance notes

- If a future checker adds a third iteration over `cases`/`evals`, route it
  through the same `_items` guard rather than re-adding a bare `.get(k, [])`.
- The "absent/`null` → no problem" choice is deliberate: an eval set may omit a
  collection; only a present non-list is malformed. A reviewer should confirm
  this matches the coverage-policy intent (an empty `cases` still fails the
  `>= 3 per skill` coverage check in `validate`, so nothing is silently accepted).
- These are pure-function fixes with no side effects — the PR should be small and
  fully covered by the new unit tests.

---
stage: capture
run: maintenance:eval-validators-raise-on-non-object-files
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance is recorded at the head of
  autorun-brief.md"]
---

# Defect: the eval validators raise on a file that is not an object

## Defect

`eval_schema.py` opens its own docstring for `entries()` with the rule
the whole module is meant to keep:

> Validators return problem strings; they never raise.

They do raise. Every validator reaches into `data` assuming it is a
`dict`, but the only thing upstream guarantees is that `json.loads`
succeeded — and JSON's top level is legally an array, string, number,
boolean, or null. A file that parses to any of those either crashes the
validator or, worse, produces a page of confident nonsense.

This is not a hypothetical shape. `evals/routing.json` truncated to
`null` by an interrupted write, or an output-eval file hand-authored as a
bare `[...]` array, both land here.

## Reproduction / Evidence

Direct, against the module's public functions:

```
=== validate() with non-dict JSON payloads ===
  None           -> RAISED TypeError: argument of type 'NoneType' is not a container or iterable
  5              -> RAISED TypeError: argument of type 'int' is not a container or iterable
  True           -> RAISED TypeError: argument of type 'bool' is not a container or iterable
  []             -> 1 problem(s)
  'version'      -> 26 problem(s)
  ['version']    -> 26 problem(s)

=== validate_output() with non-dict JSON payloads ===
  None           -> RAISED TypeError: argument of type 'NoneType' is not a container or iterable
  5              -> RAISED TypeError: argument of type 'int' is not a container or iterable
  []             -> RAISED AttributeError: 'list' object has no attribute 'get'
  'x'            -> RAISED AttributeError: 'str' object has no attribute 'get'

=== fixture_refs() ===
  None           -> RAISED AttributeError: 'NoneType' object has no attribute 'get'
  5              -> RAISED AttributeError: 'int' object has no attribute 'get'
  []             -> RAISED AttributeError: 'list' object has no attribute 'get'
  'x'            -> RAISED AttributeError: 'str' object has no attribute 'get'
```

End to end through the real entry point, `eval_schema.load()`, on an
actual file:

```
  file=null        -> RAISED TypeError: argument of type 'NoneType' is not a container or iterable
  file=5           -> RAISED TypeError: argument of type 'int' is not a container or iterable
  file="version"   -> 26 problem(s); first: evals/routing.json covers skill 'next' in only 0 case(s), need >= 3
```

The last line is the worst of the three. Nothing raised; the lint simply
reported twenty-six coverage failures against a file whose actual defect
is that it is a string. A reader chasing those problems is chasing
artefacts of the bug.

## Root-cause hypothesis

Confirmed by reading, not inferred:

- `validate` (line 189) starts `if "version" not in data`. The `in`
  operator needs a container; on `None`/`int`/`bool` it raises
  `TypeError`. On a `str` it silently becomes a **substring** test, which
  is why `"version"` passes the version check and the run continues into
  meaningless coverage arithmetic.
- `validate_output` (line 172) calls `data.get("skill_name")` directly.
  `entries()` guards its own access, so a list survives that far and
  dies on `.get`.
- `fixture_refs` (line 155) calls `data.get("evals")` with no guard at
  all, though its docstring promises "malformed shapes yield nothing
  rather than raising, mirroring entries".

The common cause is that the dict-ness of `data` is checked nowhere.
`entries()` carefully validates the *collection* under a key and each
entry within it, and that thoroughness one level down is probably why
the missing check one level up went unnoticed.

## Blast radius

Not test-only — these run in CI.

| Caller | Reached via | Effect on a non-object file |
|---|---|---|
| `lint.py:470` `check_evals` | `eval_schema.load` | `python3 lint.py` dies with a traceback instead of printing problems |
| `lint.py:488` `check_output_evals` | `validate_output` | same; the enclosing `try` catches only `JSONDecodeError` |
| `lint.py:490` `check_output_evals` | `fixture_refs` | same |
| `trigger_eval.py:437` | `eval_schema.load` | the routing eval run aborts |
| `charter_replay.py:159` | `load_case_set` | the charter replay aborts |

`lint.py` is a required CI check, so the failure mode is a red build
whose output is a Python traceback rather than the problem strings the
repo's whole checker convention exists to produce. No file in
`factory_init.MIRRORS` is touched by the fix, so no manifest
regeneration — verified against `factory_init.MIRRORS` directly.

## Ruled out

- **A caller-side fix — rejected.** `lint.py` could wrap each call in a
  type check, and `charter_replay.py` and `trigger_eval.py` could too.
  That is three copies of one rule, in exactly the shape this repo has a
  pre-pass to complain about, and it leaves the module's stated contract
  false. The guard belongs with the contract.
- **`entries()` already covers it — false.** `entries()` validates
  `data[key]`, not `data`. On a list it returns `([], [])` because
  `"evals" not in []` is legitimately `True`, so it reports nothing and
  lets the caller proceed to `.get`.
- **The str case is harmless — false.** It is the only case that
  produces no error at all, and it is therefore the one most likely to
  waste a reader's time. It is treated as part of the defect, not a
  curiosity.

## Work items

- [x] **One object guard, owned by the module** — add the check that
  `data` is a JSON object, and route `validate`, `validate_output` and
  `fixture_refs` through it.
  - Accept: each returns a single problem (or `[]` for `fixture_refs`)
    for every non-object payload — `None`, number, bool, string, array —
    with no exception, pinned by a regression test that fails first.
- [x] **The problem names the real defect** — a non-object file yields
  one problem identifying it as such, not derived coverage complaints.
  - Accept: `validate("version", ...)` returns exactly one problem, and
    it names the file's shape; the previous 26-problem cascade is gone.
- [x] **Battery green** — the repo's full verification set.
  - Accept: `python3 -m unittest discover tests` OK, `python3 lint.py` 0
    problems, `python3 gates.py` 0 problems and `--selftest` ok, quoted
    in `verification.md`.

## Notes

- 2026-08-27: `results_path` validates its `harness` argument only when
  `kind == "trigger"`; for `charter` and `output` an unknown harness is
  silently ignored. Logged, not fixed — it is a separate defect with no
  evidenced caller, and folding it in would widen a scoped run.

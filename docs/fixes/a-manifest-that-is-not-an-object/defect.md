---
stage: capture
run: maintenance:a-manifest-that-is-not-an-object
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance — including the earlier beads memory
  that recorded the finding — is at the head of autorun-brief.md"]
---

# Defect: a manifest that is not an object

## Defect

Both manifest readers catch a parse failure and then assume the parsed
value is a dict:

```python
# lint.py:22
def check_manifest(root):
    ...
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return [f"plugin.json is not valid JSON: {err}"]
    return [f"plugin.json missing field: {field}"
            for field in ("name", "description", "version")
            if not data.get(field)]
```

```python
# lint.py:35
def check_pi_package(root):
    """... Guarded like check_manifest so the dual-target packaging
    can't silently drift."""
    ...
    if data.get("private") is not True:
```

A JSON document's top level is legally an array, string, number, boolean
or null. `json.loads` returns each of them untouched, and none of them
has `.get`.

## Why it matters

`lint.main` walks `CHECKERS` with no exception handling:

```python
problems = [p for checker in CHECKERS for p in checker(root)]
```

`check_manifest` and `check_pi_package` are the **first two** entries in
that tuple. So the failure is not "one checker reports nothing" — it is
the whole lint gate dying before any other checker runs, hiding every
other problem in the repo behind a traceback. `python3 lint.py` is one
of the three commands CI runs on every push.

The irony is recorded in the code itself: `check_pi_package`'s docstring
says it is "guarded like check_manifest", and what it faithfully
reproduced was the gap. It even knows the idiom — it guards `pi` with
`isinstance(pi, dict)` one level down. Only the top level is taken on
trust.

## Reproduction

Five legal JSON documents, neither of them an object, through both
readers:

```
$ python3 -c "
import tempfile
from pathlib import Path
import lint
for shape in ('null', '42', '\"text\"', '[\"a\"]', 'true'):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp); (root / '.claude-plugin').mkdir()
        (root / '.claude-plugin' / 'plugin.json').write_text(shape)
        (root / 'package.json').write_text(shape)
        for fn in (lint.check_manifest, lint.check_pi_package):
            try:
                print(f'  {shape:8} {fn.__name__:18} -> {fn(root)}')
            except Exception as err:
                print(f'  {shape:8} {fn.__name__:18} -> RAISES'
                      f' {type(err).__name__}: {err}')
"
  null     check_manifest     -> RAISES AttributeError: 'NoneType' object has no attribute 'get'
  null     check_pi_package   -> RAISES AttributeError: 'NoneType' object has no attribute 'get'
  42       check_manifest     -> RAISES AttributeError: 'int' object has no attribute 'get'
  42       check_pi_package   -> RAISES AttributeError: 'int' object has no attribute 'get'
  "text"   check_manifest     -> RAISES AttributeError: 'str' object has no attribute 'get'
  "text"   check_pi_package   -> RAISES AttributeError: 'str' object has no attribute 'get'
  ["a"]    check_manifest     -> RAISES AttributeError: 'list' object has no attribute 'get'
  ["a"]    check_pi_package   -> RAISES AttributeError: 'list' object has no attribute 'get'
  true     check_manifest     -> RAISES AttributeError: 'bool' object has no attribute 'get'
  true     check_pi_package   -> RAISES AttributeError: 'bool' object has no attribute 'get'
```

Ten for ten.

## Why the tests did not catch it

`tests/test_lint.py` covers a missing file and unparseable bytes for
both readers, and a missing field for each — the two states either side
of this one. `TestPiPackage`'s own docstring repeats the claim the code
makes: "guarded like the Claude one so the dual-target packaging can't
silently drift". No test parses a file to a non-object.

## A third instance, not fixed here

`check_output_evals` (lint.py:512) parses `evals/output/*.json` and hands
the value to `eval_schema.validate_output` and `eval_schema.fixture_refs`:

```
$ python3 -c "
import tempfile
from pathlib import Path
import lint
for shape in ('null', '\"text\"', '[\"a\"]'):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'evals' / 'output').mkdir(parents=True)
        (root / 'evals' / 'output' / 'next.json').write_text(shape)
        try:
            print(f'  {shape:8} -> {lint.check_output_evals(root)}')
        except Exception as err:
            print(f'  {shape:8} -> RAISES {type(err).__name__}: {err}')
"
  null     -> RAISES TypeError: argument of type 'NoneType' is not a container or iterable
  "text"   -> RAISES AttributeError: 'str' object has no attribute 'get'
  ["a"]    -> RAISES AttributeError: 'list' object has no attribute 'get'
```

Same symptom, different owner: the raise happens inside `eval_schema`,
whose validators own what a validator may assume about its input. The
fix belongs there, and one already exists on the unmerged branch
`agent/eval-validators-raise-on-non-object-files`. Guarding it at lint's
call site instead would add the third copy of the rule that this run
exists to stop at two. Left open, deliberately.

## Breakdown

- [x] The top-level shape is checked once and applied by both readers.
      Acceptance: a test asserts each of the five non-object shapes
      yields exactly one problem naming the shape, for both readers.
- [x] The lint gate survives a non-object manifest. Acceptance: a test
      walks every entry in `CHECKERS` over a tree whose `plugin.json` is
      `null` and asserts none raises, so the other findings still
      report.
- [x] The existing behaviour is unchanged. Acceptance: the clean-tree
      test and every missing-field/invalid-JSON test still pass
      untouched.
- [x] Full battery green.

## Notes

2026-08-27 — the guard is a named function with two callers rather than
two inline `isinstance` checks. Two inline checks would fix the symptom
and leave the cause: `check_pi_package` was written to match
`check_manifest` and copied its gap, and its test class repeated the
claim. Giving the two readers one thing to copy is the fix for that.

2026-08-27 — the helper is named `object_problems`, matching the
function of the same name on the unmerged branch
`agent/eval-validators-raise-on-non-object-files`. That is deliberate:
if both ever land, the duplication is obvious at the name rather than
hidden behind two spellings of one rule, and `lint.py` already imports
`eval_schema`, so collapsing them is a one-line change. It is NOT an
import today — that function is not on `main`, and a branch may not
depend on an unmerged one.

2026-08-27 — scope was corrected mid-run. The brief first claimed no
other checker read a JSON top level this way; `check_output_evals` does,
and raises. The claim was wrong, the brief was corrected in place, and
the finding is recorded above as open rather than quietly folded in.

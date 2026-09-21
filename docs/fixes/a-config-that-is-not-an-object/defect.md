---
stage: capture
run: maintenance:a-config-that-is-not-an-object
date: 2026-08-30
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the defect was
  found by a live audit of the modules no open PR claimed, and the
  reproduction below is that audit's own transcript"]
---

# Defect: a config that is not an object

## Defect

`factory_config.load` guards the parse and then hands the parsed value
straight to callers:

```python
# factory_config.py:72
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as err:
        rel = path.relative_to(root).as_posix()
        return None, [f"config: {rel} is not valid JSON: {err}"]
```

A JSON document's top level is legally an array, string, number, boolean
or null. `json.loads` returns every one of them untouched, and none of
them has `.get`. Every accessor in the module — `resolve_model`,
`resolve_budget`, `resolve_cap`, `config_problems` — opens with
`config.get(...)`.

The `null` case is the sharpest: the seam answers `(None, [])`. That is
**no problem at all**, so a caller that checks `if problems:` proceeds
with `config = None` and raises one line later.

Detector F does not use `load` — it parses each candidate home itself —
but it repeats the same omission and then subscripts the result:

```python
# gates.py:895
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            problems.append(f"F: {rel} is not valid JSON: {err}")
            continue
        budgets = config.get("budgets_usd")
```

## Why it matters

`factory_config` states its own contract in its module docstring:

> Conventions match gates.py: functions return (value, problems) with
> `config:`-prefixed problem strings; a field the config does not cover
> is a problem, never a silent default.

The seam promises a problem string and delivers a traceback.

The reachable surface is the whole factory. `factory_config.load` has
five runtime callers — `assembler`, `budget_guard`, `dashboard`,
`cost_report` and `work_queue` — and detector F is one of the three
commands CI runs on every push. In a **stamped product repo**
`.github/factory.json` is the repo's own curated file, exactly like the
`.github/labels.json` that detector J was recently taught to report
(#376). So the gate whose entire job is policing this file's shape is
the thing a malformed file takes down.

`cost_report.guard` is documented to FAIL CLOSED — "a report that cannot
prove it is under the cap is treated as over it". A traceback is not a
closed failure; it is no verdict at all.

## Reproduction

Against the seam and both of its readers, on `main`:

```
$ python3 -c "... factory_config.load(root) for each non-object shape"
  null   load->None  resolve_cap-> RAISED AttributeError: 'NoneType' object has no attribute 'get'
  []     load->[]    resolve_cap-> RAISED AttributeError: 'list' object has no attribute 'get'
  5      load->5     resolve_cap-> RAISED AttributeError: 'int' object has no attribute 'get'
  "x"    load->'x'   resolve_cap-> RAISED AttributeError: 'str' object has no attribute 'get'
  true   load->True  resolve_cap-> RAISED AttributeError: 'bool' object has no attribute 'get'
```

Through the real entry points:

```
null  gates.check_config_shape   -> RAISED AttributeError: 'NoneType' object has no attribute 'get'
null  cost_report.guard          -> RAISED AttributeError: 'NoneType' object has no attribute 'get'
null  work_queue.plan_batch      -> RAISED AttributeError: 'NoneType' object has no attribute 'get'
```

And end to end, through the CI command itself, on a checkout of `main`:

```
$ echo 'null' > factory/templates/factory.json
$ python3 gates.py
  File ".../gates.py", line 903, in check_config_shape
    budgets = config.get("budgets_usd")
              ^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'get'
```

## Why the tests did not catch it

`TestLoad` covers a missing file and invalid JSON — the two ways a read
can fail *before* `json.loads` returns. Nothing covered a read that
succeeds and returns the wrong kind of thing. Detector F's tests all
write objects.

## The same class, four times

This is the fourth instance of one defect class in this repo, and the
first with no owner:

| where | status |
|---|---|
| `lint.check_manifest` / `check_pi_package` | fixed, PR #394 |
| `eval_schema` validators | fixed, PR #398 |
| `charter_replay.validate` | fixed via `load_case_set`, PR #398 |
| **`factory_config.load` + detector F** | **this run** |

The pattern is always the same: a reader catches `JSONDecodeError` and
then trusts the value. Recorded as a seed rather than a detector,
because a detector for it is a real design question, not a one-liner.

## Notes

Found while auditing the module surface that no open PR claimed.
`factory_config.py` is touched by PRs #391 and #396, but neither
addresses the object rule: #391 catches `OSError`/`UnicodeDecodeError`
around the read, #396 rejects a non-finite cap. Contention with both is
recorded in the PR body.

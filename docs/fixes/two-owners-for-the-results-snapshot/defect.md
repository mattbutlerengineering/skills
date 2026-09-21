---
stage: capture
run: maintenance:two-owners-for-the-results-snapshot
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance is recorded at the head of
  autorun-brief.md"]
---

# Defect: the results snapshot has two owners

## Defect

`trigger_eval.py:385` and `charter_replay.py:413` define the same
function twice.

```python
# trigger_eval.py:385
def record(output, results_dir):
    """Write a dated results file; eval_schema owns the naming grammar."""
    results_dir.mkdir(parents=True, exist_ok=True)
    path = eval_schema.results_path(results_dir, "trigger", output["date"],
                                    harness=output.get("harness"))
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return path
```

```python
# charter_replay.py:413
def record(output, results_dir):
    """Write a dated snapshot; eval_schema owns the append-only naming."""
    results_dir.mkdir(parents=True, exist_ok=True)
    path = eval_schema.results_path(results_dir, "charter", output["date"])
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return path
```

Four decisions are stated twice: that the directory is created with
parents, that the name comes from `eval_schema.results_path`, that the
payload is serialised as `json.dumps(..., indent=2)` with a trailing
newline in utf-8, and that the written path is returned. Only the kind
string and the `harness` keyword genuinely differ.

Both docstrings name `eval_schema` as the owner of the naming half. The
writing half has no owner, and so acquired two.

## Why it matters

`evals/results/` is append-only and is the evidence base the LEDGER
graduates maturity against. The two writers are the only two producers
in that tree.

## Failure scenario

A change to how a snapshot serialises — `sort_keys=True` for stable
diffs, dropping the trailing newline, switching indentation — is applied
to the writer the author had open. `evals/results/` then holds trigger
snapshots in one format and charter snapshots in another, with no
reconciliation available because the tree is never rewritten. Nothing
fails loudly: both files parse, both validate, and the divergence is
discovered only by someone diffing across kinds.

The same shape has already been paid for elsewhere in this repo:
ADR-0041's dedup identity acquired a second owner in `budget_guard`
(PR #341), and the labels-array walk acquired one in `plane_drift`
(PR #335). This is that class, in the eval tools.

## Evidence

`eval_schema` is the declared seam for eval knowledge (ADR-0022,
ADR-0024) and already owns the results naming grammar it is asked for
above:

```
$ grep -n "def results_path" eval_schema.py
49:def results_path(results_dir, kind, date, slug=None, harness=None):
```

Both modules already import it, so routing the write through it adds no
dependency:

```
$ grep -n "^import eval_schema" trigger_eval.py charter_replay.py
trigger_eval.py:9:import eval_schema
charter_replay.py:11:import eval_schema
```

## Breakdown

- [x] `eval_schema` grows the snapshot writer, covering directory
      creation, naming, serialisation and the returned path, with the
      kind and optional harness supplied by the caller. Acceptance: a
      new test in `tests/test_eval_schema.py` writes a snapshot through
      it and asserts the exact bytes on disk and the returned path.
- [x] `trigger_eval.record` routes through it. Acceptance: the existing
      trigger recording tests pass unchanged — the observable output is
      byte-identical.
- [x] `charter_replay.record` routes through it. Acceptance: the
      existing charter recording tests pass unchanged.
- [x] Full battery green, and `one_owner.py` reports no new problem.

## Notes

2026-08-27 — the writer is `eval_schema.write_snapshot`. It takes the
kind from the caller and refuses the directory-shaped `output` kind,
which `results_path` will otherwise happily name. `slug` was dropped
from the signature during implementation: no snapshot kind uses it, and
a parameter whose only reachable use is to be refused is worse than its
absence.

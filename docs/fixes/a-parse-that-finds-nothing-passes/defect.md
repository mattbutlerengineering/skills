---
stage: capture
run: maintenance:a-parse-that-finds-nothing-passes
date: 2026-08-30
re-entry: implement
intake: #417
assumptions:
  - "The fix is scoped to TestSweepsWorkflow.commands() and not generalised into a repo-wide meta-test. A static sweep found 51 test loops over a derived collection with no non-empty guard; ten of the underlying collections were emptied empirically and all but this one are pinned by something. A lint rule over the other 50 would be noise, and the evidence for that claim is tabulated below rather than asserted."
  - "The guard is an assertion inside the helper rather than at each call site. Two tests loop over commands() today; putting the claim in one place is this repo's stated preference (one_owner.py, ADR-0061) and covers the next caller. The consequence — the sibling's own assertTrue(jobs) becomes a second owner and is removed — is recorded in review.md, not smuggled."
  - "`jobs:` gaining a trailing comment is used as the demonstration edit. It is not a prediction that someone will make that edit; it is the cheapest reachable input that empties the parse, and it is used because a defect argued from a hypothetical is weaker than one argued from a command you can run."
---

# Defect: a workflow parse that finds nothing turns its test green

Filed as intake issue #417 on 2026-08-30.

## Defect

`tests/test_sweeps.py::TestSweepsWorkflow.test_every_sweep_job_ensures_the_labels`
holds its only assertion inside a loop:

```python
def test_every_sweep_job_ensures_the_labels(self):
    for job, commands in self.commands().items():
        self.assertIn("sweeps.py ensure-labels", commands, job)
```

`commands()` hand-parses `.github/workflows/sweeps.yml` — correctly so;
this repo is stdlib-only and there is no PyYAML to reach for. But a
hand-rolled parse matches the file's **shape**, not its meaning, and when
the shape drifts it returns `{}` rather than raising:

```python
if line.rstrip() == "jobs:":
    in_jobs = True
```

With `{}`, the loop body never executes, no assertion runs, and the test
reports OK.

## Reproduction

Against `main`, in-process, with the real workflow:

```
real commands() jobs: ['label-drift', 'reconcile', 'sentry']
after `jobs:  # the four sweeps` -> {}
test_every_sweep_job_ensures_the_labels with NO job ensuring labels: PASSES (vacuous)
whole class: ran=8 failures=1 errors=0
   still caught by: test_the_triage_labels_are_ensured_before_any_sweep_runs
```

The second step strips **every** `sweeps.py ensure-labels` step from the
workflow — precisely the condition the test forbids — and the test still
passes. A trailing comment on `jobs:` is valid YAML and changes nothing
about what the workflow does.

## Why it matters

The sibling test states the stake in its own comment: `gh issue create
--label X` aborts on a label that does not exist, so a sweep that runs
before the taxonomy exists **files nothing at all** — including the
label-drift sweep's own report that the taxonomy is missing. A silent
sweep and a clean sweep look identical from outside. The test that
forbids that ordering was the one that stopped checking.

## Scope: what is not wrong

A static sweep flagged 51 candidate loops. Emptying the underlying
collection and re-running the owning suite separates the reachable holes
from the noise:

| emptied | result |
| --- | --- |
| `sweeps.TRIAGE` | caught (36 failures/errors) |
| `factory_roles.ROLES` | caught (7) |
| `factory.VERBS` | caught (5) |
| `factory_init.MIRRORS` | caught (14) |
| `gates.CHECKERS` | caught (1) |
| `human_gates.GATES` | caught (10) |
| `golden_cases()` | caught (1) |
| `lint.CHECKERS` | caught (4, full suite) |
| `charter_files()` | unguarded, but unreachable — always contains `CHARTERS_INDEX` |
| **`TestSweepsWorkflow.commands()`** | **unguarded and reachable** |

`lint.CHECKERS` is worth naming explicitly: scoped to `tests/test_lint.py`
alone it looks vacuous, and only the full suite catches an unwired
checker. That is a false positive corrected by widening the experiment,
and it is why the table reports full-suite runs.

## Work items

1. `commands()` fails instead of returning `{}`. **Accept:** a workflow
   whose `jobs:` line the parse does not recognise raises
   `self.failureException`, not an empty dict.
2. A regression test for the compounded failure — parse drift *and* a
   missing `ensure-labels` step — which was green before. **Accept:** the
   test fails when the guard is reverted.
3. The sibling's call-site `assertTrue(jobs)` is removed, the claim now
   having one owner. **Accept:** `python3 one_owner.py` reports nothing new.

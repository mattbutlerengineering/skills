---
stage: ship
run: maintenance:a-permission-drop-nothing-fails-on
date: 2026-08-30
assumptions:
  - "The run stops at 'PR open'. Merge is ADR-0033 gate 3, a human decision; an agent-authored PR merging itself is what that gate exists to prevent. #419 closes on merge via the commit trailer."
  - "The first push of this branch carried a red battery and was amended rather than followed up, because the branch had no PR and no reviewer yet. What went wrong is recorded below rather than erased with it."
---

# Release: a permission drop nothing fails on

## What shipped

- Branch `agent/a-permission-drop-nothing-fails-on`
- **PR #420**, open against `main`
- Intake **#419**, closed on merge by the `Closes #419` trailer

One new file, `tests/test_workflow_permissions.py`, plus this run's four
artifacts. No workflow, tool, or payload file changed — so no
`update-manifest` in the commit and no detector E interaction.

## State at hand-off

```
$ python3 -m unittest discover tests 2>&1 | tail -3
Ran 1348 tests in 17.091s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

Merge: **not done** — human gate.

## What went wrong in this run

The first commit was pushed with a red battery. The artifacts were
written and committed without re-running the gates afterwards, and
detector H caught what the run had not:

```
H: docs/fixes/a-permission-drop-nothing-fails-on/verification.md:1 verification
   artifact shows neither literal evidence nor a NOT-RUN disclaimer
   (evidence must be a fenced code block)
```

verification.md stated its results in tables and named no literal
command output — which is precisely the artifact shape detector H exists
to reject, in a run whose entire subject is a check that was not
actually checking. The fix was to paste the real output. The commit was
amended, not followed up, because the branch had no PR and no reviewer
at that moment.

The lesson is narrow and worth keeping: **the battery has to run after
the artifacts are written, not just after the code is.** In this repo
docs are gated too.

## Seeds

- Two workflow jobs are now covered twice: `sweeps.yml`'s grant by both
  its own `test_it_can_write_issues_and_only_read_code` and this table,
  and `toolsmith-mine.yml`'s `pull-requests: read` by both
  `tests/test_rejection_mining.py:304` and this table. Both older tests
  carry context this table does not (#297's story, the read-vs-write
  distinction), so neither was removed. If a third overlap appears, the
  older per-tool assertions are the ones to retire.
- The rejected derivation is written out in defect.md. If `make` recipes
  ever stop carrying verbs — one target per verb — the derivation
  becomes viable and the table could be generated instead of recorded.

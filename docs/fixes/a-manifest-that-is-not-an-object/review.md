---
stage: review
run: maintenance:a-manifest-that-is-not-an-object
date: 2026-08-27
assumptions: []
---

# Review: a manifest that is not an object

Scope: `lint.py` (+29/-1) and `tests/test_lint.py` (+31). `lint.py` is
not in `factory_init.MIRRORS`, so there is no payload copy and no
manifest to regenerate.

Written by the same agent that wrote the change, so ADR-0036 clause 2 is
unsatisfied.

## Correctness

**Checked, not a finding — the guard reports alone and returns early.**
On a string, `data.get("keywords")` cannot be asked at all, so there is
no second complaint to collect; returning the shape problem by itself is
the only honest answer. Both readers return rather than accumulate, and
the tests pin the exact single-element list.

**Checked, not a finding — `bool` needs no special case here.** Unlike a
dollar amount, where `True` passing for `1` is the whole hazard, a
boolean top level simply is not an object and is named as one. The test
matrix includes `true` for that reason.

**Checked, not a finding — no existing behaviour moved.** The clean
tree, both missing-file paths, both unparseable-JSON paths and all four
field checks are untouched and green. The guard sits strictly between
"parsed" and "read a field".

**Open, not fixed here — `check_output_evals` has the same symptom from
a different owner.** It hands its parsed value to
`eval_schema.validate_output` and `eval_schema.fixture_refs`, which
raise on a non-object (TypeError on `null`, AttributeError on a string
or list — reproduction in `defect.md`). The guard belongs to
`eval_schema`, whose validators own what a validator may assume, and a
complete fix already exists on the unmerged, PR-less branch
`agent/eval-validators-raise-on-non-object-files`. Guarding it at lint's
call site would be the third copy of the rule this run exists to stop at
two. Left open on purpose, and named here so it is not mistaken for an
oversight.

**Major, accepted with its cost — this run creates a future duplicate.**
If that branch lands, `lint.object_problems` and
`eval_schema.object_problems` state the same rule in two modules, which
is exactly what `one_owner.py` exists to catch. Accepted because the
alternative is worse: a branch may not import a function that is not on
`main`, and leaving `lint.py` crashing until an unrelated branch is
merged is not a smaller cost. The names are deliberately identical so
the collapse is a one-line change, and `lint.py` already imports
`eval_schema`, so the import direction is already established.

## Design

One function, two callers, in the file that has both. No new module —
the shared-module bar (multiple real callers AND observed divergence)
is about modules, and this is a helper beside the two functions that
use it. The docstring carries why the shape cannot be assumed and why
the problem is reported alone, because the next reader will otherwise
take the guard for defensive padding and inline it away.

## Security

No new input surface. The change makes a CI gate report on malformed
input instead of aborting on it, which is a small availability
improvement for the gate: previously a single bad manifest hid every
other lint finding in the repo behind a traceback.

## Verdict

No critical findings. One major accepted with its cost stated, one open
finding recorded with its owner. The blocking condition on shipping is
ADR-0036 clause 2.

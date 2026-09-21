---
run: maintenance:the-failing-run-posts-no-report
date: 2026-08-27
---

# Autorun brief

**Scale.** Maintenance run, `re-entry: implement` — a located defect with
a reproduction, not a design question.

**What and why.** The weekly cost report + monthly circuit breaker
(ADR-0034) is split across a compute half (`cost_report.py`, offline and
unit-tested) and a mutate half (`.github/workflows/cost-report.yml`,
which posts the report issue and flips `FACTORY_PAUSED`). The compute
half deliberately composes a report even on its fail-closed paths. The
workflow's posting step inherits an implicit `success()` gate and throws
that report away on exactly those paths.

**Scope, in.** The posting step's gate in the root workflow and its
byte-identical payload mirror; the manifest checksum that pins them; a
test in `tests/test_cost_report.py` covering every step that reads the
report step's outputs.

**Scope, out.** `cost_report.py` itself (the compute half is correct —
it is the workflow that discards its work). `FACTORY_PAUSE_TOKEN`
provisioning. The `CONTINUE` constant `one_owner.py` reports as shared
between `budget_guard.py` and `cost_report.py` — pre-existing, and a
one-owner finding is a question for a human, not a gate.

**Success criteria.** A fail-closed verdict posts its report issue; a
crash before the outputs are written does not ask `gh` to create an empty
issue; every consuming step's gate is stated rather than inherited; the
battery stays green and the payload mirror stays byte-identical to root.

**Constraints.** Stdlib only. The workflow is mirrored verbatim, so both
copies change together and `factory_init.py update-manifest` runs.

**Release authorization.** None given. Ship prepares and stops.

**Tracker.** No issue interaction — read-only `gh` only.

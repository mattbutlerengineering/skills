---
stage: review
run: maintenance:the-failing-run-posts-no-report
date: 2026-08-27
assumptions: []
---

# Review: the failing run posts no report

## What was examined

The run's whole diff: four lines of `if:` in each of the two workflow
copies, one manifest checksum, and one new helper plus one new test class
in `tests/test_cost_report.py`. Read alongside `cost_report.py`'s
compute/mutate boundary, the pause and resume steps whose gates this one
now matches, `TestFailClosedPause` and `TestWorkflowOutputLockstep` (the
two classes that should have caught it), and `workflow_parse.run_steps`,
whose block-end rule `step_block` reuses.

## Findings

### Critical

None.

### Major

**`always()` widens when the step runs, and the title guard is what
bounds it.** The step now also runs after a report step that failed for a
reason that is *not* a fail-closed verdict — a syntax error, a missing
import, a runner that died. In those cases no outputs were written, so
`steps.report.outputs.title` is the empty string and the condition is
false. The guard is not decoration: without it, `gh issue create --title
""` would fail and replace a legible Python traceback with a gh error
about an empty title. `TestMain::test_a_fail_closed_verdict_writes_pause_
before_the_failing_exit` already pins the ordering the guard depends on —
outputs are written before the failing exit — so the two tests hold the
property from both ends.

**The pin is over every consumer, not over one more named step.** The
defect was a gate stated by *omission*, and a test naming the third step
would have left a fourth step free to repeat it. `test_every_step_reading
_the_report_outputs_states_its_gate` subTests over whatever steps
reference `steps.report.outputs.`, and
`test_the_three_consumers_are_the_ones_this_pin_covers` names today's
three so the coverage is legible rather than implied. A step added later
joins the pin without anyone remembering to extend it.

### Minor

**`step_block` is a fourth stdlib workflow-text reader in the suite.**
`workflow_parse.run_steps`, `test_design_pipeline.on_block`,
`TestWorkflowOutputLockstep.REFS` and now this one each read workflow YAML
their own way. That is the repo's stated position — no YAML parser,
stdlib only — and `step_block` reuses `run_steps`' block-end rule rather
than inventing a third one, which is the part that could have drifted.
Whether these four should become one shared reader is a `one_owner`-shaped
question about `tests/`, and `one_owner.py`'s `EXCLUDED` tuple
structurally cannot see inside `tests/`. **Deferred**, owner: whoever
takes the `tests/` blind spot; not this run's diff to widen.

**The other five free workflows were not audited for the same shape.**
Said plainly in `verification.md`'s "Not verified" rather than left to
read as covered. `cost-report.yml` was examined because its compute half
advertises a fail-closed path; the others may or may not have consumers
gated by omission. No action here — an unexamined file is not a finding.

**The fix is unverifiable offline.** GitHub evaluates `if:`, so this run
can prove the file's text and the reasoning, not the scheduling. The
mitigation is that the construction is not novel: the pause step three
lines below has shipped the identical `always() && <output condition>`
form since WO-0033. No action; recorded so the next reader does not
mistake a green battery for a proven runtime behaviour.

## Process findings

**ADR-0036 clause 2 is not satisfied.** A non-authoring reviewer must
re-execute the verification and record it on the pull request. This
review is self-authored, so the branch is deliberately **held out of the
merge queue** — no PR is opened, nothing is merged.

**One `one_owner` finding names a file this run touched — and it is
pre-existing.** `budget_guard.py:55 CONTINUE and cost_report.py:44
CONTINUE`. `cost_report.py` is not in this diff; the finding is on
`origin/main` and stays there. Stated rather than filtered out of the
evidence.

**`factory/manifest.json` is the one contended file in the diff.** Nearly
every open PR touches it, because every payload edit must. It is
generated, so a conflict resolves by re-running `python3 factory_init.py
update-manifest` on the merged tree, never by hand-editing a checksum.

## Fix / defer decisions

| Finding | Severity | Decision |
| --- | --- | --- |
| `always()` widens the step; title guard bounds it | major | intended; both ends pinned by test |
| Pin covers every consumer, not one named step | major | intended — omission was the failure mode |
| A fourth workflow-text reader in the suite | minor | deferred — `tests/` is `one_owner`'s blind spot |
| Five other workflows unaudited | minor | recorded in "Not verified"; no action |
| Offline verification cannot prove scheduling | minor | recorded; construction already in production |
| ADR-0036 clause 2 unsatisfied | process | branch held out of the queue |

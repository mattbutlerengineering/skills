# Evals

Two eval kinds live here, per [ADR-0019](../docs/adr/0019-trigger-and-output-evals.md).
Both cost real model runs and run on demand — CI never invokes them.

## Layout

- [`routing.json`](routing.json) — the trigger-eval set of routing cases,
  run by [`trigger_eval.py`](../trigger_eval.py) with all eleven skill
  descriptions installed at once, detecting which fires. The case shape
  (`{id, kind, expected, query}`), kind vocabulary, and coverage policy are
  owned by [`eval_schema.py`](../eval_schema.py) (ADR-0022); lint and the
  runner both validate through it.
- [`output/`](output/) — per-skill output-eval sets; graded via the documented
  subagent procedure in [`docs/output-evals.md`](../docs/output-evals.md).
- [`fixtures/`](fixtures/) — eval fixtures: seed docs trees copied into a
  scratch project so upstream artifacts pre-answer what a stage skill would
  otherwise interview for.
- [`results/`](results/) — dated, append-only run records: trigger runs as
  `trigger-<date>[-N].json`, output gradings under `output/<slug>-<date>[-N]/`;
  `-2`, `-3`… suffixes distinguish same-day runs.
  LEDGER.md links these as evidence.

## Honesty policy

- Results files are snapshots pinned to a model and CLI version — dated,
  append-only, never rewritten. A new run gets a new file.
- A failing trigger case gets one 5-run rerun (`--only <id>
  --runs-per-query 5`) before being treated as real; sampling noise at three
  runs is common.
- Never edit an eval definition to make a failing case pass. Fix the skill,
  or record the failure. Eval definitions change only when an expectation
  proves ambiguous or non-discriminating — say so in the commit message.
- Evals inform description and skill quality but never graduate LEDGER
  maturity: a skill graduates past draft only via a real run
  (ADR-0012, ADR-0019).

## Known limitation

Trigger evals install descriptions as command files — a proxy for installed
plugin skills, not the thing itself. Before over-trusting a run's absolute
numbers, spot-check a few queries against the actually-installed plugin;
treat the confusion matrix (which skill fired instead) as the more portable
signal.

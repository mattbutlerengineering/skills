# Evals

Two eval kinds live here, per [ADR-0019](../docs/adr/0019-trigger-and-output-evals.md).
Both cost real model runs and run on demand — CI never invokes them.

## Layout

- [`routing.json`](routing.json) — the trigger-eval set of routing cases,
  run by [`trigger_eval.py`](../trigger_eval.py) with every skill
  description installed at once, detecting which fires. The case shape
  (`{id, kind, expected, query}`), kind vocabulary, and coverage policy are
  owned by [`eval_schema.py`](../eval_schema.py) (ADR-0022); lint and the
  runner both validate through it.
- [`output/`](output/) — per-skill output-eval sets; graded via the documented
  subagent procedure in [`docs/output-evals.md`](../docs/output-evals.md).
- [`fixtures/`](fixtures/) — eval fixtures: seed docs trees copied into a
  scratch project so upstream artifacts pre-answer what a stage skill would
  otherwise interview for.
- [`results/`](results/) — dated, append-only run records: trigger runs as
  `trigger-<date>[-N].json` (claude harness, the default) or
  `trigger-omp-<date>[-N].json` (`--harness omp`, ADR-0031), output gradings
  under `output/<slug>-<date>[-N]/`, and charter-regression replays
  (`charter_replay.py`) as `charter-<date>[-N].json`; `-2`, `-3`… suffixes
  distinguish same-day runs. LEDGER.md links the trigger and output records
  as evidence (maturity stays keyed to claude runs; omp snapshots are
  supplementary harness evidence); charter replays are factory evidence,
  never LEDGER evidence.

## Plugin evals (not in this directory)

A third harness, `claude plugin eval` (Claude Code v2.1.269+), keeps its
suite in [`plugin-evals/`](../plugin-evals/) (ADR-0081). It measures what
the plugin adds: each case runs with the plugin and again without it, and
the report gives `WITH`, `W/OUT` and their difference, `Δ`. Run it on
demand from the repo root:

```
claude plugin eval . --scaffold --model claude-sonnet-5 \
  --judge-model claude-haiku-4-5 --max-cost-usd 15 --no-publish \
  --allow-tools Write Edit "Bash(python3 *)" "Bash(git *)"
```

Add `--tag lean`, `--tag next` or `--tag implement` to run one suite.
The CLI defaults to this directory, `evals/`. `.claude-plugin/plugin.json`
points it at `plugin-evals/` instead (`experimental.evals`), so a bare run
cannot write timestamp directories into `results/` here, whose names
`eval_schema.py` owns. Run output goes to gitignored
`plugin-evals/results/`. A run that is cited anywhere has its
`aggregate-result.json` copied unedited to
`plugin-evals/records/<YYYY-MM-DD>[-N].json`, which is append-only under
the policy below. A partial run (the cost ceiling hit, exit 2) or a run
with skipped judge graders is never cited.

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
  (ADR-0012, ADR-0019). That holds for plugin-eval records too: one may
  be cited beside a skill's LEDGER row only as the figures its committed
  file holds (ADR-0081).

## Known limitation

Trigger evals install descriptions as command files — a proxy for installed
plugin skills, not the thing itself. Before over-trusting a run's absolute
numbers, spot-check a few queries against the actually-installed plugin;
treat the confusion matrix (which skill fired instead) as the more portable
signal.

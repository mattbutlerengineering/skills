# Evals: routing discrimination + on-demand output grading

- Status: accepted
- Date: 2026-07-01

Two eval kinds, both defined under `evals/`. **Trigger (routing) evals**
install all eleven skill descriptions simultaneously and detect *which* one
fires for a query — cross-skill discrimination, not one description in
isolation, because adjacent pipeline stages are the real confusion risk.
The runner (`trigger_eval.py`) is self-contained stdlib Python derived from
the skill-creator plugin's Apache-2.0 code (see NOTICE); results are dated,
append-only JSON under `evals/results/`, pinned to a model. **Output evals**
(`evals/output/<slug>.json`) seed a fixture run directory, pre-supply
interview answers, and grade the produced artifact against objective
expectations via the documented subagent workflow in
`docs/output-evals.md` — on demand only, no always-on gate.

Evals inform description and skill quality but never graduate LEDGER
maturity. This extends ADR-0012, which stands: a skill graduates past draft
only via a real run.

# Skill maturity ledger

Maturity vocabulary: **draft** (written, never exercised) → **used-once**
(exercised in at least one real run) → **battle-tested** (exercised across
multiple runs; rough edges worn off). Evidence is one line naming the run(s)
that justify the maturity. A skill graduates past draft only via a real run —
never by review.

Trigger-eval results inform description quality but never graduate maturity
(see ADR-0019). Counts are routing cases passed, from the linked recorded run.

| Skill | Maturity | Evidence | Trigger eval |
|-------|----------|----------|--------------|
| next | draft | — | 4/5 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| idea | draft | — | 3/3 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| prd | draft | — | 4/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| ux-design | draft | — | 3/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| architect | draft | — | 3/3 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| decompose | draft | — | 3/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| implement | draft | — | 2/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| verify | draft | — | 2/3 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| review | draft | — | 1/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| ship | draft | — | 2/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| operate | draft | — | 2/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |

Reading of the 2026-07-01 run: all failures are under-triggering (no skill
fired); zero cases fired the wrong skill. Distractors 5/5 stayed silent.

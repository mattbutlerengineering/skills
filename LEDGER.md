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
| implement | draft | — | 3/4 — [2026-07-01](evals/results/trigger-2026-07-01-2.json) |
| verify | draft | — | 2/3 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| review | draft | — | 3/4 — [2026-07-01](evals/results/trigger-2026-07-01-3.json) |
| ship | draft | — | 2/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| operate | draft | — | 2/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| address-pr-review | draft | — | 0/4 — [2026-07-03](evals/results/trigger-2026-07-03.json), reruns [2026-07-03-9](evals/results/trigger-2026-07-03-9.json)–[12](evals/results/trigger-2026-07-03-12.json) |
| autorun | draft | — | 1/3 — [2026-07-03](evals/results/trigger-2026-07-03-2.json), reruns [2026-07-03-13](evals/results/trigger-2026-07-03-13.json)–[14](evals/results/trigger-2026-07-03-14.json) |
| mermaid | draft | — | 1/3 — [2026-07-03](evals/results/trigger-2026-07-03-3.json), mermaid-3 passed rerun [2026-07-03-17](evals/results/trigger-2026-07-03-17.json) |

Reading of the 2026-07-01 run: all failures are under-triggering (no skill
fired); zero cases fired the wrong skill. Distractors 5/5 stayed silent.

Reading of the 2026-07-03 utility-skill run (15 cases, all failures
confirmed by 5-run reruns): address-pr-review never fired — its cases
either stayed silent or misfired to review (apr-2 fired review 3/5 on
rerun). autorun and mermaid mostly under-trigger. The anticipated
near-misses against watch/next/docs held (apr-vs-watch-1,
autorun-vs-next-1, mermaid-vs-docs-1 all passed), but review-vs-apr-1 and
mermaid-vs-ux-1 under-triggered (expected skill stayed silent).

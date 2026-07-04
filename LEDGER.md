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
| idea | draft | — | 3/3 — [2026-07-01](evals/results/trigger-2026-07-01.json); capture-vs-idea-1 under-triggered on [2026-07-03-42](evals/results/trigger-2026-07-03-42.json), confirmed by rerun [-50](evals/results/trigger-2026-07-03-50.json) |
| prd | draft | — | 4/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| ux-design | draft | — | 3/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| architect | draft | — | 3/3 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| decompose | draft | — | 3/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| implement | draft | — | 4/6 — [2026-07-03-39](evals/results/trigger-2026-07-03-39.json), maintenance cases included; decomp-vs-impl-1 recovered on its 5-run rerun ([-45](evals/results/trigger-2026-07-03-45.json)), capture-vs-implement-1 confirmed failing ([-46](evals/results/trigger-2026-07-03-46.json)) |
| verify | draft | — | 5/5 — [2026-07-03-40](evals/results/trigger-2026-07-03-40.json), maintenance cases included |
| review | draft | — | 3/4 — [2026-07-01](evals/results/trigger-2026-07-01-3.json) |
| ship | draft | — | 2/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| operate | draft | — | 2/5 — [2026-07-03-41](evals/results/trigger-2026-07-03-41.json), maintenance case included; operate-situational-1 recovered on its 5-run rerun ([-47](evals/results/trigger-2026-07-03-47.json)), ship-vs-operate-1 and operate-maint-1 confirmed failing ([-48](evals/results/trigger-2026-07-03-48.json), [-49](evals/results/trigger-2026-07-03-49.json)) |
| capture | draft | — | 2/4 — [2026-07-03-38](evals/results/trigger-2026-07-03-38.json); capture-2 and impl-vs-capture-1 confirmed failing by 5-run reruns ([-43](evals/results/trigger-2026-07-03-43.json), [-44](evals/results/trigger-2026-07-03-44.json)) |
| address-pr-review | draft | — | 3/4 — [2026-07-03-36](evals/results/trigger-2026-07-03-36.json), after detection fix; earlier 0/4 ([2026-07-03](evals/results/trigger-2026-07-03.json), reruns [-9](evals/results/trigger-2026-07-03-9.json)–[-12](evals/results/trigger-2026-07-03-12.json)) was misattribution |
| autorun | draft | — | 0/3 — [2026-07-03-29](evals/results/trigger-2026-07-03-29.json), after description rewrite; autorun-3 wobbles (passed [-2](evals/results/trigger-2026-07-03-2.json), 1/3 in [-29](evals/results/trigger-2026-07-03-29.json)) |
| mermaid | draft | — | 0/3 — [2026-07-03-30](evals/results/trigger-2026-07-03-30.json), after description rewrite; mermaid-3 wobbles (2/3 in [-22](evals/results/trigger-2026-07-03-22.json), 1/3 in [-30](evals/results/trigger-2026-07-03-30.json)) |

Reading of the 2026-07-01 run: all failures are under-triggering (no skill
fired); zero cases fired the wrong skill. Distractors 5/5 stayed silent.

Reading of the 2026-07-03 utility-skill run (15 cases, all failures
confirmed by 5-run reruns): address-pr-review never fired — its cases
either stayed silent or misfired to review (apr-2 fired review 3/5 on
rerun). autorun and mermaid mostly under-trigger. The anticipated
near-misses against watch/next/docs held (apr-vs-watch-1,
autorun-vs-next-1, mermaid-vs-docs-1 all passed), but review-vs-apr-1 and
mermaid-vs-ux-1 under-triggered (expected skill stayed silent).

Reading of the 2026-07-03 description-fix follow-up (snapshots [-20]
through [-37]): the "address-pr-review misfired to review" signal was a
detection bug, not a routing failure — review-skill-<id> is a substring
of address-pr-review-skill-<id> and _match_slug returned the first
substring hit, so every apr fire was misattributed to review. With the
fix (longest name first, covered by TestSubstringShadowing), apr scores
3/4; only the terse apr-vs-review-1 still under-triggers. Two rounds of
description rewrites (trigger vocabulary from the failing queries, a
consult-first mandate for mermaid, an apr disclaimer on review) did not
materially move autorun (0/3) or mermaid (0/3, mermaid-3 borderline):
their failures are structural to the harness — the claude -p model
answers simple or conversational queries directly instead of consulting
a command, matching the skill-creator plugin's documented
simple-task under-triggering. review's rates after gaining the
disclaimer are within its pre-change variance (review-direct-2 has
never passed; verify-vs-review-1 bounced on 2026-07-01 too).

Reading of the 2026-07-03 maintenance-surface run (snapshots [-38]
through [-50], claude-sonnet-5): the maintenance vocabulary in the
implement and verify descriptions carries — verify went 5/5 (including
verify-maint-1 and the impl-vs-verify-1 near-miss) and implement-maint-1
passed, so queries that name a defect brief, re-entry, or a regression
test route correctly. Every failure is under-triggering; nothing
misfired. The cases that stayed silent through their 5-run reruns share
a shape: bug-report or outcome phrasings that name no artifact
(capture-2, impl-vs-capture-1, capture-vs-idea-1, ship-vs-operate-1,
operate-maint-1) — the claude -p model just answers or starts fixing,
the same structural simple-task under-triggering documented above.
operate remains the weakest surface: ship-vs-operate-1 has never fired,
and operate-maint-1 stayed silent even while naming the retro.

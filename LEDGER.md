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
| next | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 4/5 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| idea | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 3/3 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| prd | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 4/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| ux-design | draft | — | 3/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| architect | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 3/3 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| decompose | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 3/4 — [2026-07-01](evals/results/trigger-2026-07-01.json) |
| implement | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 3/4 — [2026-07-01](evals/results/trigger-2026-07-01-2.json) |
| verify | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 2/3 — [2026-07-05](evals/results/trigger-2026-07-05-11.json) (unchanged from [2026-07-01](evals/results/trigger-2026-07-01.json)) |
| review | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 2/5 — [2026-07-05](evals/results/trigger-2026-07-05-3.json), review-situational-1 2/5 on rerun [2026-07-05-13](evals/results/trigger-2026-07-05-13.json) |
| ship | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 3/4 — [2026-07-05](evals/results/trigger-2026-07-05-9.json) (was 2/4 — [2026-07-01](evals/results/trigger-2026-07-01.json)) |
| operate | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 2/4 — [2026-07-05](evals/results/trigger-2026-07-05-14.json), first widening [2026-07-05-10](evals/results/trigger-2026-07-05-10.json), direct-2 rerun [2026-07-05-12](evals/results/trigger-2026-07-05-12.json) |
| capture | draft | — | — |
| address-pr-review | draft | — | 3/4 — [2026-07-05](evals/results/trigger-2026-07-05.json), apr-vs-watch-1 held [2026-07-05-2](evals/results/trigger-2026-07-05-2.json) (prior 0/4 was a detection artifact — see reading) |
| autorun | draft | — | 0/4 — [2026-07-05](evals/results/trigger-2026-07-05-4.json), autorun-vs-next-1 held [2026-07-05-5](evals/results/trigger-2026-07-05-5.json) (was 1/3 — [2026-07-03](evals/results/trigger-2026-07-03-2.json)) |
| mermaid | draft | — | 1/3 — [2026-07-05](evals/results/trigger-2026-07-05-6.json), mermaid-vs-docs-1 held [2026-07-05-8](evals/results/trigger-2026-07-05-8.json), mermaid-vs-ux-1 silent [2026-07-05-7](evals/results/trigger-2026-07-05-7.json) |
| factory-init | draft | — | — |
| doctor | draft | — | — |
| interactive-architecture-diagram | draft | — | — |
| animated-diagram | draft | — | — |
| architecture-diagram | draft | — | — |
| work-queue | draft | — | — |
| audit | draft | — | — |
| deepen | draft | — | — |

Reading of the 2026-07-01 run: all failures are under-triggering (no skill
fired); zero cases fired the wrong skill. Distractors 5/5 stayed silent.

Reading of the 2026-07-03 utility-skill run (15 cases, all failures
confirmed by 5-run reruns): address-pr-review never fired — its cases
either stayed silent or misfired to review (apr-2 fired review 3/5 on
rerun). autorun and mermaid mostly under-trigger. The anticipated
near-misses against watch/next/docs held (apr-vs-watch-1,
autorun-vs-next-1, mermaid-vs-docs-1 all passed), but review-vs-apr-1 and
mermaid-vs-ux-1 under-triggered (expected skill stayed silent).

Correction to the 2026-07-03 reading (diagnosed in PR #83): the
address-pr-review 0/4 and its "misfired to review" cases were a
measurement artifact, not a routing failure — trigger_eval's slug
detection took the first substring hit, and review-skill-<id> is a
substring of address-pr-review-skill-<id>, so every genuine apr fire
was recorded as review. With longest-match detection and the sharpened
apr/review disambiguation, apr scores 3/4 (only the terse near-miss
apr-vs-review-1 stays silent, 0/3).

Reading of the 2026-07-05 run (detection fix + description changes for
apr/review/ship/operate; verify, autorun, mermaid descriptions
untouched): ship's colloquial widening flipped impl-vs-ship-1 (2/3;
was 0/5) for 3/4, though ship-situational-1 stays under (1/3).
operate's widening flipped operate-situational-1 (3/3 then 4/5; was
0/5) but the first draft demoted the retro vocabulary and
operate-direct-2 slipped (1/3, 2/5 rerun); restoring the retro-first
opening with the post-launch phrasings appended kept situational-1
passing while direct-2 still bounced 2/5 — net 2/4, composition
improved, and ship-vs-operate-1 moved from pure silence to 2/5.
verify unchanged at 2/3 (verify-direct-2 the same bouncy failure).
review reads 2/5 on its now-larger case set, within historical bounce:
review-direct-2 and review-vs-apr-1 have never passed, and
review-situational-1 failed 1/3 pre-change on 2026-07-01 too. autorun
(0/4) and mermaid (1/3) were deliberately not re-worded: PR #83 burned
two recorded iterations on the available angles (unattended/hands-off
phrasing; concrete diagram-type nouns) with no improvement — their
under-triggering is structural to the claude -p harness, which answers
simple or brief-handoff queries directly instead of consulting a
skill. Further description roulette would overfit the eval; whether
such queries should be expected to fire at all is an ADR-worthy
calibration question.

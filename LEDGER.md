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
| next | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 5/7 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| idea | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 4/5 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| prd | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 4/4 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| ux-design | draft | — | 6/7 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| architect | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 4/4 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| decompose | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 5/5 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| implement | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 4/6 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| verify | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 3/3 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| review | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 7/8 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| ship | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 5/5 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| operate | used-once | feature:seed-backlog dogfood run (issue #7), closed 2026-07-06 | 4/4 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| capture | draft | — | 3/4 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| autorun | draft | — | 3/5 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| factory-init | draft | — | 3/4 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| doctor | draft | — | 7/7 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| animated-diagram | draft | — | 3/4 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| pipeline-board | draft | — | 3/3 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| assembly-line | draft | — | — |
| conduct | draft | — | — |
| audit | draft | — | 10/11 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| deepen | draft | — | 6/8 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| automate | draft | — | 5/6 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| launch-demo | draft | — | 3/3 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| lean | draft | — | 8/8 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| polish | draft | — | 10/10 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| house-voice | draft | — | — |
| knowledge-base | draft | — | 7/8 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| ux-writing | draft | — | 9/9 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| ux-patterns | draft | — | 8/8 — [2026-10-10](evals/results/trigger-2026-10-10-3.json) |
| prisma-migrations | draft | — | — |
| implement-queue | draft | — | — |

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

Reading of the 2026-10-10 full run ([2026-10-10-3](evals/results/trigger-2026-10-10-3.json),
185 cases across every skill then shipped, 163 passed): it is now the
cited run for every row it covers, so some counts read lower than their
July runs on larger case sets (idea 4/5, implement 4/6). autorun reads
3/5 on the same `claude -p` harness, so the July note that its
under-triggering is structural to that harness no longer holds as
stated.

# Hybrid recall policy for skill descriptions

- Status: accepted
- Date: 2026-07-01

The 2026-07-01 trigger eval showed perfect cross-skill discrimination (no
case ever fired the wrong skill) but under-triggering on terse action
imperatives — Claude answers "do a code review of the changes" directly
instead of invoking the skill. The failures concentrated in `review` and
`implement`.

Policy: **one evidence-driven recall pass where the evidence points, then
stop.** A description may gain action-verb phrasings only for queries a
recorded eval run shows failing, each change is kept only if a rerun of the
affected cases measurably improves them (and regresses none of the
adjacent-stage or distractor guards), and the rerun is committed as a new
dated results file. Refining a variant within the pass is allowed when the
rerun shows a mixed result — the 2026-07-01 pass did this once for `review`,
whose first variant traded direct-ask recall for quality-check recall; the
kept variant recovers most of that (and still leaves `review-direct-2`
failing) — but every variant's rerun is recorded, and the pass still ends.
"Measurably improves" is judged per skill across its cases, not per case:
a kept change may trade a fraction on one case for large gains on others,
as long as the trade is visible in the committed results. After that pass,
residual under-triggering on terse imperatives is accepted as platform
behaviour — descriptions are never tuned merely to move eval numbers, and
`ship`/`verify`/`operate`'s failing phrasings stay as recorded, accepted
failures.

This is the description-side complement to the eval-side honesty policy
(evals/README.md): evals don't bend toward descriptions, and descriptions
bend toward evals exactly once, on evidence, in the open.

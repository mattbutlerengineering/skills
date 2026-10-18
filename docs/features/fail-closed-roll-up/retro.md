---
stage: operate
run: feature:fail-closed-roll-up
date: 2026-10-17
users-observed: 1
signal-source: "repo history and CI: one person, the Owner, whose autorun session wrote the only verification.md committed after #998 merged that the rule judges (docs/fixes/a-quoted-date-dodges-the-cutoff/verification.md, 7e4a19a). No stamped repo has the rule: the chore(release) PR is not cut and the installed 0.20.0 plugin cache has no ROLLUP_ADOPTED."
assumptions:
  - "Let it breathe: the release is about 13 hours old. The protocol gives the brief's operate section the decision whether the stage runs, and its minimum-signal (the first post-merge verification.md the new rule judges) is met, counted from the repo below. So the retro is written now, not deferred."
  - "Population counted as people, not agents or artifacts. The Owner counts once: autorun sessions the Owner started wrote both post-cutoff artifacts. Whether an autorun-written artifact counts as use by the Owner is a reading, recorded here. Read strictly, no one outside the pipeline has used the rule, and that is the honest summary: the whole population is the Owner plus one autorun-authored artifact."
---

# Retro: Fail-closed roll-up for verification Summaries

#998 squash-merged as `461803a` at 2026-10-17T08:59:16-07:00. This retro
was written about 13 hours later, once the brief's minimum-signal was met.
Every count below comes from the repo, CI or the forge, and never from
the brief.

## Outcomes vs. intent

### Minimum signal: the first post-merge verification.md the rule judges

- What happened: exactly one such file exists, and the rule **applied to
  it and passed it, with nothing to fire on**. That file is
  `docs/fixes/a-quoted-date-dodges-the-cutoff/verification.md`. It was
  written in `7e4a19a` at 09:39 -07:00, 40 minutes after the merge, and
  reached main in `96af7c9` (#1002) at 10:13. Its `date:` is
  `2026-10-17`, which is not before `ROLLUP_ADOPTED`, so the rule judges
  it. It has 11 labelled verdicts and 0 labelled disclosures, so the
  trigger (a criterion disclosed NOT RUN) never armed. The pass is true
  but vacuous. The detector's public functions, run on the file at HEAD
  and at `461803a`'s `gates.py` (exported into the scratchpad with
  `git archive`), give the same answer:
  ```
  rollup applies: True
  evidence_problems: []
  rollup_problems: []
  summary names_unknown: [True]
  labelled verdicts: 11
  labelled disclosures: 0
  unclosed: None
  ```
  No other post-merge verification.md exists. `git log --all
  --since=2026-10-17T15:59:16Z -- '*verification.md'` lists only
  `7e4a19a` and `96af7c9` for this file, plus `461803a` itself (this
  run's own verification.md). No verification.md in any worktree or
  scratchpad was modified after the merge. Across all 92 tracked
  `verification.md` files, the rule applies to two: this run's own and
  the one above. Both have 0 disclosures and 0 problems.
- Signal strength: anecdote (n = 1, and its author is this pipeline: the
  run's own review seed started the maintenance run that wrote it).

### Success in one sentence: a full-pass Summary over a disclosed NOT RUN fails `gates.py`, and no pre-cutoff artifact does

- What happened: the second half holds on the real tree. `python3
  gates.py` printed `gates: 0 problem(s)` (exit 0) on `3f35cb0`, with no
  shipped artifact edited. The first half has never been tested by a
  real author: **the rule has never fired on a real artifact.** Every
  CI run created since the merge passed or was skipped (`gh run list
  --created ">=2026-10-17T15:59:00Z"`: `validator success: 42`,
  `assembler skipped: 5`, and `--status failure` gives `0`). Those runs
  cover #1000, #1002, #1004, #1006 and #1008, the only PRs since. None
  is open now, and none was refused. The rule fires only on fixtures:
  the `TestEvidenceRollUp` tests and the selftest's `rolledup` defect.
- Signal strength: measured for "no false positive on the real tree";
  unobserved for "refuses a dishonest Summary".

### The rule as a floor: does it hold for template-shaped Summaries? (found at Operate)

- What happened: **no.** The verify template asks the Summary to count
  its NOT RUN items, and both judged artifacts write the count as
  "0 NOT RUN". That zero count is itself a vocabulary hit
  (`names_unknown: True`), so it satisfies the rule permanently. If a
  criterion later turns to NOT RUN and the Summary is not updated, the
  stale-Summary drift the rule exists to catch passes. Probe on the
  judged file, with criterion 9's `- Result: PASS` (line 278) flipped to
  `- Result: NOT RUN — probe` in memory:
  ```
  probe A (summary unchanged, '0 NOT RUN'):  []
  probe B (summary without the NOT RUN count):  [(13, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass')]
  ```
  ADR-0107 accepts the negation dodge ("nothing was skipped"), and a
  zero count belongs to the same class. This shape is different,
  though: the rule's own template produces it, it is in 2 of the 2
  artifacts the rule judges, and the `gates.py` comment's premise ("A
  count carries its word … so naming covers counting") fails exactly
  at zero.
- Signal strength: measured (a probe, not use).

### Reach: stamped repos get the rule on their next update

- What happened: not yet reached. `.claude-plugin/plugin.json` reads
  `0.20.0`. Its last change is `5a58fe4` (`chore(release): plugin 0.20.0
  for the consumer round-2 wave (#976)`, 2026-10-16), from before #998.
  The installed cache at `idea-to-prod/0.20.0` has no `ROLLUP_ADOPTED`
  anywhere, and its verify template has no roll-up wording. Stamped
  repos observed: 0.
- Signal strength: unobserved.

## Open debt

Issues this run itself filed — Review deferrals, Verify carry-forwards —
are the run's debt, never feedback (the protocol's "The Operate
population" section says which issues are the run's own).

- #997: the run's own `type:feature` issue, closed by #998. Nothing is
  outstanding on it.
- #1001 / #1002: the O and M quoted-date dodge, which this run's review
  fix loop seeded at `docs/backlog.md` line 123. It was fixed and merged
  the same day through one shared `gates._grandfathered`. That is the
  run's own debt, paid. It is not feedback.
- The review's 7 deferred minors are recorded in `review.md`, not filed
  as issues: invisible or incidental words satisfy the rule; heading
  variants escape it; the disclosure heads are stated twice in
  `gates.py`; no test pins that a Summary's own disclosure is not a
  trigger; the `n't run` and hyphen widening satisfies on incidental
  prose; "couldn't be run" and "1 not-applicable" still false-positive;
  the trailing-comment `date:` is unpinned. Some of them are seeded
  below.
- ADR-0107 is still `provisional` (`docs/adr/README.md` line 130). The
  Owner accepts or amends it, and the zero-count finding above bears on
  that.
- The ADR-0095 `chore(release)` PR is not cut, so the payload has not
  shipped (above).
- The launch brief: Ship's `launch_demo.py config` printed `SHIP`, and
  the brief was never produced.

## Run retrospective

- Keep: Idea measured the target failure and reported **zero**. The PRD
  then named the run as prevention instead of inflating the problem.
  Review's probe-plus-mutation method found two real majors (the
  quoted-date dodge and the honest-wording false positives) before
  merge, and both were fixed with tests seen failing first.
- Keep: the brief's operate minimum-signal ("counted from the repo,
  never from this brief") gave this stage a concrete, checkable bar
  instead of a calendar wait.
- Change: the fix loop fixed the date dodge in H only and seeded O and
  M. A second autorun had to redo the same fix through a shared helper
  40 minutes later and amend ADR-0107 again. When a review finding names
  a pattern that already has several owners, fix it at the shared
  owner in the same loop.
- Change: the review probed many dishonest Summaries but never the one
  the template itself produces ("N PASS, 0 FAIL, 0 NOT RUN" over a
  disclosed criterion). Probe the template's own example output against
  the rule.
- Stop: writing "prepared" then merging within minutes in the same
  session. It cost a separate write-back PR (#1000) for a release the
  Owner authorized live.

## Environment

One row per mistake the run recorded, naming what in the environment
would have caught it; a retro without this section reads as no
environment findings, not as a defect.

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| A quoted, empty or non-ISO `date:` grandfathered a post-cutoff Summary | `review.md` §Major: a quoted, empty or non-ISO `date:` | mechanical | `gates._grandfathered` plus `tests/test_gates.py` (done in #1002); the `gates_selftest.py` dodge row, seeded at `docs/backlog.md` line 124 |
| `SUMMARY_UNKNOWN_TERM` missed the slashless `NA` head that `DISCLOSURE_VERDICT` accepts | `review.md` §Major: the Summary vocabulary missed the slashless `NA` | mechanical | one shared heads alternation in `gates.py`; `one_owner.py` cannot see a duplicate inside one module (`review.md` §Minor: the disclosure heads are stated twice) |
| Mutation M6 (count the Summary's own disclosure) survived the suite | `review.md` §Minor: no test pins that a Summary's own labelled disclosure is not a trigger | mechanical | a `TestEvidenceRollUp` case in `tests/test_gates.py` |
| A zero count ("0 NOT RUN") in the Summary satisfies the rule over a disclosed criterion | this retro, §The rule as a floor (probe A) | mechanical | `gates._rollup_problems` plus a `TestEvidenceRollUp` case; an ADR succeeding ADR-0107 |
| Honest gap phrasings failed the gate ("could not be run", "1 not applicable") | `review.md` §Major: honest gap phrasings outside the vocabulary | judgement | ADR-0107's own rule, which widens the vocabulary on evidence and never by fit |
| The stale local `main` ref made `git diff --stat main` list files this run never touched | `breakdown.md` Notes (deviation, environment); `verification.md` assumptions | mechanical | the verify skill's base-ref step, diffing against `origin/main` or the merge base |
| Two docs overstated what the gate refuses | `review.md` §Minor: two docs overstate what the gate does | judgement | a `CLAUDE.md`-level reading rule; closed in the fix loop |

Guardrail baseline: the repo's four checks run in CI on every push and
PR (the `validator` workflow, 42 successes since the merge), so the
baseline is a guardrail, not its absence.

## Idea seeds

- A Summary's zero count ("0 NOT RUN") satisfies detector H's roll-up
  over a criterion disclosed NOT RUN. Teach the rule that a zero count
  does not name a disclosed criterion, and record it in an ADR
  succeeding ADR-0107.
- One shared disclosure-heads alternation for `DISCLOSURE_VERDICT` and
  `SUMMARY_UNKNOWN_TERM` in `gates.py`. The two copies already drifted
  once.
- Tighten `SUMMARY_UNKNOWN_TERM`'s contracted `n't run` branch so it no
  longer matches "doesn't run on drafts", and accept "couldn't be run"
  and "1 not-applicable".
- Measure the rule in a stamped repo after the next `chore(release)`:
  the first post-cutoff `verification.md` a consumer writes that the rule
  judges.

## Run complete

Closed 2026-10-17. Seeds above are the input to the next Idea-stage run.

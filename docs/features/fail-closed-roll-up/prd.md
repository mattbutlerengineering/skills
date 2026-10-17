---
stage: prd
run: feature:fail-closed-roll-up
date: 2026-10-17
ux: not-applicable
ux-reason: "Docs, two skill templates and one gate rule; no screens or flows."
assumptions:
  - "Interview answered from autorun-brief.md and idea.md in this directory; no live interview held. Every answer below traces to the brief's five Owner decisions, its sections marked as the orchestrator's reading, or idea.md's measured findings."
  - "No typed id is assigned: the prd skill and its template do not assign one, and the run's most recent feature PRD (pr-body-preflight) carries none."
---

# PRD: Fail-closed roll-up for verification Summaries

## Problem statement

People read a `verification.md` by its `## Summary`. The Owner reads it
at a merge gate. Ship's pre-flight asks it whether verification "has no
unresolved failures". Review reads it, and so do the merge train and the
hourly improvement routine. A Summary can read as "all criteria pass"
while a criterion further down says the check was never run. Detector H
makes each criterion section carry its own evidence or its own NOT-RUN
disclosure. No rule states, and no gate checks, that the Summary must
not roll a disclosed NOT RUN, skipped or unknown up into a pass. The
repo also has no shared words for what kind of claim a line makes, so
"pass" can cover an observed result and an unexamined one alike.

**The observed count is zero.** idea.md counted all 77 tracked
`verification.md` files (method and output there, run 2026-10-17 at
`207054d`). No Summary today reads as an unqualified pass over a
criterion that disclosed NOT RUN. All three files with labelled
disclosures count them in the Summary ("0 of 7 met, … 7 unmet",
"2 NOT YET VERIFIABLE", "1 DEFERRED"). The case is prevention. Since
2026-10-15, scheduled routines write and read these artifacts with no
Owner in the loop, and the habit that has kept Summaries honest so far
belongs to the authors, not to any rule.

## Solution

When this ships:

- `CONTEXT.md` names four claim kinds (observed, derived, inferred,
  unknown) and states the roll-up rule: **unknown, unsupported,
  truncated and skipped never aggregate to pass.**
- `docs/pipeline-protocol.md` states the rule once and points to
  `CONTEXT.md` for the vocabulary.
- The verify template's `## Summary` guidance and the review template's
  `## Verdict` guidance (and each skill's SKILL.md where it describes
  writing that line) say the line counts or names its NOT RUN / unknown
  items and never reads as an unqualified pass over them.
- `python3 gates.py` refuses a `verification.md` dated on or after a
  cutoff when a criterion section carries a **labelled** NOT-RUN
  disclosure (a verdict that `gates._is_disclosure` accepts) and the
  Summary neither counts nor names it. The rule keys on labelled
  disclosures only. idea.md showed that H's prose `not_run` flag also
  fires on prose that is not a disclosed criterion. It lit up 10 such
  candidates, so keying on it would false-positive on day one.
- Artifacts dated before the cutoff are grandfathered. None is
  rewritten.
- An ADR records the rule and the cutoff, marked provisional because it
  was written unattended.

## Actors

- **Verify author**: the agent or person writing a `verification.md`,
  more and more often an unattended routine.
- **Review author**: the agent or person writing a `review.md` verdict.
- **Owner**: reads Summaries at merge gates and decides merges.
- **Ship pre-flight**: the Ship stage reading verification for
  unresolved failures before release.
- **Unattended routines**: the merge train and the hourly improvement
  routine, which read and produce artifacts with no Owner present.
- **Stamped-repo maintainer**: a repo that received `gates.py` through
  the factory payload and gets the new rule on its next update.

## User stories

1. As an **Owner**, I want a verification Summary that reads as a pass
   to mean every criterion passed or was counted as not run, so that I
   can merge from the Summary without re-reading every section.
2. As a **Verify author**, I want the template and `gates.py` to tell me
   when my Summary hides a NOT-RUN criterion, so that I fix it before
   commit rather than at review.
3. As a **Ship pre-flight**, I want a Summary that names its NOT-RUN
   count, so that "no unresolved failures" cannot quietly include
   unexamined criteria.
4. As an **unattended routine**, I want the rule enforced by the gate,
   not by an author's habit, so that the guarantee holds when no one
   reads the whole file.
5. As a **Review author**, I want the review template to state the same
   roll-up rule for the `## Verdict`, so that review verdicts follow it
   even though no gate checks them.
6. As a **stamped-repo maintainer**, I want the rule to leave my
   existing, pre-cutoff artifacts alone, so that updating the payload
   does not turn my tree red.

## Success criteria

- [ ] A fixture `verification.md` dated on or after the cutoff, with one
      criterion carrying a labelled NOT-RUN disclosure and a Summary that
      reads as a full pass, makes `python3 gates.py` report an `H:`
      problem. A test asserts the exact problem string through the
      public interface.
- [ ] The same fixture passes once its Summary counts or names the
      NOT-RUN item. So does a fixture with no disclosed criterion.
- [ ] The three honest shapes already on main pass under the rule when
      re-dated past the cutoff in a test fixture: "7 unmet",
      "2 NOT YET VERIFIABLE", "1 DEFERRED".
- [ ] A fixture whose criterion section only mentions "not run" in prose,
      with no labelled disclosure verdict, does not trigger the rule.
- [ ] The failing fixture, dated before the cutoff, passes.
- [ ] The cutoff is one named constant compared with frontmatter
      `date:`, and a test pins its value.
- [ ] `python3 gates.py` reports 0 problems on main's real tree after the
      change, with no shipped `verification.md` or `review.md` edited
      (`git diff --stat main -- 'docs/**/verification.md'
      'docs/**/review.md'` is empty).
- [ ] `CONTEXT.md` defines the four claim kinds and the roll-up rule.
      `docs/pipeline-protocol.md` states the rule once and links to
      `CONTEXT.md` without redefining the kinds.
- [ ] `skills/verify/TEMPLATE.md`'s Summary guidance and
      `skills/review/TEMPLATE.md`'s Verdict guidance state that the line
      counts its NOT RUN / unknown items and never reads as an unqualified
      pass over them.
- [ ] An ADR recording the rule and the cutoff exists, marked
      provisional.
- [ ] `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`
      and `python3 gates.py && python3 gates.py --selftest` all pass.
      Detector E is clean after `python3 factory_init.py
      update-manifest`, with the payload mirror of `gates.py` updated.

## Out of scope

- Rewriting any shipped `verification.md` or `review.md` (Owner decision
  3, grandfather by date).
- Gating `review.md` mechanically. The rule reaches it through its
  template only.
- Changing H's existing per-section rule, including what counts as a
  claim. So the borderline shape idea.md found is not caught: a criterion
  whose verdict says PASS with a partial not-run hedge (three files on
  main). Its head asserts PASS, H already treats it as a claim, and
  reclassifying it would change the per-section rule.
- Keying the rule on H's prose `not_run` flag (it over-matches; see
  Solution).
- The other rea-learnings recommendations: known-answer evals,
  close-out questions, the regression-test rule.
- Bumping `.claude-plugin/plugin.json`'s version (ADR-0095). The
  release PR after the wave does that.

## Open questions

- The grammar for "the Summary counts or names the NOT-RUN item" and
  "asserts an unqualified pass". The Summary is free prose, so the rule
  must accept the honest shapes above without teaching authors to dodge
  it by rewording. Owner: Architect.
- The cutoff's value, and what H does with a post-feature
  `verification.md` that has no readable frontmatter `date:`. Owner:
  Architect, logged in its assumptions.
- Whether the rule fires on a file with no `## Summary` heading (48 of
  77 today have none). The success criteria above assume it does not:
  there is no Summary line to judge. Owner: Architect, to confirm or
  record otherwise.
- Which disclosure heads count toward "named". For example, does a
  Summary saying "1 DEFERRED" satisfy a criterion disclosed as
  `SKIPPED`? Owner: Architect.

---
stage: idea
run: feature:fail-closed-roll-up
date: 2026-10-17
origin: "Backlog seed at docs/backlog.md line 118 (from: session:2026-10-16), recommendation 3 of docs/research/rea-learnings.md, claimed in place by this stage. Interview answered from autorun-brief.md in this directory (five Owner answers, the rest the orchestrator's reading); no live interview held."
assumptions:
  - "Outside corroboration (the optional last30days check on why-now and evidence) was not run: the skill says never to run it unasked, and no human was present to ask. The interview alone is a complete result."
---

# Idea: Fail-closed roll-up for verification Summaries

## Problem

A reader opens a `verification.md`, reads the `## Summary`, sees "all
criteria pass", and acts on it: merges, ships, or moves the run on.
Further down, a criterion section says the check was never run. The
Summary is the one line people actually read, and it is the one line no
rule states and no gate checks. Detector H makes every criterion section
carry its own evidence or its own NOT-RUN disclosure; nothing says the
Summary may not roll a disclosed NOT RUN, skipped or unknown up into a
pass.

The vocabulary for this is also missing. The repo has no shared words
for what kind of claim a line makes (observed from quoted output,
derived from that, inferred by judgement, or unknown because nobody
looked), so "pass" can quietly cover all four.

## Who has it

- **The Owner at a merge gate**, reading the Summary rather than the
  whole file.
- **Ship's pre-flight**, which asks whether verification "has no
  unresolved failures".
- **Review**, and **the merge train** and **hourly improvement
  routine**, which read and produce artifacts with no Owner in the loop.

Today they cope two ways: by reading the whole artifact, and by Verify
authors who count their gaps in the Summary on their own initiative
(`docs/fixes/toolsmith-mine-pr-permissions/verification.md` opens
"7 PASS, 0 FAIL, 2 NOT YET VERIFIABLE"). Both depend on someone choosing
to be careful.

## Why now

On 2026-10-15 the merge train and the hourly improvement routine began
running on schedules, reading and writing run artifacts unattended. The
habit that has kept Summaries honest so far is an author's habit, and the
authors are now increasingly unattended agents. On 2026-10-16 the
rea-learnings research note found that no rule states the summary half
of the roll-up.

## Evidence

**The measured count of the failure this targets is zero.** No tracked
verification.md today has a Summary that reads as an unqualified pass
over a criterion that disclosed NOT RUN, skipped or unknown. The case
for the change is prevention under unattended authors, plus a reasoned
gap in the rules (stated above), not an observed failure.

Method, run 2026-10-17 on this branch at `207054d`:

1. Enumerate `git ls-files 'docs/**/verification.md' docs/verification.md`.
2. Parse each with `gates.verification_sections` (read-only). A section
   is *disclosed* when one of its labelled verdicts satisfies
   `gates._is_disclosure` ("labelled"), or when it only carries H's
   `not_run` token somewhere in its prose ("token-only"). The `## Summary`
   section itself is excluded.
3. Keep files that have a `## Summary` and at least one disclosed section
   other than a stand-alone "Not verified" list, which by construction
   sits outside every criterion.
4. Read each candidate's Summary and disclosed sections by hand.

Script output (the counting script lives outside the repo):

```
files: 77
no ## Summary section: 48
files with >=1 disclosed non-Summary section: 32
```

Of the 29 files with a Summary, 20 have a disclosed section; 7 of those
are disclosed only in "Not verified" lists, leaving **13 candidates**.
Hand check:

- **Labelled disclosures (3 files), all counted in the Summary.**
  `docs/features/orchestrator/verification.md` (seven criteria
  `NOT RUN — unmet`; Summary "0 of 7 met, 0 failed, 7 unmet"),
  `docs/fixes/toolsmith-mine-pr-permissions/verification.md` (two
  `NOT RUN`; Summary "2 NOT YET VERIFIABLE"),
  `docs/features/codex-style-standards-enforcement/verification.md` (one
  `DEFERRED`; Summary "16 PASS, 3 FAIL, 1 DEFERRED"). None is a case.
- **Token-only, Summary not an unqualified pass (4 files).**
  `docs/features/factory-evolution-v1/verification.md` (14 PASS, 4 FAIL),
  `docs/features/software-factory/verification.md` (3 PASS, 2 PARTIAL,
  3 FAIL), `docs/features/first-live-dispatch/verification.md` (says
  "not re-proven" in the Summary),
  `docs/fixes/deepening-tool-seams/verification.md` ("Three pass under a
  stated narrowing"). None is a case.
- **Token-only, the "not run" text is not a disclosure (3 files).**
  `docs/fixes/dashboard-timeline-unreadable-age/verification.md`
  ("`update-manifest` was not run" because nothing is mirrored),
  `docs/fixes/a-timestamp-the-digest-cannot-parse/verification.md` (an
  out-of-scope item pointed at "Not verified"),
  `docs/features/readme-skill-map/verification.md` (Provenance: "Not run
  at Implement", then run at Verify). None is a case.
- **Borderline (3 files): a criterion asserts PASS with a partial
  not-run hedge, and an otherwise all-pass Summary does not name the
  hedge.** `docs/fixes/one-guarded-file-read/verification.md` criterion 6
  ("PASS (at HEAD only; the per-commit … claim was not replayed …)";
  Summary "Nine of nine brief criteria pass"),
  `docs/features/launch-demo/verification.md` "Terminal recorder, end to
  end" ("PASS — the owner watches the mp4 before merge"; Summary "10 PASS,
  0 FAIL"), `docs/fixes/one-fact-one-owner/verification.md` D3 (PASS "plus
  a two-sample spot check (see *Not verified*)"; Summary "19 PASS, 1
  PASS-AS-AMENDED, 0 FAIL"). In each, the criterion's verdict is a claim
  that H already treats as a claim (the head asserts PASS), and the
  unexamined part is a sub-claim, not the criterion. They are not the
  failure this idea names, but they are the nearest real shape of it.

The 48 files without a `## Summary` heading are outside the count: there
is no Summary line for the rule to judge.

Anecdote, labelled as such: the brief's author hand-sampled four files
before this stage and also found no confirmed instance.

## Solution hunch

A hunch, not a design:

- `CONTEXT.md` gains the claim kinds (observed, derived, inferred,
  unknown) and the roll-up rule: **unknown, unsupported, truncated and
  skipped never aggregate to pass.** `docs/pipeline-protocol.md` states
  the rule once and points at the vocabulary.
- The verify template's `## Summary` and the review template's
  `## Verdict` guidance say the line counts its NOT RUN / unknown items
  and never reads as an unqualified pass over them.
- Detector H learns one rule for `verification.md` dated on or after a
  grandfather cutoff: when a criterion section carries a labelled NOT-RUN
  disclosure, the Summary must name that count or kind and must not
  assert an unqualified pass. It reuses H's existing section parse. The
  exact grammar is Architect's call.
- Shipped artifacts are grandfathered by date, never rewritten.

## Success in one sentence

A new verification.md whose Summary reads as a full pass while one of
its criteria disclosed NOT RUN fails `python3 gates.py`, and no artifact
shipped before the cutoff does.

## Unknowns & risks

- **The count is zero.** The rule guards against a failure nobody has
  committed yet. If the PRD cannot justify prevention for unattended
  authors on its own, the run should shrink to the docs half or stop.
- **Free-prose Summaries.** A grammar that judges "asserts an unqualified
  pass" can false-positive on honest Summaries or be dodged by rewording.
  A rule that teaches authors to dodge it is worse than none. The three
  labelled-disclosure files above are the honest shapes it must accept
  ("7 unmet", "2 NOT YET VERIFIABLE", "1 DEFERRED").
- **Which disclosure triggers it.** H's `not_run` flag fires on prose
  mentions too: here it lit up 10 candidate files whose "not run" text
  was not a disclosed criterion. Keying the rule on that flag rather than
  on a labelled `_is_disclosure` verdict would false-positive on day one.
- **The borderline shape is out of reach.** A PASS with a hedge (the
  three borderline files) is a claim, not a disclosure, so the rule as
  hunched would not see it. Whether it should is a PRD question.
- **Mirroring.** `gates.py` ships into the payload, so a new H rule
  reaches stamped repos and needs the manifest regenerated.
- **Review is ungated.** The rule reaches review.md through its template
  only.
- **Dates.** The cutoff compares frontmatter `date:`; what H does with an
  artifact that has no readable date is open (Architect).

## In-flight check

Ran 2026-10-17 and nothing matches. `gh pr list --state open` returned
one PR, #993 (`docs(pr-body-preflight): ship — released by #991`), which
is unrelated. A search of open issues for roll-up / epistemic /
fail-closed / summary found none, and no open issue title names a
summary, detector H, verification or a verdict. Two local branches
touch detector H (`factory/wo-0011-detector-h`,
`factory/issue-151-detector-h-residuals`), and both are stale heads of
PRs #128 and #154, merged in July 2026. They hold the per-section rule
this run leaves unchanged.

## Next

PRD, through the `prd` skill or the `next` router.

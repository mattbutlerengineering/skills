---
stage: review
run: feature:review-interface-pass
date: 2026-11-04
assumptions:
  - "Autorun stage, no live user: severity is the reviewer's call. No critical and no major finding was found, so nothing was fixed and the battery was not re-run after a fix (it was run once, on the unchanged branch)."
  - "Diff scope is `git diff eff46d2 HEAD` (the run's base, `origin/main` at the brief's pin) at a18c681 (the Verify commit). The code under review is skills/review/SKILL.md, skills/review/references/domain-reviewers.md, skills/review/references/interface.md, tests/test_review_domain_table.py and README.md; the rest are the run's artifacts and one backlog line."
  - "The ADR pass used the live list from `adr_status.py` (122 ADRs). Subjects the diff reaches (skill descriptions, utility skills' reference files, review and credit conventions) were matched by title; none is violated."
---

# Review: An Interface domain pass for review

## Scope

The diff of this run against its base `eff46d2`, read in full: the new
Interface row and its extension-only exception in
`skills/review/references/domain-reviewers.md`; the new
`skills/review/references/interface.md` (122 lines); the reference list and
credit line added to `skills/review/SKILL.md`; the README credits paragraph;
`tests/test_review_domain_table.py`. Plus the PRD, architecture.md,
breakdown.md, verification.md and the brief. Verification came first, so the
usual order holds. The `description` line of `review` is unchanged
(byte-identical), so no routing eval is owed. Nothing was run live and no
model was called, which is by the brief.

Battery, run from this worktree on the branch as it stands:

```
python3 run_tests.py   -> tests: 3994 tests across 127 modules in 53.0s on 8 workers, 0 problem(s)
python3 lint.py        -> lint: 0 problem(s) across 35 skills
python3 kb.py drift    -> drift: 0 problem(s)
python3 gates.py       -> gates: 0 problem(s)
python3 gates.py --selftest -> selftest: ok
```

`git status --porcelain` was empty before this artifact was written.

## Findings

No critical and no major finding. Two minors, both deferred.

### Minor: `*.html` and `*.htm` select documentation pages and static sites

- Scenario: a docs-only diff that edits `docs/index.html` selects the
  Interface pass. The pass reads the removed side, finds no signal on a
  page that holds none, and reports clean. The cost is one quick read, which
  `domain-reviewers.md` accepts for every domain row ("A false selection
  costs one quick read that comes back clean"). It only becomes a defect if
  readers learn to skip the pass because it is often selected for nothing;
  that rate is unmeasured (verification.md, Not verified).
- Standard: none
- Decision: deferred — the Idea named false positives as a risk and the
  Architect chose extension-only selection with the generated-output
  skip as the bound; narrowing `*.html` would miss the server-rendered
  templates the brief wants covered. Revisit when a real adopter diff shows
  the rate.

### Minor: the pass's behavior under a live reviewer is untested

- Scenario: verification's hand-walk applies the three success-statement
  fixtures by reading the rules; no model ran the reference, so a reviewer
  agent might mis-clear a different-selector swap or fail to cap
  Pre-existing findings at three. The decayed contract is the PRD's success
  statement, reached only by a paid run the brief forbids.
- Standard: none
- Decision: deferred — NOT RUN by the brief's no-spend constraint. The
  Owner can add an eval case for the pass and run it with the repo's usual
  eval command; no such case exists today and none was written here.

## Passes with no findings

- Correctness: clean. The three worked examples in `interface.md` agree
  with the clearing rules (a same-selector swap clears; a different-selector
  swap does not; a bare `aria-label` deletion on an icon-only control is
  critical). The `git diff -U0 -M <base>...HEAD` recipe reads the removed
  side and keeps renames as moves. The pin test's selection check matches
  the row's extension tokens and rejects `TEMPLATE.md`, `src/api.ts`,
  `package.json` and `migrations/001.sql`.
- Design: clean. The row and reference follow the existing domain-pass
  contract (the pass name in the heading, evidence or silence, read only).
  Severity stays the skill's own; the three statuses add no new severity
  and leave the fix loop unchanged. `architecture.md` records why no ADR is
  owed (cheap to reverse); that holds the protocol's three-leg test.
- Security: clean. Skill text and a stdlib test only; the external source is
  restated and credited, nothing is copied, no `NOTICE` change.
- Complexity: clean. No code added beyond the pin test; no `lean:` marker in
  the diff.
- ADR compliance: clean. Live ADRs whose subject the diff reaches were
  checked by title (ADR-0020 description recall, ADR-0079 utility reference
  files, ADR-0098 reviewer credential); none is violated, and the
  description is unchanged.
- Domain passes: the diff's changed paths include `*.md` and a `.py` test
  only; no payments, migrations, dependencies or Interface path is selected,
  so no domain pass ran.
- Standards: `docs/standards.json` was read for the `pipeline`, `docs` and
  `factory` domains; no statement matched a finding.

## Verdict

Ready to ship. No critical finding remains unfixed (none was found), and no
major finding is open. Unknown, not run, and not read as passed: the
pass's false-positive rate on real adopter UI diffs (no such diff exists),
and its behavior under a live reviewer agent (needs a paid run the brief
forbids). The routing eval is not owed because the `description` did not
change.

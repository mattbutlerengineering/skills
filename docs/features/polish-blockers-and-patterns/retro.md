---
stage: operate
run: feature:polish-blockers-and-patterns
date: 2026-11-09
users-observed: 0
signal-source: "Scan on 2026-11-09 of the Owner's local agent session transcripts (Claude Code project sessions and omp sessions, 350 sessions with events after the merge on 2026-11-05T06:08Z, newest event 2026-11-09T20:41Z) for an invocation of the polish skill or a read of its files made to run it on a UI. Counts: 0 sessions ran polish; 4 sessions read polish files, all while maintaining this repo, none on a UI. 0 errors, 0 complaints, 0 workarounds. `gh issue list --state all` for polish after the merge: no feedback issue. The scan covers this machine only."
---

# Retro: named blockers and code detection patterns in polish

The release is four days old (merged 2026-11-05), so this retro reflects
days of use, and the scan found no use. The population is zero from
what could be scanned. A scan limit is not a finding that nobody ran
`polish`: it reads only this machine's transcripts, and the plugin is
installed by others from `main`, whom nothing here observes.

## Outcomes vs. intent

### `polish` names its blockers: the six floor items plus eight, each high severity on sight, so "ranked by who is locked out" is checkable (idea.md's success sentence)

- What happened: the text is on `main` (PR #1157, merged 2026-11-05). `skills/polish/SKILL.md` step 5 lists the eight added blockers beside the six floor items and `inspect` ranks them first; `verification.md` records 10 of 11 criteria PASS, and the pin `tests/test_polish_shape.py` holds the eight and the six. Whether any run was ranked by the list is not known.
- Signal strength: unobserved. Shape is verified; use is not.

### `inspect` carries 10 to 15 framework-neutral pattern rows with correct WCAG 2.2 ids, so a code-only reading finds something

- What happened: the table has 12 rows, pinned to 10 to 15 with a WCAG cell on each accessibility row. The ids rest on Implement's recorded read of the W3C text on 2026-11-04, which Verify and Review did not re-fetch. The kill test (does a code-only `polish` find more with the table than without) is still NOT RUN; it needs the Owner's paid run.
- Signal strength: unobserved. No run used the table and the before-and-after comparison was never made.

### Description unchanged and the battery green

- What happened: `verification.md` shows the description hunk absent and the battery green at the shipped head, and `review.md` re-ran it. Nothing after the merge contradicts it.
- Signal strength: measured, at ship time only.

## Open debt

Issues created before the run's merge or citing its artifacts are the run's own and count toward nothing:

- #1156 — the run's feature issue; closed.
- Five minors deferred in `review.md` (loose 3.3.1 id on the disabled-submit row; step 5's "whatever the surface's job" wording; no pointer from step 6 to the table; ledger date and work-order range overlap; the doubled repository name in the credit). None became an issue.
- The kill test, owed to the Owner (`verification.md` §Kill test).

#1617 (six released runs without a retro) was filed after the merge and names the missing retro, so it is not feedback on the feature.

## Run retrospective

- Keep: Verification's quoted WCAG-id record and the shape pin. Making the id check an artifact (`breakdown.md` Notes) let Review accept ids it did not re-fetch, and the pin turned "eight blockers, 10 to 15 rows, an id on each accessibility row" into a test with exact problem strings.
- Change: Decompose wrote rows with no work-order id or PRD citation, so detector O failed on the run's own breakdown at Implement (`breakdown.md` Notes, first entry). Also `release.md` now reads `outcome: released` in its frontmatter while its Outcome section still says "Prepared and stopped"; the body was not rewritten with the frontmatter.
- Stop: nothing identified. The run's cost was low and every stage produced something used by the next.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| Decompose emitted breakdown rows with no work-order id or PRD citation, caught only when Implement ran gates | `breakdown.md` Notes, first Implement entry | mechanical | `gates.py` detector O (PRD-COVERAGE) already caught it; the carrier is running it at the Decompose boundary, in `skills/decompose/SKILL.md`'s own checks, not a new rule |
| Provisional work-order ids (WO-0191 to WO-0197) were picked by hand against five sibling runs | `breakdown.md` Notes; `review.md` §Minor ledger rows | mechanical | `gates.py` detector C, which already fails a duplicated work order at merge time |
| The pin's `focus` floor phrase matches any use of the word, so it holds that check weakly | `review.md` §Passes, Correctness | mechanical | `tests/test_polish_shape.py`, anchoring the phrase to the floor item's full wording |
| The disabled-submit row cites 3.3.1, a loose fit | `review.md` §Minor, first | judgement | none; a reader's call, disclosed in the row's verification note |
| Step 5 says the list outranks findings "whatever the surface's job", which contradicts step 2's surface-job rule if read literally | `review.md` §Minor, second | judgement | `docs/standards.json` carries no statement on severity wording; none fits |
| `release.md` frontmatter was rewritten to `released` while the Outcome section kept "Prepared" | `release.md` Outcome vs frontmatter | mechanical | a `gates.py` detector comparing `release.md` frontmatter `outcome:` with its Outcome section; none exists |

## Idea seeds

- Run `gates.py` detector O at the end of Decompose, so a breakdown without work-order ids and PRD citations is caught before Implement starts (from: feature:polish-blockers-and-patterns)
- Anchor the `focus` floor phrase in `tests/test_polish_shape.py` to the floor item's full wording so the check cannot pass on any use of the word (from: feature:polish-blockers-and-patterns)
- Add a gates detector that fails a `release.md` whose Outcome section contradicts its frontmatter `outcome:` after the Ship write-back (from: feature:polish-blockers-and-patterns)
- Run the owed kill test: `polish` code-only on one fixture UI on `eff46d2` and on current `main`, and record which table rows each run named (from: feature:polish-blockers-and-patterns)
- Re-run this Operate scan after one week of use and count sessions that ran `polish` on a UI, so the outcomes can leave `unobserved` (from: feature:polish-blockers-and-patterns)

## Run complete

2026-11-09. The seeds above are the input to the next Idea-stage run. The scanner seed (the Moonshot rung) was already in `docs/backlog.md` and is not repeated.

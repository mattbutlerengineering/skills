---
stage: capture
run: maintenance:a-zero-count-names-nothing
date: 2026-10-17
re-entry: implement
origin: docs/backlog.md seed (from feature:fail-closed-roll-up), detector H's zero-count roll-up gap, raised by that run's retro
assumptions: ["re-entry: implement, taken from the brief's reading (the orchestrator's, not an Owner answer) under the skill's rule that a scoped fix with no design decisions re-enters at Implement. Owner decision 2 fixes the shape, and the change stays inside the existing section parse, so Capture found no design question to send to Architect", "Implement: the zero grammar is 0/zero/no/none/nothing as a whole word, at most one word, an optional was/were, then spaces, hyphens or emphasis; the brief left the exact grammar to Implement, and this covers its four required shapes plus the negation", "Implement: the negated zero (no criteria were skipped) is treated as a zero, taking the brief's recommended yes since it costs one alternation under the same bound and is pinned RED then GREEN; a two-word negation (no live check was skipped) still names, recorded as an accepted limit with a lean: marker and in ADR-0108", "Implement: the verify template line 11 is changed, because it asks for pass/fail counts and so invites the 0 NOT RUN shape both judged artifacts used; skills/verify/TEMPLATE.md is not mirrored into factory/templates (factory_init.MIRRORS has no skills/ entry), so no payload lockstep applies", "Implement: a new provisional ADR-0108 superseding ADR-0107 in part, not an amendment line, because the seed asks for one and ADR-0107's Consequences say a dodge seen in a real artifact is a reason for a new ADR, not a rewrite; ADR-0107's status becomes superseded in part by ADR-0108 (the naming clause; provisional), the README grammar for a partial supersession; 0108 was the next free number on the branch and on origin/main, and no open PR adds one"]
---

# Defect: a zero count names nothing

## Defect (or Condition)

Detector H's Summary roll-up (ADR-0107) is switched off by the count
shape its own verify template teaches.

`gates.verification_sections` (`gates.py:1152`) sets a section's
`names_unknown` on any unfenced `SUMMARY_UNKNOWN_TERM` match
(`gates.py:1204`). `gates._rollup_problems` (`gates.py:1236`) returns
`[]` as soon as any `## Summary` has `names_unknown` set
(`gates.py:1246`), before it looks at disclosures at all.

- **Observed.** "11 PASS, 0 FAIL, 0 NOT RUN" matches on "NOT RUN". So
  a Summary saying that *zero* items were not run counts as naming the
  unknown kind. It still passes when a criterion section's `- Result:`
  is a NOT RUN disclosure. The stale-Summary drift the rule exists for
  (a criterion re-run and dropped to NOT RUN, with the Summary left as
  written) passes the gate.
- **Expected** (Owner decision 2, "Zero doesn't name"). An unknown-kind
  term directly preceded by a zero count (`0` or `zero`, optionally
  followed by a separator) does not set `names_unknown`. Every other
  mention still names: "1 NOT RUN", "2 skipped", "criterion 4 was not
  run". So an honest Summary that passes today keeps passing. Comparing
  the counts with the number of disclosed sections ("count must match")
  was rejected.

## Reproduction / Evidence

Reproduced for real on 2026-10-17 at `d702008`, outside the repo. The
probe scripts live in the session scratchpad, not the repo:
`repro_zero.py` for `evidence_problems` and `repro_zero_tree.py` for
`check_evidence_honesty`. Each script imports this tree's `gates.py`.
The fixture is the tracked
`docs/fixes/a-quoted-date-dodges-the-cutoff/verification.md`, which
the rule judges because it is dated `2026-10-17`. Its line 15 reads
`11 criteria: 11 PASS, 0 FAIL, 0 NOT RUN. ...`. In memory, criterion
9's line 278 `- Result: PASS` is replaced by
`- Result: NOT RUN — probe`. The file on disk is never edited.

Through H's public text function, `gates.evidence_problems`, verbatim:

```
control (unflipped, '0 NOT RUN'): line 15 = '11 criteria: 11 PASS, 0 FAIL, 0 NOT RUN. On HEAD `8745052`, every'
  evidence_problems -> []
probe A (crit 9 NOT RUN, Summary unchanged): line 15 = '11 criteria: 11 PASS, 0 FAIL, 0 NOT RUN. On HEAD `8745052`, every'
  evidence_problems -> []
probe B (crit 9 NOT RUN, ', 0 NOT RUN' removed): line 15 = '11 criteria: 11 PASS, 0 FAIL. On HEAD `8745052`, every'
  evidence_problems -> [(13, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass')]
probe C [0 not run]: line 15 = '11 criteria: 11 PASS, 0 FAIL, 0 not run. On HEAD `8745052`, every'
  evidence_problems -> []
probe C [zero skipped]: line 15 = '11 criteria: 11 PASS, 0 FAIL, zero skipped. On HEAD `8745052`, every'
  evidence_problems -> []
probe C [0 N/A]: line 15 = '11 criteria: 11 PASS, 0 FAIL, 0 N/A. On HEAD `8745052`, every'
  evidence_problems -> []
probe C [0-skipped]: line 15 = '11 criteria: 11 PASS, 0 FAIL, 0-skipped. On HEAD `8745052`, every'
  evidence_problems -> [(13, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass')]
```

The same probe through the detector's tree entry point,
`gates.check_evidence_honesty`, on a throwaway tree that holds only the
flipped file:

```
check_evidence_honesty A (Summary unchanged) -> []
check_evidence_honesty B (zero count removed) -> ['H: docs/fixes/a-quoted-date-dodges-the-cutoff/verification.md:13 summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass']
```

Probe A is the defect, and probe B is the existing problem string the
fix must produce for A. Probe C shows that the four zero shapes behave
differently. "0 not run", "zero skipped" and "0 N/A" dodge the rule.
"0-skipped" is already refused. The term's leading boundary
`(?<![\w/-])` means a term right after a hyphen never matches, so the
hyphen separator needs a guard test, not a RED one.

**Main tree.** There are 92 tracked `verification.md` files (`git
ls-files`). The roll-up judges two of them (`_rollup_applies`, dated on
or after `ROLLUP_ADOPTED`). Neither has a labelled disclosure, so no
judged artifact changes outcome:

```
tracked verification.md: 92  judged by roll-up: 2
- docs/features/fail-closed-roll-up/verification.md date='2026-10-17' disclosures=0 evidence_problems=[]
    summary hits (line, term, zero-preceded): [(16, 'NOT RUN', True), (17, 'unknown', False), (20, 'NOT RUN', False), (25, 'unknown', False), (27, 'Not verified', False)]
- docs/fixes/a-quoted-date-dodges-the-cutoff/verification.md date='2026-10-17' disclosures=0 evidence_problems=[]
    summary hits (line, term, zero-preceded): [(15, 'NOT RUN', True)]
gates: 0 problem(s)
```

In the second file the Summary's only hit follows a zero. After the fix
it will name nothing, and it still passes because it has no disclosures.
The first file also has hits that do not follow a zero. **This run is
prevention**: the rule's own template produces the shape, but nothing
on main bites today.

## Root-cause hypothesis

Hypothesis: `names_unknown` tests whether a word is present, and a zero
count is a word that says the opposite of naming. The comment above
`SUMMARY_UNKNOWN_TERM` (`gates.py:232`) states the premise: "A count
carries its word ("1 NOT RUN"), so naming covers counting". That holds
for every count except zero.

## Blast radius

- **Code.** `gates.py` and its payload copy
  `factory/templates/tools/factory/gates.py`, which is byte-identical
  today (`cmp`) and manifest-pinned. Stamped repos get the change on
  their next payload update, and none has the roll-up yet (the
  fail-closed-roll-up retro, §Reach).
- **Behaviour.** Outcome changes only for a judged Summary whose every
  unknown-kind mention follows a zero, and only when a criterion
  section holds a labelled disclosure. That artifact is then refused
  with H's existing roll-up string. A Summary with no disclosures is
  never refused by the roll-up, whatever its Summary says.
- **Who.** No artifact in this repo changes outcome (the count above).
  A stamped repo writing a template-shaped Summary over a disclosed
  criterion would see an actionable H problem. Severity: low. It is a
  gate bypass the template invites, and no one has used it.
- **Since.** #998 (`461803a`, 2026-10-17), the rule's introduction.

## Ruled out

- **"Count must match"** (compare the Summary's numbers with the
  disclosed-section count). The Owner rejected it in decision 2, and
  ADR-0107 already rejected a count requirement.
- **Changing `ROLLUP_ADOPTED`.** No judged artifact changes outcome, so
  the cutoff stands. Out of scope per the brief.
- **A design question for Architect.** The shape is decided, and the
  change sits inside `verification_sections`' existing per-line loop
  (or a helper it calls). There is no second parse and no new module.
- **The hyphen shape as a dodge.** "0-skipped" is already refused
  (probe C above).
- **In flight.** The check ran on 2026-10-17 and nothing matches.
  `gh pr list --state open` returned `[]`. `gh issue list` searches for
  "zero count", "0 NOT RUN", `names_unknown`, `SUMMARY_UNKNOWN_TERM` and
  "roll-up" returned only unrelated issues (journals and a decompose
  item). `git log --all -S` for `SUMMARY_UNKNOWN_TERM` and
  `names_unknown` over `gates.py` finds only `c3627a2` and `461803a`,
  the commits that introduced them. No branch or worktree carries a
  change to either.

## Work items

Re-entry is Implement, so these checkboxes are the run's breakdown.

- [x] **Zero-shape tests first (RED)**: in `TestEvidenceRollUp`
  (`tests/test_gates.py:2822`), add the retro's probe as a fixture: a
  judged artifact whose Summary reads "N PASS, 0 FAIL, 0 NOT RUN" over a
  criterion with `- Result: NOT RUN`. Add one subtest per zero shape
  ("0 NOT RUN", "0 not run", "zero skipped", "0 N/A") over a disclosed
  criterion.
  - Accept: each asserts the exact existing string `summary "Summary"
    neither counts nor names the 1 criterion section(s) disclosed as not
    run (first: "...", line N); unknown never rolls up to pass` through
    `evidence_problems` (or `check_evidence_honesty` with its `H:
    {rel}:{lineno}` prefix), and each fails before the fix.
- [x] **Guards that stay green**: each zero shape with no disclosed
  criterion passes. Non-zero and named mentions over a disclosure pass:
  "1 NOT RUN", "2 skipped", "criterion 4 was not run". So does a line
  holding both a zero and a non-zero mention ("0 NOT RUN, 1 skipped"),
  which is judged per match, not per line. "0-skipped" over a disclosure
  stays refused.
  - Accept: these pass before and after the fix, and H's existing tests
    pass unedited.
- [x] **Negated zero ("no criteria were skipped")**: decide it as the
  brief recommends. Treat it as a zero if that is cheap and tested;
  otherwise record it as an accepted limit in Notes and in the ADR.
  - Accept: either a RED-then-GREEN test pins it, or the limit is
    written down with its reason.
- [x] **The fix**: in `verification_sections` (or a helper it calls),
  a `SUMMARY_UNKNOWN_TERM` match whose preceding text ends in a zero
  count (`0` or `zero` as a whole word, optionally followed by
  whitespace or a hyphen) does not set `names_unknown`. Every other
  match does. Keep one section parse. Update the comment above
  `SUMMARY_UNKNOWN_TERM` whose "naming covers counting" premise fails
  at zero, and the `verification_sections` docstring. Stdlib only.
  - Accept: the RED tests go GREEN, and `python3 -m unittest
    tests.test_gates` passes.
- [x] **Verify template wording**: read `skills/verify/TEMPLATE.md`
  line 11. If its count guidance teaches the dodge, add that a zero
  count does not name a disclosed criterion.
  - Accept: either the line is changed, or Notes says why it already
    does not teach the dodge.
- [x] **ADR**: a new provisional ADR succeeding ADR-0107's naming
  clause ("Satisfied by naming the kind"), as the seed asks, with its
  row in `docs/adr/README.md`. Record the rejected "count must match"
  option. If the protocol prefers an amendment line on a provisional
  ADR, use that and log the choice in Notes.
  - Accept: `docs/adr/` states the zero-count rule, and `python3
    gates.py` and `python3 kb.py drift` are clean.
- [x] **Payload mirror and manifest**: copy `gates.py` to
  `factory/templates/tools/factory/gates.py`. Delete any stray
  `.orig`/`.rej` files, then run `python3 factory_init.py
  update-manifest` and commit the manifest.
  - Accept: `cmp` shows the two files are identical, and detector E is
    clean.
- [x] **Backlog claim**: the claim on `docs/backlog.md` line 125
  landed with this capture commit. Confirm it is still there and
  well-formed, then check this box.
  - Accept: the seed line ends in
    `(claimed: maintenance:a-zero-count-names-nothing)`.
- [x] **Whole-repo checks**: `python3 run_tests.py`, `python3 lint.py`,
  `python3 kb.py drift`, and `python3 gates.py && python3 gates.py
  --selftest`.
  - Accept: all pass, and `gates.py` reports `gates: 0 problem(s)` on
    the real tree with no shipped artifact edited.

## Notes

- 2026-10-17 (Capture): `gates_selftest.py`'s `rolledup` fixture has
  no zero-count row, and stamped repos run only the selftest. Adding
  one is not in the brief's scope and no work item covers it. It sits
  next to the selftest dodge-row seed at `docs/backlog.md` line 124.
- 2026-10-17 (Capture): out of scope, per the brief: backlog lines 126
  to 128 (the shared heads alternation, the `n't run` tightening, the
  stamped-repo measurement), H's per-section rule, and shipped
  artifacts.
- 2026-10-17 (Implement): RED at `9fc15c7`: 12 failures, each `[]`
  where H's roll-up string was expected (11 zero-shape and probe
  subtests plus the `names_unknown` section test); the guards passed.
  GREEN at `4cc2ede`. Reverting only the `_names_unknown(line)` call to
  the old `SUMMARY_UNKNOWN_TERM.search(line)` brings back the same 12
  failures; dropping `SUMMARY_ZERO_COUNT`'s leading boundary fails the
  `10 NOT RUN` guard. Capture's `repro_zero.py` and
  `repro_zero_tree.py` probes now return the roll-up string for probe A
  and every probe C shape.
- 2026-10-17 (Implement): work item 3, the negated zero, is a zero
  (`no`, `none`, `nothing` in `SUMMARY_ZERO_COUNT`), pinned by the
  "no criteria were skipped", "none skipped" and "nothing was skipped"
  subtests. Limit: a negation with two words before the verb ("no live
  check was skipped") still names. It carries a `lean:` marker and is in
  ADR-0108's Consequences. A side effect, also in ADR-0108: "nothing
  was skipped except live dispatch" as a Summary's only mention is now
  refused.
- 2026-10-17 (Implement): work item 5, `skills/verify/TEMPLATE.md`
  line 11 asks for pass/fail counts and so invites "0 NOT RUN", so it
  now adds that a zero count names nothing. Not mirrored into
  `factory/templates`.
- 2026-10-17 (Implement): work item 6, new provisional
  `docs/adr/0108-a-zero-count-names-nothing.md` superseding ADR-0107 in
  part, with ADR-0107's status line and both index rows updated.
- 2026-10-17 (Implement), adjacent and not fixed: `skills/verify/SKILL.md`
  lines 31 to 33 say H "refuses a Summary that names no unknown word"
  and cite ADR-0107 only. Under ADR-0108 a zero-preceded word does not
  count, so the sentence is slightly loose. Out of this run's scope
  (the brief names only the template).
- Next stage: Verify.

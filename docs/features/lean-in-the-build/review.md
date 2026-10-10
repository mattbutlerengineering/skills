---
stage: review
run: feature:lean-in-the-build
date: 2026-10-10
assumptions:
  - "Review scaled to the blast radius: two prose bullets in two skill bodies, one template line, a patch version bump carried into the manifest, and run artifacts. No executable code changed. The bullets were judged against lean's own text (SKILL.md, references/ladder.md, references/cut-list.md) for accuracy, not re-litigated on taste. Taken without user input."
  - "The one fix applied (the floor list) is minor and surgical, so it was made here rather than routed back to Implement; architecture.md's quoted wording and the breakdown row's four-item acceptance are left as the record of what was planned. Taken without user input."
---

# Review: lean in the build

## Scope

`git diff origin/main...HEAD` at 834402f: 12 files, 783 insertions, 4
deletions. The reviewable change is `skills/implement/SKILL.md` (one
bullet in step 4), `skills/review/SKILL.md` (three passes become four,
plus the **Complexity** bullet), `skills/review/TEMPLATE.md` (the
clean-pass prompt names complexity), `.claude-plugin/plugin.json`
0.5.0 -> 0.5.1 and the matching `factory/manifest.json` version field.
The rest is this run's own artifacts and three appended
`docs/factory/costs.jsonl` rows. All four passes were applied, the
fourth (Complexity) through `../lean/references/cut-list.md` as the
run itself now requires.

Terms checked against lean: "ceiling" and "trigger" are lean's own
words for what a `lean:` marker names (SKILL.md step 3, step 5);
"evidence its tag owes" is the cut-list's "Evidence it owes" column;
"stop at the first rung that holds" is SKILL.md step 2 verbatim; the
suspicion sentence restates SKILL.md step 4; a marker with no trigger
being the thing flagged matches step 5; the `deepen` hand-off for shape
rather than size matches step 6. Neither bullet names a harness tool,
so both stay harness-neutral.

## Findings

### Minor: the Implement bullet restated lean's floor with one of its five items missing

- Scenario: the bullet said "Lean's floor is never cut:" and listed
  validation, data-loss handling, security and accessibility. Lean's
  floor (SKILL.md step 3, ladder.md "When the ladder is the wrong
  tool", cut-list.md "What never appears") has a fifth item, "anything
  the user explicitly asked for". An implementer reading only the
  bullet takes the four-item list as complete, and rung 1 ("does this
  need to exist?") then reads as licence to drop an explicitly
  requested detail that no acceptance criterion happens to restate.
  The four-item list came from the PRD and the breakdown row; the
  wording is still a decayed restatement of lean's contract.
- Standard: none
- Decision: fixed. The bullet now ends the list with "anything the user
  explicitly asked for". `skills/lean` is untouched.

### Minor: the Complexity bullet's suspicion rule names only the `dead` tag's evidence

- Scenario: "A cut whose references you could not enumerate is a
  suspicion" covers a `dead` cut. The cut-list marks any finding it
  could not confirm with a leading `?`, so a `reuse` cut whose
  same-behaviour evidence is missing is also a suspicion. The bullet
  says this only by implication: "Each confirmed cut is a finding".
  A reviewer could file an unconfirmed `reuse` or `stdlib` cut as a
  finding.
- Standard: none
- Decision: deferred. The sentence is lean's own (SKILL.md step 4,
  "A cut whose references were not enumerated is reported as a
  suspicion"), and "Each confirmed cut" already keeps unconfirmed cuts
  of every tag out of the findings. Widening it would rewrite the
  wording architecture.md settled for no change in behaviour. Revisit
  if a review files an unconfirmed non-`dead` cut.

### Minor (pre-existing, outside this diff): lint does not check that a sibling skill's reference exists

- Scenario: `lint.py`'s `SKILL_ASSET` lookbehind skips
  `../<skill>/references/...` on purpose (it would otherwise resolve a
  bare `references/...` against the wrong directory), and
  `LOCAL_LINK` sees only markdown links. So nothing checks the
  backticked cross-skill path at all. Reproduced: changing
  `../lean/references/ladder.md` to `ladderr.md` in
  `skills/implement/SKILL.md` still printed
  `lint: 0 problem(s) across 28 skills` (reverted at once). The same
  blind spot covers `skills/pipeline-board/SKILL.md`'s
  `../architecture-diagram/references/design-system.md`.
- Standard: none
- Decision: deferred. The checker is not this run's code. Filed as a
  `docs/backlog.md` seed `(from: feature:lean-in-the-build)`.

## Passes with no findings

- **Correctness**: no defects beyond the floor restatement above. The
  Complexity bullet's "stand in for the failure scenario" squares the
  new findings with the Rule that every finding needs a scenario or a
  decayed contract.
- **Design**: both bullets cite lean by path in backticks, the pattern
  pipeline-board already uses (ADR-0008 self-containment holds, and
  lint is clean). No rungs, tags or floor are copied into review: the
  pass points at the cut-list, whose "What never appears" keeps the
  floor out of the findings. Lean's "review is read-only" is about
  lean's own mode. Inside review, a cut is ranked and goes through the
  fix loop like any other finding, as architecture.md says.
  "Nothing about the ladder goes into `breakdown.md`" does not clash
  with lean step 6: a cut outside the current item still goes under
  the breakdown's Notes through implement's existing step 5.
- **Security**: no executable code, secrets, network calls or new
  dependencies. `docs/standards.json`'s one pipeline/docs statement
  (`adr0004-typed-ids-in-frontmatter`) holds: no typed ID was added
  outside frontmatter.
- **Complexity**: nothing to cut. The diff adds no `lean:` marker. Each
  added sentence carries a rule a later stage acts on, and the
  template change is one word.

## Verdict

Ready to ship. One minor was fixed and two minors were deferred with
reasons, one of them as a backlog seed. The paid routing eval and
charter replay are still owed, as verification.md records.

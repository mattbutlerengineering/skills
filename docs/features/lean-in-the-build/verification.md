---
stage: verify
run: feature:lean-in-the-build
date: 2026-10-10
assumptions:
  - "The routing eval (trigger_eval.py) and charter_replay.py were NOT RUN: both are paid and the brief forbids them. Owed, not run. Taken from the brief."
  - "Packaging row WO-0152's acceptance said factory/manifest.json is not regenerated; it was regenerated (version field only, 0.5.0 -> 0.5.1), as logged in breakdown.md Notes. Verified against PRD-0012's own Packaging criterion and detector E instead of the row's narrower wording. Taken without user input."
---

# Verification: lean in the build

## Summary

5 of 5 PRD-0012 success criteria pass, and the breakdown's acceptance
criteria pass, with one logged deviation (the manifest's version field,
below). Every check ran on the branch tip (3246413) on 2026-10-10, on
top of `origin/main` 6aacc5c; output is pasted as it printed. Verdict:
ready for Review. The paid evals are owed.

```
$ git rev-parse --short origin/main
6aacc5c
$ git merge-base --is-ancestor origin/main HEAD && echo up-to-date
up-to-date
$ git diff origin/main --stat
 .claude-plugin/plugin.json                       |   2 +-
 docs/factory/costs.jsonl                         |   3 +
 docs/features/lean-in-the-build/architecture.md  | 183 +++++++++++++++++++++++
 docs/features/lean-in-the-build/autorun-brief.md | 138 +++++++++++++++++
 docs/features/lean-in-the-build/breakdown.md     |  60 ++++++++
 docs/features/lean-in-the-build/idea.md          |  93 ++++++++++++
 docs/features/lean-in-the-build/prd.md           |  96 ++++++++++++
 factory/manifest.json                            |   2 +-
 skills/implement/SKILL.md                        |   8 +
 skills/review/SKILL.md                           |  10 +-
 skills/review/TEMPLATE.md                        |   2 +-
 11 files changed, 593 insertions(+), 4 deletions(-)
```

## Criteria & evidence

### Implement consults the ladder (PRD-0012; WO-0150)

- Check: diff `skills/implement/SKILL.md` against `origin/main`; confirm
  the referenced path resolves from the skill's directory; confirm no
  markdown link, no description change, and the breakdown and implement
  templates unchanged.
- Evidence:
  ```
  $ git diff origin/main -- skills/implement/SKILL.md
  @@ -23,6 +23,14 @@ document — the code is the artifact, and progress is the checkboxes.
     - Turn the item's acceptance criterion into a failing test at the highest
       seam the codebase offers (prefer existing test seams over new ones).
     - Watch it fail for the right reason.
  +   - Before writing the implementation, climb `lean`'s ladder in
  +     `../lean/references/ladder.md` and stop at the first rung that holds.
  +     Lean's floor is never cut: validation where untrusted input enters,
  +     error handling that prevents data loss, security controls,
  +     accessibility basics. A deliberate shortcut with a known ceiling
  +     carries a comment starting `lean:` that names the ceiling and what
  +     would trigger the upgrade; that marker is the record, so nothing
  +     about the ladder goes into `breakdown.md`.
     - Write the minimum implementation that passes, matching the
       architecture's contracts and the codebase's existing style.
  $ ls -l skills/implement/../lean/references/ladder.md
  -rw-r--r--  1 mbutler  staff  5608 Oct 10 15:08 skills/implement/../lean/references/ladder.md
  $ grep -n '](.*lean' skills/implement/SKILL.md skills/review/SKILL.md; echo "(exit $?)"
  (exit 1)
  $ git diff origin/main -- skills/implement/SKILL.md skills/review/SKILL.md | grep -c '^[-+]description:'
  0
  $ git diff origin/main --stat -- skills/implement/TEMPLATE.md skills/decompose/TEMPLATE.md skills/lean evals/ factory/templates/
  (no output)
  ```
- Result: PASS

### Review has a Complexity pass (PRD-0012; WO-0151)

- Check: diff `skills/review/SKILL.md` and `skills/review/TEMPLATE.md`
  against `origin/main`; confirm the referenced path resolves.
- Evidence:
  ```
  $ git diff origin/main -- skills/review/SKILL.md skills/review/TEMPLATE.md
  -4. **Review in three passes:**
  +4. **Review in four passes:**
  ...
     - **Security** — inputs validated at boundaries, no secrets in code,
       injection surfaces parameterized, errors don't leak internals.
  +   - **Complexity** — apply `lean`'s cut-list in
  +     `../lean/references/cut-list.md` to the run's diff. Each confirmed cut
  +     is a finding: its cut-list line and the evidence its tag owes stand in
  +     for the failure scenario. A cut whose references you could not
  +     enumerate is a suspicion, not a finding. Every `lean:` marker the diff
  +     adds must name its ceiling and its trigger; one that names no trigger
  +     is a finding. A concern about a module's shape rather than its size is
  +     handed to `deepen` in one line — never refactored here.
  --- a/skills/review/TEMPLATE.md
  -<Which of correctness / design / security came back clean.>
  +<Which of correctness / design / security / complexity came back clean.>
  $ ls -l skills/review/../lean/references/cut-list.md
  -rw-r--r--  1 mbutler  staff  4393 Oct 10 15:08 skills/review/../lean/references/cut-list.md
  ```
  The TEMPLATE.md hunk above is that file's only change (`--stat`: 1
  insertion, 1 deletion).
- Result: PASS

### lean stays a utility skill (PRD-0012; WO-0150, WO-0151, WO-0152)

- Check: `protocol.py` membership; `next` never names lean; lean's files
  unchanged.
- Evidence:
  ```
  $ python3 -c "import protocol;print('UTILITY', 'lean' in protocol.UTILITY_SKILLS)"
  UTILITY True
  $ python3 -c "import protocol;print('lean' in protocol.STAGES, 'lean' in protocol.ALL_SKILLS, [k for k in protocol.STAGE_ARTIFACTS if 'lean' in str(k)])"
  False True []
  $ grep -n "lean" skills/next/SKILL.md; echo "(next exit $?)"
  (next exit 1)
  $ git diff origin/main --stat -- skills/lean
  (no output; same command as under the first criterion)
  ```
- Result: PASS

### Packaging (PRD-0012; WO-0152)

- Check: both version fields; whether any `factory_init.MIRRORS` source
  or `factory/templates/**` file changed; regenerate the manifest again
  and confirm it does not move (detector E's manifest/payload agreement
  is also in the battery).
- Evidence:
  ```
  $ python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'], json.load(open('factory/manifest.json'))['version'])"
  0.5.1 0.5.1
  $ git diff origin/main -- factory/manifest.json
  @@ -1,6 +1,6 @@
   {
     "plugin": "idea-to-prod",
  -  "version": "0.5.0",
  +  "version": "0.5.1",
     "files": {
  $ git diff origin/main --name-only > changed.txt && python3 -c "...intersect with factory_init.MIRRORS sources..."
  26 mirror entries; changed mirrored: []
  $ python3 factory_init.py update-manifest && git diff --stat -- factory/manifest.json && echo "manifest-idempotent: no diff after regen"
  factory-init: 0 problem(s)
  manifest-idempotent: no diff after regen
  ```
  No checksum moved: the manifest's only change is the version field the
  plugin bump carries. This deviates from WO-0152's wording ("not
  regenerated") as logged in breakdown.md Notes, and matches the
  precedent of every recent version bump on main.
- Result: PASS (with the logged deviation from the row's wording)

### Battery (PRD-0012; WO-0152)

- Check: the full CI battery on the branch tip, before and after this
  artifact was written; no eval definition edited.
- Evidence:
  ```
  $ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
  Ran 2066 tests in 36.080s
  OK
  $ python3 lint.py
  lint: 0 problem(s) across 28 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
  `git diff origin/main --stat -- evals/` prints nothing (shown under the
  first criterion), so no eval definition or result changed.
- Result: PASS

## Failures

None.

## Not verified

- Routing eval (`python3 trigger_eval.py`): NOT RUN, paid. The
  `implement` and `review` descriptions are unchanged, so routing should
  not move, but no run says so.
- Charter replay (`python3 charter_replay.py`): NOT RUN, paid.
- Behavioural effect: whether a live Implement agent actually climbs the
  ladder and leaves `lean:` markers, and whether Review's Complexity pass
  produces findings rather than a boilerplate "none", is not observable
  until a real run uses the new wording (the PRD's open question for the
  Operate retro).
- Cross-skill path resolution is checked here in the source tree only.
  That the plugin installs `lean` as a sibling of `implement` and
  `review` is the assumption the sanctioned `../<skill>/references/`
  pattern already rests on; lint's `check_skill_assets` does not check
  sibling paths (the pre-existing gap architecture.md assigns to Review).

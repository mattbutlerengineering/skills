---
stage: verify
run: maintenance:plugin-description-drift
date: 2026-08-23
assumptions: ["No prd.md exists in a maintenance run, so the criteria list is built from defect.md's two Accept clauses, decomposed into the seven checkable claims they contain", "Criterion 5 is verified by reconstruction rather than by replay: the pre-fix red was observed live during Implement, and re-creating it here by reverting the description is the same observation on the same tree"]
---

# Verification: maintenance:plugin-description-drift

Criteria come from `defect.md`'s two work items — a maintenance run has no
`prd.md`, so the Accept clauses are the whole of the contract. Seven
checkable claims, all run against the working tree on 2026-08-23. Each
carries its verdict in its own section below; the roll-up is at the end.

## C1 — `check_plugin_skills` exists and is wired into the checker list

Check: grep the definition, then print the registry tuple.

```
36:def check_plugin_skills(root):
CHECKERS = (check_manifest, check_plugin_skills,
            check_pi_package, check_skills,
            check_skill_recitals, check_skill_assets, check_templates,
            check_router, check_readme_skills, check_protocol,
            check_protocol_tables, check_backlog, check_evals,
            check_output_evals, check_ledger, check_ledger_links)
```

**PASS.** It sits second, next to `check_manifest`, which reads the same
file. `check_readme_skills` remains in the tuple untouched.

## C2 — one problem string per unnamed utility skill

Check: call the public checker against a temp tree whose description names
no skill at all, and count.

```
12 problems
plugin.json's description never names utility skill 'address-pr-review'
plugin.json's description never names utility skill 'work-queue'
```

**PASS.** Twelve problems for twelve slugs — one each, not one aggregate.
First and last shown; the twelve match `protocol.UTILITY_SKILLS` exactly.

## C3 — a test asserts the exact strings through the public interface

Check: run the new suite.

```
Ran 7 tests in 0.064s

OK
```

`TestPluginSkills` asserts full problem-string equality via
`lint.check_plugin_skills`, never a private helper, and covers the missing
manifest and unparseable-JSON paths as one problem rather than twelve.

**PASS.**

## C4 — the pre-fix red named the three missing slugs

Check: this was observed live during Implement, before `plugin.json` was
touched. Reconstructed here by reverting the description on the same tree.

```
exit 1
LINT: plugin.json's description never names utility skill 'animated-diagram'
LINT: plugin.json's description never names utility skill 'architecture-diagram'
LINT: plugin.json's description never names utility skill 'interactive-architecture-diagram'
lint: 3 problem(s) across 24 skills
```

**PASS.** Exactly the three the defect brief named, and no others.

## C5 — the regression guard actually fires

Check: with the description reverted, run the live-tree suite —
`TestMainSummary` executes `lint.main()` against the real repo root and
requires exit 0.

```
live-tree suite: FAILED (failures=1)
```

**PASS**, and this is the centerpiece the protocol asks a maintenance run
for. The guard is not a new bespoke test: `TestMainSummary` already
existed and already ran lint against the real tree. It could not see this
defect because no checker looked. With `check_plugin_skills` wired in, the
same pre-existing test goes red on the drift — which is precisely how the
failure was first surfaced during Implement.

## C6 — the description names every utility skill, and the checker is clean

Check: reload the manifest and diff its description against the taxonomy.

```
unnamed utility skills: none
```

**PASS.** 405 characters, up from 331. `name`, `version` and `author`
round-tripped unchanged — the edit was a substring replacement, not a
`json.dumps` rewrite, so the file's two-space formatting is intact.

## C7 — the full battery is green

Check: the repo's three verification commands, plus the on-demand
one-owner pre-pass.

```
Ran 1351 tests in 16.629s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
```

**PASS.** 1351 tests, up from main's 1344 by the seven added here. The
one-owner pre-pass still reports its nine pre-existing findings and names
neither `lint.py` nor `check_plugin_skills`, so this change introduced no
second owner of anything.

## Not verified, and why

- **`claude plugin` rendering.** Nothing here proves how a marketplace or
  CLI surface renders the longer description; the criterion was
  completeness against the taxonomy, and no length limit is near (405 of
  a documented 1024 for skill descriptions).
- **The stage-skill prose.** Out of scope by the capture assumption: the
  description names stages in title case, not by slug, so no checker
  holds that half and none was added.
- **`trigger_eval.py` and `charter_replay.py`.** Never run — real model
  calls that cost money, excluded from CI by repo convention. Neither
  reads `plugin.json`.

## Result

7 of 7 PASS, 0 FAIL. The three commands the repo verifies with, run last,
after the regression experiment had been reverted:

```
Ran 1351 tests in 16.629s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
```

Nothing routes back to Implement. Next stage is Review.

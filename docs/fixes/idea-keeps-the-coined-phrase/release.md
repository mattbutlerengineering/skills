---
stage: ship
run: maintenance:idea-keeps-the-coined-phrase
date: 2026-10-25
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1124
---

# Release: Idea briefs keep the user's own framing

## Pre-flight

- [x] Verification green: 3 PASS, 0 FAIL, no criterion unverified; the grader-wrap caveat is recorded.
- [x] Review: no critical or major finding.
- [x] No secrets; no configuration; no migrations; no ADR added.
- [x] Protected paths: `.claude-plugin/plugin.json` untouched (ADR-0095);
      `skills/` changed, so a release PR bumps the version.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert removes one template line and one sentence.

Blast radius: Idea briefs in repos on the next plugin version. If the call
is wrong, a brief opens with a quote that is not the user's framing.

```
git checkout -b revert/idea-keeps-the-coined-phrase origin/main
git revert <merge sha of the PR>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/idea-keeps-the-coined-phrase
gh pr create --base main --body-file <body>   # "No work order:" + "Closes #N"
```

## Release log

1. Soft gate: review.md Verdict -> pass.
2. Launch demo: not run, per the Owner's standing answer this session.
3. Eval spend for #1118, authorized by the Owner in session (about $3): the
   diagnosis run cost $1.51 and the proving run $1.16, $2.67 in all.

## Post-release checks

- First live observation: the next Idea brief opens with the user's own
  framing quoted.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names.

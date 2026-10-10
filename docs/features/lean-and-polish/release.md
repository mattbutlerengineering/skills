---
stage: ship
run: feature:lean-and-polish
date: 2026-10-10
assumptions:
  - "Release authorization read from the brief: push feat/lean-and-polish-skills by name, open one anchor issue (#631) and one non-draft pull request to main whose body begins with Closes #631 and a No work order: line, poll the checks, and stop. No merge, no tag, no label. #624, #626 and #627 are neither closed nor referenced with a closing keyword."
  - "The pull request body cites this run's breakdown rows by bare number (0146 to 0148), as the docs-audit and readme-skill-map releases did, so the lifecycle legs read the body as waived. Taken without user input."
  - "The battery ran once on the tip on Python 3.14.6; CI runs it again and the result is recorded under Release log."
---

# Release: lean and polish (PRD-0011) — pushed, pull request open; merge left to the owner

Production for this repository is `main` and the installable plugin cut
from it. This release adds two utility skills, `lean` and `polish`, to
plugin version 0.5.0, with their roster entries (protocol and mirror,
plugin manifest, README table and skill-map figure, LEDGER at draft,
21 routing-eval cases) and this run directory.

## Pre-flight

- [x] Verification green — `verification.md`, every section pass; the
  routing eval and the github.com figure check are listed as owed.
- [x] Review: no defect — `review.md`, "None found".
- [x] Battery on tip `6c888f4`, Python 3.14.6:
  ```
  $ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
  Ran 2066 tests in 27.822s
  OK
  $ python3 lint.py
  lint: 0 problem(s) across 28 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- [x] Base current — `origin/main` is the merge base:
  ```
  $ git merge-base HEAD origin/main | cut -c1-7
  41f3266
  ```
- [x] No secrets in diff:
  ```
  $ git diff origin/main...HEAD | grep "^+" | grep -E -c "sk-ant-|ghp_|github_pat_|AKIA[0-9A-Z]{16}|-----BEGIN|xox[bp]-|sk_live_"
  0
  ```
- [x] No open pull request claims plugin 0.5.0 (`gh pr list --state
  open` returned none on 2026-10-10).

## Release steps

1. Push `feat/lean-and-polish-skills` by name.
2. Open one non-draft pull request to `main`, body per the protocol's
   Pull request body section, `Closes #631`.
3. Poll `gh pr checks` until done; record the result below.
4. Stop. The merge is the owner's (ADR-0033 gate 3; the pull request
   carries `prd.md` and `architecture.md`, so a human code-owner merge
   under ADR-0036).

## Rollback plan

Door: one-way-ish. The code is a revert away, but the version bump is
published the moment main moves: installed plugin caches pick up 0.5.0
with two new skills, and a revert does not un-install them from a cache
that already refreshed; a corrective release would need 0.5.1.
Blast radius: every installed copy of the plugin, which gains two
directly-invoked skills whose descriptions compete for routing with
`review`, `deepen`, `audit` and `ux-design`; a description that
over-triggers would steal those skills' asks until the routing eval
catches it. Rollback: revert the merge commit and release 0.5.1.

## Release log

- 2026-10-10: branch pushed; anchor issue #631 opened; pull request
  #632 opened non-draft against `main`. Checks on the first push:
  ```
  check	pass	24s
  needs-review-label	pass	5s
  review	pass	26s
  merged-label	skipping	0
  check	pass	28s
  ```
  Stopped here: the merge is the owner's.

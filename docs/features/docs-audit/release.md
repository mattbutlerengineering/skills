---
stage: ship
run: feature:docs-audit
date: 2026-10-10
assumptions:
  - "The brief's Release authorization was read as: push docs/docs-audit by name, open one non-draft pull request with base feat/grok-harness whose body begins with Closes #616 and a No work order: line, then stop. No merge, no gh pr ready, no tag, no version bump, no label, no new issue, no beads write. The merge is ADR-0033 gate 3 and, because the pull request carries prd.md and architecture.md, a human code-owner merge under ADR-0036."
  - "The pull request body and this file cite the run's breakdown rows by bare number (0114 through 0124 of PRD-0010) and carry no work-order id token, so the lifecycle legs read the body as a waived one (ADR-0057, ADR-0064) and detector C finds no token in this artifact; the readme-skill-map precedent (#615) stayed green this way."
  - "The pull request is stacked: its base is feat/grok-harness (#618), because #618 edits four of this run's in-scope docs. Its diff is therefore taken against origin/feat/grok-harness (a0f7553, which is #618's head at the time of shipping). After #618 squash-merges, the base must be retargeted to main; the stacked commits then rebase cleanly only if the owner retargets before deleting the feat/grok-harness branch (MEMORY's PR-stack procedure: retarget the child first)."
  - "The battery ran once on the tip in this worktree on Python 3.14.6 only; the pull request's own check job runs it again on CI's interpreter, and that result is recorded under Release log."
  - "The pairwise merge test ran against the one other open pull request not in this stack (#620, fix/reaping-test-flake): its eight paths are a fix-run directory and three test files, none of which this branch touches, and git merge-tree of the two heads exits 0."
---

# Release: documentation audit (PRD-0010) — pushed, pull request open; merge left to the owner

Production for this repository is `main` and the installable plugin cut
from it. This release is the living reference docs corrected in place:
sixteen false or stale claims fixed across `AGENTS.md`, `CLAUDE.md`,
`CONTEXT.md`, `README.md`, `docs/setup.md`, `docs/output-evals.md`,
`docs/factory/improvement-routine.md` and `evals/README.md`, plus eleven
append-only cost-ledger rows and the run directory. No code, no skill,
no template, no ADR, no mirrored file changes; `.claude-plugin/plugin.json`
stays `0.3.0`.

Branch `docs/docs-audit`, tip `9cc384e` at pre-flight (the commit adding
this file follows it), nineteen commits ahead of `origin/feat/grok-harness`
(`a0f7553`, the merge base and #618's head).

## Pre-flight

- [x] Verification green — `verification.md`: "8 PASS, 0 FAIL across
  PRD-0010's eight success criteria", Failures section `None.`
- [x] Review: no unfixed critical — `review.md` verdict "Ready to ship.
  No critical finding"; four majors fixed in `6e2a6a3`; five minors
  deferred with reasons (listed under Owner actions below).
- [x] Battery on tip `9cc384e`, Python 3.14.6:
  ```
  $ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
  Ran 1958 tests in 23.161s
  OK
  $ python3 lint.py
  lint: 0 problem(s) across 25 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  $ uptime
  10:40  up 98 days, 12:22, 6 users, load averages: 9.13 15.19 27.14
  ```
  The two load-sensitive tests `verification.md` names did not fail on
  this run.
- [x] Base current — #618's head is the merge base:
  ```
  $ git merge-base HEAD origin/feat/grok-harness | cut -c1-7
  a0f7553
  $ gh pr view 618 --json state,baseRefName,headRefOid
  OPEN main a0f7553905e93f97db571412ab35f8c88bfe8778
  ```
- [x] No secrets in diff — the diff against `origin/feat/grok-harness`,
  added lines grepped for `sk-ant-`, `ghp_`, `github_pat_`, AWS key ids,
  `-----BEGIN`, Slack and Stripe live key shapes:
  ```
  0
  ```
  No configuration is needed anywhere: the change is Markdown and
  ledger rows.
- [x] Migrations/data changes — none. Mirrored files: none touched
  (checked against `factory_init.MIRRORS` in Python), so no manifest
  regeneration is owed; `skills/`, `evals/results/`, `factory/`,
  `docs/adr/` and `.claude-plugin/` have an empty diff.
  ```
  mirrored touched: []
  ```
- [x] Pairwise against open pull requests — #620 touches no path this
  branch touches, and the two heads merge clean:
  ```
  $ git merge-tree --write-tree HEAD origin/fix/reaping-test-flake >/dev/null; echo "exit=$?"
  exit=0
  ```
- [x] Rollback plan concrete (below)

## Rollback plan

Door: two-way — every change is an in-place Markdown edit or an appended
ledger row; `git revert` of the squash commit restores each doc's prior
text, and nothing is published in between (`plugin.json` stays `0.3.0`,
so no installed plugin cache re-copies until the next bump).

Blast radius: readers of the living docs — the owner, a new contributor,
and agents that auto-load `CLAUDE.md`/`AGENTS.md`. If a correction is
wrong, a reader is misled on that one claim until it is noticed; no
check, skill, template or stamped repo changes behaviour, because no code
and no mirrored file is in the diff.

(the same call the pull request body makes under the protocol's Pull
request body section)

```
# Pull request open, unmerged: nothing is published.
gh pr close <n> --delete-branch      # #616 stays open; it closes only on merge

# After the squash merge to main: revert on a branch and merge the revert at gate 3.
git fetch origin main && git switch -c revert/docs-audit origin/main
git revert --no-edit <squash-sha>
make check
git push -u origin revert/docs-audit
gh pr create --base main --title "revert: back out the documentation audit" --body-file <body>   # No work order: a revert
gh issue reopen 616
```

## Release log

1. `git push -u origin docs/docs-audit` → (pending)
2. Pull request body written to the session scratchpad (`Closes #616`
   first, the `No work order:` line, the smallest visual, before/after
   evidence, `## Merge danger`, the attribution line last), then
   `gh pr create --base feat/grok-harness --head docs/docs-audit --body-file pr-body.md`
   → (pending)
3. `gh pr checks` on the pull-request event → (pending)

## Owner actions

1. Review the diff on the pull request (eight docs, small hunks; the run
   directory carries the evidence, `claims.md` row per claim).
2. Merge #618 first.
3. Retarget this pull request to `main` before `feat/grok-harness` is
   deleted (REST: `gh api -X PATCH repos/mattbutlerengineering/skills/pulls/<n> -f base=main`),
   let CI re-run, then squash-merge. The pull request carries `prd.md`
   and `architecture.md`, so it is a human code-owner merge (ADR-0036).
   Expected on merge: #616 closes.
4. Deferred review minors (no change on the branch; each reasoned in
   `review.md`): the doc-gardener playbook's drifted-index examples are
   partly already held by checks; LEDGER's narrative pre-change score
   for one operate routing case (0/5 versus a recorded 1/3); the
   protocol's Work-already-in-flight sentence names capture's check
   narrower than capture runs it; README's omp fallback "copy
   `skills/*`" is cwd-ambiguous; `docs/factory/costs.jsonl` is outside
   PRD-0010's literal file list (append-only, by breakdown assumption).
5. Follow-ups for Operate to seed into `docs/backlog.md` (`claims.md`
   § Follow-ups): F-1 detector I's walk does not reach `evals/`; F-2 a
   parity check holding `AGENTS.md`'s non-Beads text to `CLAUDE.md`'s;
   F-3 three LEDGER maturity cells (`capture`, `autorun`, `ux-design`)
   read draft though exercised, for a recorded graduation pass; F-4 the
   protocol's backlog reader/producer set versus four utility skills
   that read it and three that append — a contract decision (ADR-0029
   amendment or skill narrowing).
6. Review's caution: four false claims surfaced in docs recorded clean,
   so "every checkable claim is true" holds for the inventoried claims,
   not provably for every sentence.

## Post-release checks

For the owner, after the squash merge; none has run yet.

- On `main`: `make check` green (lint, gates, selftest, unittest).
- `gh issue view 616` → `CLOSED` by the merge.
- Nothing to check in the plugin cache: no version bump, so installed
  copies keep the old docs until the next bump.

## Outcome

(pending — filled after the pull request is open and its checks finish)

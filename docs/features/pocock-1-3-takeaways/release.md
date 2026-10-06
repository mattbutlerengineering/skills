---
stage: ship
run: feature:pocock-1-3-takeaways
date: 2026-10-06
assumptions:
  - "The worktree's own skills/ship/SKILL.md and skills/ship/TEMPLATE.md were followed, not the installed 0.2.0 plugin's copies: this run changed both (the rollback plan now records Door and Blast radius in the words of the protocol's new Pull request body section), and they are what this run ships."
  - "Prepare and stop, per the brief's Release authorization: no push, pull request, issue, tag, merge or publish was executed. The only network actions were a read-only git fetch origin main and read-only gh views (pr list, pr view, issue view, check-runs). Every step under Release log is written for the human operator; the verdict is prepared, not shipped."
  - "The PR body carries a No work order: line giving the real reason (the run's fourteen rows have no tracker mirror, ADR-0026) and cites the rows by bare number, departing from the orchestrator's instruction to cite the work-order ids in full. Detector B accepts either form, but ADR-0057 reads a body naming a work order that resolves to no mirrored issue as a malformed work-order PR that stays loud on both lifecycle legs: PRs #581 and #583 did that and show needs-review-label: failure and merged-label: failure on their head commits, while PR #351 (pipeline-board, the same unmirrored-run situation) stayed green with the waiver form. An id token in the body's unquoted prose can never resolve here, so the artifact tells the operator not to add one."
  - "Detector B requires a Closes #N link regardless of the waiver, this run has no issue, and the brief forbids creating one at this stage, so the release steps have the operator open a type:chore audit-anchor issue first (the #350, #580, #582 precedent) and close it from the PR. Never #178 or #181."
  - "Plugin version 0.3.0 stands: after the fetch origin/main is still 661ffc7 at 0.2.0, and feat/lean-and-polish-skills has zero commits ahead of main (its 0.3.0 bump and manifest regeneration are uncommitted working-tree edits), so no re-bump; the 0.3.1 rule is written into the release steps for the operator if that order flips before merge."
  - "The merge gate is cited as ADR-0033 gate 3 (PR merge), as breakdown.md's Note records; the brief's and PRD-0007's gate 2 wording is left as written upstream."
---

# Release: Pocock 1.3 takeaways — plugin 0.3.0 (prepared, not executed)

Production for this repo is the installable plugin: work merged to `main`,
then the version-gated cache re-copy (`claude plugin update`) delivers it
to every installed copy. The brief authorizes prepare-and-stop only, so
this artifact records the pre-flight that ran, the release steps and PR
body for the operator, and the rollback plan. The merge itself is ADR-0033
gate 3 and stays with the human.

Branch `feat/pocock-1-3-takeaways`, HEAD `836ef02`, nineteen commits ahead
of `origin/main` (`661ffc7`), range `9129d61..836ef02`. The branch's
upstream is `origin/main`, so every push below names the branch; a bare
`git push` would push to `main`.

## Pre-flight

- [x] Verification green (no unresolved failures) — `verification.md`:
  six PASS, zero FAIL across PRD-0007's six criteria plus one PASS for the
  breakdown close-out; its Failures section reads, in full, `None.` Its
  Not verified list (routing eval, a real strict YAML loader, detector B on
  a live PR event, charter replay, omp at a pinned tag) is carried into the
  post-release checks below where a check can be done after merge.
- [x] Review: no unfixed critical findings — `review.md` verdict line:
  `**Ready to ship: no critical findings, none unfixed.** Five minors and
  four nits;` the two fix-before-ship minors (operate step 6's sentence,
  work-queue item 7's fast-forward promise) each close with `- Fixed in
  09709c7.`, and `09709c7` is an ancestor of HEAD. The remaining minors
  (tab gap in the rule; gate-2 wording in three upstream artifacts;
  architecture.md's description of the `next` sentence) are deferred with
  reasons in review.md and `package.json` at `0.1.0` is flagged there as
  pre-existing drift since #89, not this release's change.
- [x] Battery on HEAD, both interpreters, each output written to the
  session scratchpad and grepped:
  ```
  $ python3 --version; python3.12 --version
  Python 3.14.6
  Python 3.12.13
  $ python3 -m unittest discover tests > unittest-314.txt 2>&1; echo "exit=$?"; grep -E '^(Ran |OK|FAILED)' unittest-314.txt
  exit=0
  Ran 1800 tests in 21.066s
  OK
  $ python3.12 -m unittest discover tests > unittest-312.txt 2>&1; echo "exit=$?"; grep -E '^(Ran |OK|FAILED)' unittest-312.txt
  exit=0
  Ran 1800 tests in 19.641s
  OK
  $ python3 lint.py > lint.txt 2>&1; echo "exit=$?"; grep -E '^lint:' lint.txt
  exit=0
  lint: 0 problem(s) across 25 skills
  $ (python3 gates.py && python3 gates.py --selftest) > gates.txt 2>&1; echo "exit=$?"; grep -E '^(gates:|selftest:)' gates.txt
  exit=0
  gates: 0 problem(s)
  selftest: ok
  $ python3 factory_init.py update-manifest; echo "exit=$?"
  factory-init: 0 problem(s)
  exit=0
  $ git status --short
  (empty: the committed manifest was already current; no .orig/.rej under factory/)
  ```
- [x] No secrets in diff; target config present — `git diff
  origin/main...HEAD` (26 files, +2077/-29) written to a scratch file; its
  added lines were grepped for AWS access-key, GitHub token (`ghp_`,
  `github_pat_`), OpenAI/Stripe/Slack key shapes, PEM private-key headers,
  and any `api_key|secret|token|password` assigned a quoted value of eight
  or more characters: `0` matches. A loose pass for the bare words
  `secret|token|password|api_key` hit only the fourteen ledger rows'
  `"tokens": 0` field, prose about work-order id tokens, and the brief's
  own "no secrets in the diff" line. The plugin needs no configuration in
  the target environment beyond the install itself.
- [x] Migrations/data changes have a tested forward path — none: the diff
  is skill and protocol text, one stdlib Python rule and its tests, the
  payload mirror and manifest, `plugin.json`, fourteen append-only ledger
  rows, and the run's own artifacts. No path in the diff is
  migration-shaped (`grep -i 'migrat|schema|\.sql$|alembic'` over
  `git diff --name-only`: no matches). `evals/` and `LEDGER.md` are
  untouched (`git diff --stat origin/main...HEAD -- evals/ LEDGER.md` is
  empty), as are the eight existing `docs/**/retro.md` and the four
  detector tools `gates.py`, `lint.py`, `trigger_eval.py`, `validator.py`.
- [x] Rollback plan concrete (commands/steps below)

### Merge-order facts

```
$ git rev-parse --short origin/main            # before fetch
661ffc7
$ git fetch origin main                        # read-only
$ git rev-parse --short origin/main            # after fetch
661ffc7
$ git log --oneline HEAD..origin/main | wc -l  # landed on main since 661ffc7
0
$ git merge-base HEAD origin/main
661ffc7                                        # the branch is a strict descendant of main
$ git merge-tree --write-tree origin/main HEAD > /dev/null; echo "exit=$?"
exit=0                                         # no conflicts
$ git ls-remote --heads origin feat/pocock-1-3-takeaways | wc -l
0                                              # branch not yet on the remote; no open PR for it
```

- `main` has not moved: `origin/main` is `661ffc7` before and after the
  fetch, so the merge is a fast-forward from main's point of view and the
  manifest committed here is the one detector E will read.
- `.claude-plugin/plugin.json` on this branch is `0.3.0` (origin/main:
  `0.2.0`); `factory/manifest.json` line 3 is `"version": "0.3.0"`; the
  two agree, which is all `lint.check_manifest` pins. `package.json` is
  `0.1.0` on both this branch and origin/main — pre-existing drift
  (review.md), not this release's change.
- The sibling worktree `feat/lean-and-polish-skills` sits at `661ffc7`
  with zero commits ahead of main; its working tree has uncommitted edits
  to `.claude-plugin/plugin.json` (also `0.3.0`), `factory/manifest.json`,
  `protocol.py` and its payload mirror, `LEDGER.md`, `README.md` and
  `evals/routing.json`, plus two untracked skills. If it lands first, this
  branch must bump to `0.3.1`, re-run `python3 factory_init.py
  update-manifest`, and resolve `protocol.py` by hand (both branches edit
  the seam and its identity mirror).
- Open PR #602 (`fix/blocked-by-fail-open`, `work_queue.py` and
  `knowledge_plane.py` with their mirrors and tests) also touches
  `factory/manifest.json`. No file overlaps this branch except the
  manifest: whichever of #602 and this PR lands later re-runs
  `python3 factory_init.py update-manifest` and commits the result before
  merging, or detector E goes red on main.
- The gate: ADR-0033 lists PRD approval (1), blueprint/ADR approval (2)
  and PR merge (3); this release's merge is gate 3, as the breakdown's Note
  and `skills/work-queue/SKILL.md` already say (ADR-0036 lets the gate-3
  reviewer be an agent; here it is the owner).

## Rollback plan

Door: two-way — `git revert` of the squash commit restores every file
(skill text, protocol section, lint rule and its payload mirror, manifest,
`plugin.json`). The one thing a revert cannot un-publish is the `0.3.0`
version already pulled by an installed copy; a revert therefore bumps to
`0.3.1` so those caches refresh instead of pinning the reverted text.

Blast radius: every installed copy of the plugin on its next update, and
every stamped repo's payload `protocol.py` on its next re-stamp (nothing in
the payload calls the new rule). Six skills' trigger text changed by one
character each, unmeasured by the routing eval by scope. No Python
behaviour changes outside one new lint rule in
`protocol.skill_frontmatter_problems`.

(the same call the PR body makes under the protocol's Pull request body
section)

```
# PR open, unmerged: nothing is published. Close it and delete the branch;
# the anchor issue stays open (it closes only on merge), so close or keep it by hand.
gh pr close <PR> --delete-branch
gh issue close <anchor> --comment "PR closed without merge; run parked at docs/features/pocock-1-3-takeaways/"

# After merge: revert the squash commit on a branch, bump past the published
# version so installed 0.3.0 caches re-copy, regenerate the manifest, re-check,
# and merge the revert at gate 3 like any other PR.
git fetch origin main && git switch -c revert/pocock-1-3-takeaways origin/main
git revert --no-edit <squash-sha>
#   plugin.json is now 0.2.0 again; an installed 0.3.0 would never re-copy a lower
#   version, so set "version": "0.3.1" in .claude-plugin/plugin.json, then:
python3 factory_init.py update-manifest
make check                                   # lint, gates, selftest, unittest
git add -A && git commit -m "revert: back out the Pocock 1.3 takeaways (bump to 0.3.1 so caches refresh)"
git push -u origin revert/pocock-1-3-takeaways
gh pr create --base main --title "revert: back out the Pocock 1.3 takeaways" --body-file <body>   # Closes a fresh type:chore anchor; No work order: a revert
gh issue reopen <anchor>                     # the run is open again

# Installed copies pick the revert up on their next update:
claude plugin update idea-to-prod@skills     # or: claude plugin uninstall idea-to-prod@skills && claude plugin install idea-to-prod@skills
```

## Release log

Nothing below has run. Each step is the exact command for the operator,
in order, with the result expected when it does run. Precondition: this
artifact is committed on the branch before step 1, so the PR carries it.

1. `git push -u origin feat/pocock-1-3-takeaways` → the branch appears on
   the remote and its upstream becomes `origin/feat/pocock-1-3-takeaways`
   (today it is `origin/main`; never run a bare `git push` before this).
   Expected: `check` and `review` run on the push; no PR legs yet.
2. `gh issue create --title "Ship pocock-1-3-takeaways (PRD-0007): plugin 0.3.0" --label type:chore --body "Audit anchor for the run's PR, closed by that PR's merge (detector B's Closes link; the run's rows have no tracker mirror, ADR-0026). Run: docs/features/pocock-1-3-takeaways/."`
   → an issue number; write it into the PR body as `#<anchor>` in both
   places. Never `#178` or `#181` (permanent gate-queue and journal
   issues).
3. Write the body below to a file with `<anchor>` substituted, then
   `gh pr create --draft --base main --head feat/pocock-1-3-takeaways --title "feat(skills): adopt the Pocock 1.3 lessons — strict-YAML descriptions, PR-body shape, environment retro (PRD-0007)" --body-file <file>`
   → a draft PR. Expected checks on open: `check` success (detector B sees
   the `No work order:` line and the `Closes #<anchor>` link),
   `review` success, `needs-review-label` success as a no-op (the body
   names no work-order id in unquoted prose, so the `--uncited skip`
   gate fires, ADR-0057/ADR-0064). If the body needs patching afterwards,
   use `gh api -X PATCH repos/mattbutlerengineering/skills/pulls/<PR> -F body=@<file>`
   (`gh pr edit` exits 1 without writing on this repo); the lifecycle leg
   does not re-run on `edited`, so get the body right on open.
4. Before merging, re-check the merge order: `git fetch origin main &&
   git log --oneline HEAD..origin/main`. If empty, merge as is. If
   `feat/lean-and-polish-skills` landed (its `plugin.json` claims
   `0.3.0`), set this branch to `0.3.1`, merge `origin/main` into the
   branch (resolve `protocol.py` and its mirror by hand), run `python3
   factory_init.py update-manifest && make check`, commit, and push the
   branch by name. If only #602 landed, merge `origin/main`, re-run
   `update-manifest`, commit, push. Then mark ready and squash-merge at
   ADR-0033 gate 3: `gh pr ready <PR>` and the merge button (or `gh pr
   merge <PR> --squash`); the squash message is the PR title. Expected on
   merge: `merged-label` success as a no-op (same gate), the anchor issue
   closes, `main` runs `check` and `digest`.
5. Post-release smoke, below.

## Pull request body (draft)

Follows the protocol's Pull request body section: detector B's lines
first, then the smallest visual, before-and-after evidence, and the
merge-danger call under its fixed heading. Operator notes: substitute
`<anchor>` in both places; do not add a work-order id token anywhere in
the body's unquoted prose — the rows are cited by bare number on purpose,
because an id that resolves to no mirrored issue reddens the
`needs-review-label` and `merged-label` legs (ADR-0057; PRs #581 and #583
show it), while the `No work order:` line satisfies detector B on its own.

````markdown
Closes #<anchor>

No work order: this PR implements work-order rows 0077 through 0090 of PRD-0007 (`docs/features/pocock-1-3-takeaways/breakdown.md`), fourteen checkboxes with no tracker mirror (ADR-0026), so no mirrored issue exists for it to close; #<anchor> is the run's audit anchor. All fourteen verified in `docs/features/pocock-1-3-takeaways/verification.md` (six PASS); review verdict ready to ship, two minors fixed in `09709c7`, the rest deferred with reasons (`review.md`); release plan in `release.md`.

## What changed

```
docs/pipeline-protocol.md                    + ## Pull request body (the one owner of the body's shape);
                                               Harness neutrality records the hand-off decision (ADR-0027 applied)
protocol.py                                  + bare-scalar description rule, three exact problem strings
factory/templates/tools/factory/protocol.py    identity mirror of the above
factory/manifest.json                          re-pinned; version 0.3.0
tests/test_protocol_frontmatter.py           + five cases, red before the rule and green after
skills/
  audit, automate, deepen, doctor,
  pipeline-board, work-queue                   description: the one unquoted ': ' becomes '; ' (one char each)
  audit, deepen, automate                      read a target repo's GLOSSARY.md beside CONTEXT.md
  next/SKILL.md                                step 5 lead sentence names the harness's loading mechanism
  operate/SKILL.md, TEMPLATE.md                step 6 Retrospect on the environment; ## Environment table
  ship/SKILL.md, TEMPLATE.md                   rollback plan records Door and Blast radius
  work-queue/SKILL.md                          worker brief: PR-body pointer, base check, tip merge
docs/factory/improvement-routine.md            PR skeleton gains ## Merge danger (first two lines unchanged)
.claude-plugin/plugin.json                     0.2.0 -> 0.3.0
docs/factory/costs.jsonl                     + fourteen owner-session $0 rows (detector G)
docs/features/pocock-1-3-takeaways/            idea, prd, architecture, breakdown, verification, review, release
```

## Before and after

The new rule run against `main`'s six descriptions (reconstructed with `git show` into a scratch tree, no checkout) and against this branch's twenty-five:

```
$ rule on origin/main's six descriptions
  skills/audit/SKILL.md description is not a bare YAML scalar: contains ': '
  skills/automate/SKILL.md description is not a bare YAML scalar: contains ': '
  skills/deepen/SKILL.md description is not a bare YAML scalar: contains ': '
  skills/doctor/SKILL.md description is not a bare YAML scalar: contains ': '
  skills/pipeline-board/SKILL.md description is not a bare YAML scalar: contains ': '
  skills/work-queue/SKILL.md description is not a bare YAML scalar: contains ': '
  offenders: 6
$ rule on HEAD's twenty-five descriptions
  offenders: 0
```

Each of the six changed by one character (`git diff origin/main --word-diff=plain -U0`, description lines only):

```
audit           [-always:-]{+always;+}
automate        [-Read-only:-]{+Read-only;+}
deepen          [-source:-]{+source;+}
doctor          [-honestly:-]{+honestly;+}
pipeline-board  [-stage:-]{+stage;+}
work-queue      [-merges:-]{+merges;+}
```

Battery on HEAD `836ef02`, Python 3.14.6 and 3.12.13:

```
Ran 1800 tests in 21.066s / OK        (python3)
Ran 1800 tests in 19.641s / OK        (python3.12)
lint: 0 problem(s) across 25 skills
gates: 0 problem(s)
selftest: ok
factory-init: 0 problem(s)            (update-manifest; git status --short empty after)
```

Not run here: the routing eval (paid, out of scope; each description moved by one punctuation character) and a real strict YAML loader in the battery (review.md checked all twenty-five with libyaml via Ruby's Psych as evidence only).

## Merge danger

Door: two-way — `git revert` of the squash commit restores every file (skill text, protocol section, lint rule and its payload mirror, manifest, `plugin.json`). The one thing a revert cannot un-publish is the `0.3.0` version already pulled by an installed copy; a revert therefore bumps to `0.3.1` so those caches refresh instead of pinning the reverted text.
Blast radius: every installed copy of the plugin on its next update, and every stamped repo's payload `protocol.py` on its next re-stamp (nothing in the payload calls the new rule). Six skills' trigger text changed by one character each, unmeasured by the routing eval by scope. No Python behaviour changes outside one new lint rule in `protocol.skill_frontmatter_problems`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
````

## Post-release checks

To run after the squash-merge; none has run yet.

- `claude plugin update idea-to-prod@skills` (or `claude plugin uninstall
  idea-to-prod@skills && claude plugin install idea-to-prod@skills`) →
  `~/.claude/plugins/installed_plugins.json` shows `"version": "0.3.0"`
  and an `installPath` ending `idea-to-prod/0.3.0` for `idea-to-prod@skills`
  (today: `0.2.0`, `gitCommitSha` `661ffc7`). The cache is version-gated:
  without the bump no re-copy happens, which is why the bump is part of
  the release.
- `grep '^description:' ~/.claude/plugins/cache/skills/idea-to-prod/0.3.0/skills/audit/SKILL.md`
  → the line reads `always;` where main's 0.2.0 copy reads `always:`; the
  `/audit` skill loads in a fresh session (the registry is snapshotted at
  session start).
- On `main` after merge: `git switch main && git pull && python3 lint.py`
  → `lint: 0 problem(s) across 25 skills`; `python3 gates.py && python3
  gates.py --selftest` → `gates: 0 problem(s)` and `selftest: ok`
  (detector E against the merged manifest).
- The PR's own `check` job on open is the first time detector B reads a
  live PR event for a body carrying `## Merge danger`; `verification.md`
  listed that under Not verified. Expected: no `B:` line in the check
  output.
- Next on-demand `python3 trigger_eval.py` run: the six reworded skills'
  routing cases are the exposure the PRD accepted; a regression there
  routes to a maintenance run, not a revert.

## Outcome

Prepared, not executed. Pre-flight is green on HEAD `836ef02` (1800 tests
`OK` on 3.14 and 3.12; `lint: 0 problem(s) across 25 skills`; `gates: 0
problem(s)`; `selftest: ok`; manifest current; no secrets; no migrations;
`main` unmoved at `661ffc7` and the branch merges without conflict).
Version `0.3.0` stands unless `feat/lean-and-polish-skills` lands first,
in which case step 4 bumps to `0.3.1`. The operator runs steps 1 to 5;
the merge is ADR-0033 gate 3. Next stage after the merge and smoke:
Operate (`retro.md`, including the new Environment table).

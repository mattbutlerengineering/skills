---
stage: ship
run: feature:readme-skill-map
date: 2026-10-07
assumptions:
  - "The brief's Release authorization was read as push the branch by name, create one plain tracking issue as the pull request's Closes anchor, open the pull request non-draft, then stop. Those three ran (push: already up to date at dccc351; issue #614; pull request #615). No merge, no gh pr ready, no tag, no version bump, no label, and nothing else on GitHub. The merge is ADR-0033 gate 3 and, because the pull request carries prd.md and architecture.md, a human code-owner merge under ADR-0036 clause 3."
  - "The anchor issue was created with no label, in the plain form of #612 rather than the type:chore form of #610, because the brief says plain and the only workflow that listens to issues fires on a label. Its title and body, and the pull request's title, are the orchestrating session's words, used verbatim; the pull request body's prose is this stage's wording within the protocol's Pull request body shape."
  - "The pull request body cites the run's rows by bare number (0091 through 0096) and carries no work-order id token anywhere, including inside code blocks, so that the lifecycle legs read it as a waived body and not as a work-order pull request naming an id that resolves to no mirrored issue (ADR-0057, ADR-0064; #611 and #613 stayed green this way, #581 and #583 went red the other way). The same rule is applied to this file: the ledger rows are described, not quoted."
  - "The frontmatter date is the local date (2026-10-07 PDT) on which every one of this run's six earlier artifacts is dated and on which the stage ran; GitHub's own timestamps on #614 and #615 read 2026-10-08 UTC. This run's brief states no date rule, unlike the one-guarded-file-read brief."
  - "The battery ran once in the worktree on Python 3.14.6 at dccc351; Python 3.12.13 was not run again here because Verify ran both interpreters at 1fed0ce, the three review commits since touch two docstrings, one comment and two PNGs, and the pull request's own check job ran the battery again on CI. The pairwise test against open pull requests ran against none, because gh pr list --state open returned zero."
  - "The screenshot and README links in the pull request body point at blob URLs on the branch, which stop resolving when the branch is deleted after the squash; after the merge the same two files live under docs/features/readme-skill-map/ on main and the README renders on the repository home page. The links were kept because the reviewer at the gate reads them now, before the merge, and that is the moment the protocol's before-and-after evidence is for."
  - "The checker's blast radius is scoped to this repository's own make check: lint.py is not in factory_init.MIRRORS (checked in Python at HEAD), the payload Makefile's own comment says structural lint has no product-repo counterpart, and no stamped repo runs it. The brief's question mark on that point is answered by the code, not by a guess."
  - "The commit that adds this file lands after the pull request was opened at dccc351, so the check results quoted under Release log are for dccc351, and the push of this file re-runs the pull-request event on the new head. That re-run's result is reported to the orchestrating session and is visible on the pull request's checks tab; this file does not quote it because it cannot contain its own commit."
---

# Release: README skill map (PRD-0008) — pushed, anchored, pull request open; merge left to the owner

Production for this repository is `main` and the installable plugin cut
from it. This release is the public README's front page: the mermaid chain
replaced by one committed, self-contained, theme-aware figure
(`docs/assets/skill-map.svg`), the sixty lines of utility prose replaced
by a thirteen-row table, and one new lint checker (`check_readme_figure`)
that keeps the figure's roster equal to `protocol.ALL_SKILLS`. No
version bump: `.claude-plugin/plugin.json` stays `0.3.0`, so installed
plugin copies see nothing until the next bump re-copies the cache.

Branch `feat/readme-skill-map`, HEAD `dccc351`, fifteen commits ahead of
`origin/main` (`e64e7de`, where the branch was cut); upstream
`origin/feat/readme-skill-map`. The brief authorizes push, one anchor
issue and the pull request, then stop; all three ran today and the merge
(ADR-0033 gate 3) stays with the owner.

## Pre-flight

- [x] Verification green (no unresolved failures) — `verification.md`:
  "7 PASS, 0 FAIL across PRD-0008's seven success criteria, plus one PASS
  for the breakdown's close-out acceptance no PRD criterion covers". Its
  Failures section reads, in full, `None.` Its Not verified list (a human
  reader; GitHub's own appearance setting for a signed-in reader; the
  figure at the home page's full README width; the routing eval and
  charter replay; detector B on a live pull-request event; a screen
  reader) is carried below: detector B on a live event is now done by
  the pull request's own check job, the home-page width is the first
  post-release check, and the rest stay with the operator or out of
  scope.
- [x] Review: no unfixed critical findings — `review.md` verdict line:
  `**Ready to ship: no critical findings, none unfixed.**` One major (the
  1.88 MB full-page screenshots, cropped to 0.72 MB) fixed in `a67fdd2`,
  one minor (lint's stale Stages-section rationale) in `1fdc9f9`, two
  nits in `203dcdd`; all three are ancestors of HEAD
  (`git merge-base --is-ancestor` for each: yes). Two minors deferred
  with reasons in `review.md` (the three filename sublabels that satisfy
  the roster line for their own stage; the substring form of the embed
  check), neither reachable by the figure as drawn. Review's Note for
  Ship — squash only, because `07ff88a` holds the uncropped captures —
  is written into the rollback plan and the pull request body.
- [x] Battery on HEAD `dccc351`, outputs in the session scratchpad and
  grepped:
  ```
  $ python3 --version
  Python 3.14.6
  $ python3 -m unittest discover tests > unittest-314.txt 2>&1; echo "exit=$?"; grep -E '^(Ran |OK|FAILED)' unittest-314.txt
  exit=0
  Ran 1944 tests in 23.948s
  OK
  $ python3 lint.py > lint.txt 2>&1; echo "exit=$?"; grep -E '^lint:' lint.txt
  exit=0
  lint: 0 problem(s) across 25 skills
  $ (python3 gates.py && python3 gates.py --selftest) > gates.txt 2>&1; echo "exit=$?"; grep -E '^(gates:|selftest:)' gates.txt
  exit=0
  gates: 0 problem(s)
  selftest: ok
  $ git status --short
  (empty)
  ```
- [x] Base current — `main` has not moved since the branch was cut:
  ```
  $ git rev-parse --short origin/main            # before fetch
  e64e7de
  $ git fetch origin main
  $ git rev-parse --short origin/main            # after fetch
  e64e7de
  $ git log --oneline HEAD..origin/main | wc -l  # landed on main since e64e7de
  0
  $ git merge-base HEAD origin/main
  e64e7de                                        # strict descendant of main
  $ git merge-tree --write-tree origin/main HEAD > /dev/null; echo "exit=$?"
  exit=0                                         # no conflicts
  ```
  So no merge of `origin/main` into the branch was needed and none was
  done; `factory/` and `docs/factory/costs.jsonl` beyond this run's six
  appended rows are untouched (`git diff main --stat -- factory/` is
  empty), so neither the manifest nor the ledger could have conflicted.
- [x] No secrets in diff; target config present — `git diff
  origin/main...HEAD` (14 files, +2404/−96, 2658 diff lines) written to a
  scratch file; its added lines grepped for `sk-ant-`, `ghp_`,
  `github_pat_`, `AKIA` plus sixteen upper-case alphanumerics,
  `-----BEGIN`, Slack and Stripe key shapes: `0` matches. A loose pass for
  `secret|password|api_key` hit one line of the brief's own prose ("no
  secret is in the diff"); the 38 hits for `token` are the SVG's design
  tokens, the six ledger rows' `"tokens": 0` field, and prose about
  work-order id tokens. The figure needs no configuration anywhere: it is
  a relative image path in a public repository, served same-origin.
- [x] Migrations/data changes have a tested forward path — none: the
  diff is the README, one SVG, one stdlib checker and its tests, six
  append-only ledger rows, two PNGs, and the run's own artifacts.
  `grep -ciE 'migrat|schema|\.sql$|alembic'` over `git diff --name-only`:
  `0`. `skills/`, `evals/`, `LEDGER.md` and `factory/` are untouched
  (`git diff --stat origin/main...HEAD -- evals/ LEDGER.md skills/` is
  empty), so no routing eval, no manifest regeneration and no maturity
  claim is in play.
- [x] Pairwise against open pull requests — `gh pr list --state open`
  returned zero pull requests (`open count: 0`), so there is nothing to
  test-merge against and no cross-PR hazard to record.
- [x] Plugin version — no bump called for. `README.md`, `lint.py`,
  `tests/test_lint.py` and `docs/assets/` are each absent from
  `factory_init.MIRRORS` (checked in Python at HEAD: the tuple holds the
  eighteen root tools, six workflows, CODEOWNERS and the Makefile, and
  none of this run's paths); `git diff main -- .claude-plugin/plugin.json`
  is empty and the file reads `"version": "0.3.0"`. The installed copy is
  `idea-to-prod@skills 0.3.0` at `e64e7de`, and its cache is a whole-repo
  copy: its `README.md` still carries the mermaid block and it has no
  `docs/assets/` directory. The figure therefore reaches installed copies
  only with the NEXT version bump, whenever that is cut; this release
  changes the public page on github.com and nothing an installed copy
  reads. Recorded under Post-release checks.
- [x] Rollback plan concrete (commands/steps below)

## Rollback plan

Door: two-way for the README, the figure and the checker — `git revert` of
the squash commit restores the mermaid chain and the prose, removes
`docs/assets/skill-map.svg`, and unregisters `check_readme_figure` with
its tests, with nothing published in between (`plugin.json` never moved,
so no installed copy has re-copied anything that a revert would have to
chase with a bump). One-way for the two screenshots: 0.72 MB of cropped
PNGs sit in `main`'s history for good once squashed, and a revert removes
them from the tree but not from every future clone. The merge must be the
project's squash — a merge commit or a rebase would also carry the 1.88 MB
uncropped captures at `07ff88a` into `main`; the squash leaves them on the
branch, unreachable from `main` once the branch is deleted (GitHub keeps
them behind `refs/pull/615/head`, which a plain clone does not fetch).

Blast radius: the public front page every adopter reads first, in both
appearance settings; and this repository's own `make check`, where the new
roster line fails any pull request that adds a skill directory without
naming it in the figure — the lean-and-polish branch is the first such
(its figure and table both need `lean` and `polish`). `lint.py` is not in
`factory_init.MIRRORS` and the payload Makefile records that structural
lint has no product-repo counterpart, so no stamped repo runs the checker.
Installed plugin copies see nothing until the next version bump, because
the cache is version-gated; if the call is wrong, nobody with an installed
copy notices until then.

(the same call the pull request body makes under the protocol's Pull
request body section)

```
# Pull request open, unmerged: nothing is published. Close it and delete the
# branch; the anchor stays open (it closes only on merge), so close it by hand.
gh pr close 615 --delete-branch
gh issue close 614 --comment "PR closed without merge; run parked at docs/features/readme-skill-map/"

# After the squash merge: revert the squash on a branch, re-check, and merge
# the revert at gate 3 like any other pull request. No version bump is needed
# unless a bump has shipped the figure to installed copies in the meantime —
# then bump past it so those caches re-copy the reverted README.
git fetch origin main && git switch -c revert/readme-skill-map origin/main
git revert --no-edit <squash-sha>
make check                                   # lint (the checker is gone with the revert), gates, selftest, unittest
git push -u origin revert/readme-skill-map
gh pr create --base main --title "revert: back out the README skill map" --body-file <body>   # Closes a fresh plain anchor; No work order: a revert
gh issue reopen 614                          # the run is open again
# The revert restores the mermaid and the prose and removes the figure, the
# checker and its tests. The two cropped screenshots leave the tree but stay
# in main's history: that is the one-way half.
```

## Release log

Steps 1 to 3 ran on 2026-10-07 (local; 2026-10-08 UTC on GitHub's clock)
under the brief's Release authorization. Steps 4 and 5 are the operator's.

1. `git push origin feat/readme-skill-map` → `Everything up-to-date`;
   `git ls-remote --heads origin feat/readme-skill-map` → `dccc351`. The
   branch was already on the remote at HEAD from Review's push; the push
   event's `check` had run and passed (run `37716326858`: `check` pass,
   `review`/`needs-review-label`/`merged-label` skipping, as a push event
   should).
2. `gh issue create --title "Ship readme-skill-map (PRD-0008): the README skill map" --body "Audit anchor for the run's PR, closed by that PR's merge (detector B's Closes link; the run's rows have no tracker mirror, ADR-0026). Run: docs/features/readme-skill-map/."`
   → https://github.com/mattbutlerengineering/skills/issues/614 ;
   `gh issue view 614` → `OPEN labels=[]`, title and body as given. Not
   #178, not #181.
3. The body was written to the session scratchpad through a quoted
   heredoc (`Closes #614` first; the `No work order:` line; `## What
   changed`; `## Before and after` with the two screenshot blob URLs, the
   README blob URL, the stand-in reader's three answers labelled anecdote,
   the checker biting in two scratch copies, and the battery; `## Merge
   danger` with Door and Blast radius; the attribution line last), checked
   offline against detector B's two patterns (`no-work-order waiver:
   True`, `closes links: ['614']`, `WO tokens: []`), then
   `gh pr create --base main --head feat/readme-skill-map --title "feat(readme): a skill map of every skill and the moment you reach for it (PRD-0008)" --body-file pr-body.md`
   → https://github.com/mattbutlerengineering/skills/pull/615 ;
   `gh pr view 615` → `OPEN draft=false feat/readme-skill-map->main
   head=dccc351`; the body as landed holds `0` work-order id tokens.
   `gh pr checks 615 --watch` on the pull-request event (run
   `37716859962`, `event=pull_request head=dccc351 conclusion=success`):
   ```
   check               pass      27s
   review              pass      28s
   needs-review-label  pass       6s   (no-op: the body names no work-order id, ADR-0057/ADR-0064)
   merged-label        skipping   0s   (fires on merge)
   ```
   The `check` job's log: `lint: 0 problem(s) across 25 skills`,
   `gates: 0 problem(s)`, `selftest: ok`, `Ran 1944 tests in 18.291s`,
   `OK`, and no `B:` line — detector B read a live pull-request event
   carrying the waiver and the anchor and found nothing, which
   `verification.md` had listed under Not verified.
4. **Operator — the merge, ADR-0033 gate 3.** Judge the figure on the
   pull request's rendered README:
   https://github.com/mattbutlerengineering/skills/blob/feat/readme-skill-map/README.md
   (both appearance settings; the file sidebar narrows this view, the
   home page after merge is wider). Then squash-merge — the button, or
   `gh pr merge 615 --squash` — and delete the branch. **Squash only**:
   a merge commit or a rebase carries the 1.88 MB uncropped captures at
   `07ff88a` into `main`. Expected on merge: #614 closes, `merged-label`
   runs as a no-op (same gate as `needs-review-label`), `main` runs
   `check` and `digest`. The pull request touches `prd.md` and
   `architecture.md`, so this is a human code-owner merge (ADR-0036
   clause 3) in any case.
5. Post-release checks, below.

## Post-release checks

For the operator, after the squash merge; none has run yet.

- The figure on the repository home page at full README width
  (https://github.com/mattbutlerengineering/skills), light and dark — the
  one width Verify could not capture because only `main` renders there.
  Expected: the loop, the router and the six cards legible without
  zooming, the dark flip inside the `<img>` as on the branch's blob view.
- On `main` after merge: `git switch main && git pull && python3 lint.py`
  → `lint: 0 problem(s) across 25 skills` with `check_readme_figure` now
  live in `CHECKERS`; `python3 gates.py && python3 gates.py --selftest` →
  `gates: 0 problem(s)` and `selftest: ok`.
- `gh issue view 614` → `CLOSED` by the merge; `gh pr checks 615` →
  `merged-label` pass.
- The plugin cache: nothing to do now. `claude plugin update
  idea-to-prod@skills` re-copies only on a version change, and this
  release makes none, so the installed `0.3.0` README keeps the mermaid
  until the next bump. After that bump, expected:
  `~/.claude/plugins/cache/skills/idea-to-prod/<next>/README.md` carries
  the `docs/assets/skill-map.svg` embed line and
  `~/.claude/plugins/cache/skills/idea-to-prod/<next>/docs/assets/skill-map.svg`
  exists.
- The lean-and-polish branch (worktree at `661ffc7`, its work still
  uncommitted) must rebase onto the merged `main` and add `lean` and
  `polish` rows to the README's utility table and a `<text>` element for
  each to the figure, or lint stops it: expected problems otherwise are
  `README.md never names skill 'lean'` and
  `docs/assets/skill-map.svg never names skill 'lean'` (and the same for
  `polish`), beside the taxonomy and LEDGER lines the existing checkers
  already print.
- Still unobserved and out of this run's scope: a human reader's
  thirty-second test (the owner's look at the gate is the first), a
  signed-in reader whose GitHub appearance is fixed opposite to their OS,
  and a screen reader against the page.

## Outcome

Shipped to the gate, cleanly: pre-flight green on HEAD `dccc351` (1944
tests `OK`; `lint: 0 problem(s) across 25 skills`; `gates: 0 problem(s)`;
`selftest: ok`; no secrets; no migrations; `main` unmoved at `e64e7de`
and the branch merges without conflict; no open pull requests to collide
with; no version bump called for). The branch is pushed, the anchor is
#614, the pull request is #615 — non-draft, base `main`, all four
pull-request checks as expected — and this stage stops there. The merge
is the owner's at ADR-0033 gate 3, squash only. Next stage after the
merge and the post-release checks: Operate (`retro.md`).

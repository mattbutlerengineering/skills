---
stage: ship
run: feature:codex-style-standards-enforcement
date: 2026-09-28
assumptions:
  - "Prepare and stop. The resume brief says 'Release authorization: none', so nothing externally visible was executed: no merge, tag, push, PR, deploy, gh mutation, plugin.json edit or plugin install/update."
  - "This file is written despite a not-ready verdict, on the caller's instruction and the prepared-not-executed precedent (docs/fixes/a-dead-cli-scores-as-a-pass/, docs/fixes/a-gate-wait-is-not-spend/). Under the protocol's artifact table its existence marks Ship complete, so `next` will route this run to Operate. The route back to Implement is manual."
  - "Version 0.3.0 is a proposal, not a decision. The skill says to version by the project's convention. The only precedent, #484, was a minor pre-1.0 bump (0.1.0 to 0.2.0) for new capability. The owner confirms the number at release time."
  - "No tag step. `git tag --list` is empty in this repo, so the convention is the plugin.json version alone."
  - "No stamped product repo was enumerated, because none lives inside this worktree. The refresh step and rollback R4 are written for 'each stamped repo, if any'."
  - "That a fresh install already receives #517 is an inference, not an observation. It rests on the marketplace clone's content and the repo's recorded version-gated update behaviour. It was not exercised, because `claude plugin` commands were out of bounds."
---

# Release: codex-style standards enforcement — plugin idea-to-prod 0.3.0 (proposed)

**Not ready. Prepared, not executed.**

- **Pre-flight verdict: not ready.** `verification.md` has three unresolved failures (criteria 8, 9 and 14). `review.md` has five majors open, each `open — needs owner decision`. The skill's rule is "never ship on a red verification — route back instead."
- **Nothing was released.** This file exists only as the prepared record. The run must go back through the owner decisions in `review.md` and then Implement, Verify and Review before any real ship. The next Ship pass rewrites this file as the executed record.
- **Orientation caveat.** By the protocol's table, this file's existence marks Ship complete, so `next` will offer Operate. That is wrong for this run. Nothing shipped, and there is nothing to operate on yet.

## What "production" means for this change

- **This repo's own gate: already live.** #517 squash-merged to `main` as 69ecd19 at 2026-09-24T03:12:16Z. `origin/main` is at 6742c9f (`git ls-remote`, this pass). Detectors K and M run on every push here and are green. There is nothing to release on this surface.
- **Installed plugin caches: not reached.** Users get skills through the installed `idea-to-prod@skills` plugin. The installed cache is `0.2.0`, last updated `2026-09-22T18:26:49.040Z`, before #517 merged:
  ```
  == 0.2.0
    "version": "0.2.0",
    standards.json: absent
    standards_index.py: absent
    review 'Load applicable standards' lines: 0
    gates.py STANDARDS-DRIFT lines: 0
  ```
  `claude plugin update` only re-copies when `.claude-plugin/plugin.json`'s version changes (the repo's recorded behaviour, and `docs/features/pipeline-board/release.md`). The version is still `0.2.0` (review Minor 7), so existing installs never receive #517.
- **Fresh installs: already exposed (inferred).** The local marketplace clone is a shallow clone of pushed `main` at 6742c9f, still labelled `0.2.0`, and it already carries #517:
  ```
  shallow: true
  standards_index.py: present
  docs/standards.json: present
  review 'Load applicable standards': 1
  .../marketplaces/skills/skills/review/SKILL.md:34:5. **Load applicable standards.** Read `../../docs/standards.json` if
  .../marketplaces/skills/skills/architect/SKILL.md:28:4. **Load applicable standards.** Read `../../docs/standards.json` if
  ```
  So a fresh install, or the force-refresh (`uninstall` then `install`), would copy #517 into a cache today. That includes Major 4's plugin-relative index path, with this repo's `docs/standards.json` bundled beside it. The version gate shields existing installs only. This was not exercised (see `assumptions:`).
- **Stamped product repos: not reached.** K, M and `standards_index.py` reach a product repo only when the owner runs `python3 factory_init.py update <repo>` from a checkout that carries them.
- **The bump ships more than this run.** It releases everything since the last bump (04c6efe, #484): 55 commits, 84 files, 6 of them under `skills/`. That includes #527 (detectors N and O, another run), whose own readiness this artifact does not assess.

## Pre-flight

- [ ] **Verification green: FAIL.** `verification.md`: "16 PASS, 3 FAIL, 1 DEFERRED, 0 not verified."
  - Criterion 9: the `CLAUDE.md#`-sourced half of the index is asserted, not verified.
  - Criterion 8: two work items' own commits left the battery red.
  - Criterion 14: the shipped selftest never fails M on `Reproduction / Evidence`.
  - Two readings there still need a human ruling: criterion 7's grandfather cutoff and criterion 8's per-commit reading.
- [ ] **Review clear: five majors open.** The soft gate itself passes: there is no critical finding, and no finding cites an `enforced` statement. Still open:
  - Major 1: detector M passes an unedited capture template.
  - Major 2: `standards_index.py update` discards a committed promotion.
  - Major 3: the `CLAUDE.md#` entries are unverified.
  - Major 4: both skills read the plugin's index, not the target repo's.
  - Major 5: enforcement status can be changed by a PR an agent may merge without the owner.
- **Battery at HEAD 6742c9f (green, run this pass).** A green battery does not make verification green.
  ```
  $ python3 -m unittest discover tests
  Ran 1793 tests in 19.850s
  OK                                   # exit 0
  $ python3 lint.py
  lint: 0 problem(s) across 25 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- [x] **No secrets in the diff.** #517 (69ecd19) is 24 files and 2482 added lines. I scanned the added lines for seven credential patterns:
  ```
  pattern AKIA[0-9A-Z]{16} -> 0 added line(s)
  pattern BEGIN [A-Z ]*PRIVATE KEY -> 0 added line(s)
  pattern gh[pousr]_[A-Za-z0-9]{20,} -> 0 added line(s)
  pattern xox[abprs]-[A-Za-z0-9-]{10,} -> 0 added line(s)
  pattern sk-[A-Za-z0-9_-]{20,} -> 0 added line(s)
  pattern eyJ[A-Za-z0-9_-]{10,}[.]eyJ -> 0 added line(s)
  pattern (postgres|mysql|mongodb)(\+srv)?://[^ ]*:[^ ]*@ -> 0 added line(s)
  ```
  - **Positive control.** Each of the first three patterns matched a planted line once, so a zero means no match rather than a blind scan.
  - **Keyword sweep** (`password|secret|token|api[_-]?key|credential`): 21 added lines. 13 are cost-ledger rows carrying `"tokens": 0`. The other 8 are prose about tokens or the name `NOT_RUN_TOKEN`. None is a credential.
  - **Full delivery range.** The whole range the bump would ship (`04c6efe..HEAD`, 8729 added lines) also scores 0 on all seven patterns.
- [ ] **Target config present: partial.**
  - #517 adds no configuration key. It touches no `factory.json`, `labels.json`, `Makefile`, workflow or CODEOWNERS. An absent `docs/standards.json` is silent under K (Verify criterion 13).
  - What is missing is the release lever itself: `.claude-plugin/plugin.json` is `0.2.0`. That bump is held behind Major 4 (steps below).
  - `factory/manifest.json` also records `"version": "0.2.0"`. No gate compares it with `plugin.json` (`gates.py` has 0 lines mentioning `version`), so the manifest must be regenerated deliberately, as #484 did.
- [ ] **Migrations / data forward path: partial.**
  - There is no schema migration. The new data file is `docs/standards.json`, and its regeneration is deterministic. Re-run this pass in a scratch clone:
    ```
    c155e7d5bc26221f8bbe9035968b403455f584b7b1fd32d49a8cfce585699711  docs/standards.json
    standards-index: 0 problem(s)
    c155e7d5bc26221f8bbe9035968b403455f584b7b1fd32d49a8cfce585699711  docs/standards.json
    ```
  - **Known broken, latent:** Major 2. The regeneration tool silently discards a committed promotion, so the first real promotion (the backlog seed that revisits WO-0064) has no working forward path until that is fixed.
  - **Stamped repos:** `update` creates `tools/factory/standards_index.py`, and an absent index stays silent. M checks every brief dated on or after 2026-09-21 in that repo, so a brief captured there before the refresh fails loudly (review Minor 3(b)). A fresh stamp is covered by `test_stamped_repo_passes_its_own_gates`. An update over an existing brief corpus is not tested.
- [x] **Rollback plan concrete.** It is written out below. Each command sequence was rehearsed in a scratch `git clone` of this worktree at 6742c9f.

## Release steps (prepared, not executed)

### Blocking, in this order, before any release step

1. **Owner rulings.** The owner rules on `review.md`'s five majors and on Verify's two interpretive calls (criteria 7 and 8).
2. **Implement pass.**
   - Major 1, with Minor 4 (which is Verify criterion 14).
   - Major 2, with Minor 1.
   - Major 4: prose in `skills/review/SKILL.md` and `skills/architect/SKILL.md`.
   - Major 3, by the owner's route: (a) a K anchor check, or (b) reword PRD-0004's criterion.
   - Every `gates.py` edit is mirrored, so each one is followed by `python3 factory_init.py update-manifest`.
3. **Major 5.** Either an owner-authored change to ADR-0036's gate-change list, or an explicit recorded acceptance of the risk. Anything under `docs/adr/**` is a human code-owner merge.
4. **Re-run the stages.** Re-run Verify, then Review. Ship proceeds only when `verification.md` has no unresolved failure and `review.md` has no open major.

### Release (owner-executed, once 1–4 are done)

5. Branch from fresh `main` and confirm Major 4's fix is in:
   ```
   git fetch origin
   git switch -c chore/plugin-0.3.0 origin/main
   grep -n 'standards.json' skills/review/SKILL.md skills/architect/SKILL.md
   # stop if either line still reads ../../docs/standards.json (Major 4 unfixed)
   ```
6. Bump the version. This is BSD/macOS `sed`; GNU `sed` takes `-i` with no `''`.
   ```
   sed -i '' 's/"version": "0.2.0"/"version": "0.3.0"/' .claude-plugin/plugin.json
   git diff .claude-plugin/plugin.json          # exactly one line changed
   ```
7. Regenerate the manifest so it records the new version:
   ```
   find factory/templates \( -name '*.orig' -o -name '*.rej' \) -print   # must print nothing
   find factory/templates -name __pycache__ -type d -prune -exec rm -rf {} +
   python3 factory_init.py update-manifest
   git diff --stat        # expect .claude-plugin/plugin.json and factory/manifest.json only
   ```
8. Run the battery:
   ```
   python3 -m unittest discover tests && python3 lint.py && python3 gates.py && python3 gates.py --selftest
   ```
9. Re-scan the full delivery range for secrets, since the fix commits will have joined it. Every line must end `-> 0`.
   ```
   for p in 'AKIA[0-9A-Z]{16}' 'BEGIN [A-Z ]*PRIVATE KEY' 'gh[pousr]_[A-Za-z0-9]{20,}' \
            'xox[abprs]-[A-Za-z0-9-]{10,}' 'sk-[A-Za-z0-9_-]{20,}' 'eyJ[A-Za-z0-9_-]{10,}[.]eyJ' \
            '(postgres|mysql|mongodb)(\+srv)?://[^ ]*:[^ ]*@'; do
     echo "$p -> $(git diff 04c6efe..HEAD | grep -E '^[+]' | grep -cE "$p")"
   done
   ```
10. Commit, push and open the PR:
    ```
    git add .claude-plugin/plugin.json factory/manifest.json
    git commit -m "chore(plugin): bump idea-to-prod to 0.3.0"
    git push -u origin chore/plugin-0.3.0
    gh pr create --title "chore(plugin): bump idea-to-prod to 0.3.0" --body-file <body.md>
    ```
    The PR body needs a `No work order:` declaration (detector B), because the bump has no breakdown row. It should not say `Closes #448`: that issue is already `CLOSED COMPLETED`, closed at 2026-09-24T03:12:17Z by #517's merge.
11. **Merge.** A non-authoring reviewer re-executes the battery on the PR (ADR-0036 clause 2), then a human merges (ADR-0033 gate 3). The bump touches no `docs/adr/**`, so clause 3 does not additionally apply.

### Propagation (after the merge)

12. On every machine with the plugin installed:
    ```
    claude plugin marketplace update skills
    claude plugin update idea-to-prod@skills
    # if the cache does not move to 0.3.0:
    claude plugin uninstall idea-to-prod@skills && claude plugin install idea-to-prod@skills
    ```
    Then start a fresh session, because skills register at session start.
13. For each stamped product repo, if any, run the refresh from a checkout at the merged bump:
    ```
    python3 factory_init.py update <path-to-product-repo>
    make -C <path-to-product-repo> check
    ```
    - Read the make-target report and M's lines. A brief dated on or after 2026-09-21 that lacks sections fails there (Minor 3(b)). Fill it in, or record the owner's call.
    - Commit the refresh as a single commit in that repo, so R4 below is one revert.

## Post-release checks (prepared, not run)

- `grep -h '"version"' ~/.claude/plugins/cache/skills/idea-to-prod/0.3.0/.claude-plugin/plugin.json` → `"version": "0.3.0",`
- `grep -c 'Load applicable standards' ~/.claude/plugins/cache/skills/idea-to-prod/0.3.0/skills/review/SKILL.md` → `1`. The 0.2.0 cache shows `0` today.
- `grep -n 'standards.json' ~/.claude/plugins/cache/skills/idea-to-prod/0.3.0/skills/{review,architect}/SKILL.md` → the target-repo path from Major 4's fix, never `../../docs/standards.json`.
- `python3 -B ~/.claude/plugins/cache/skills/idea-to-prod/0.3.0/gates.py --selftest` → `selftest: ok`
- **Live smoke test.** In a repo that has its own `docs/standards.json`, run the review skill. Its findings must cite that repo's slugs, not this repo's four.
  - It costs money, so it runs only with the owner's authorisation.
  - It is the only check that exercises Major 4's fix where users get it. Verify recorded all four prose surfaces as never exercised live.

## Rollback plan

Every sequence below was rehearsed in a scratch `git clone` of this worktree at 6742c9f. The worktree itself was never touched.

**R0: now.** Nothing was executed, so nothing needs undoing. One exposure is already live, though (see "Fresh installs" above). Until Major 4 is fixed, do not use the force-refresh (`uninstall` then `install`), the documented workaround for a stale cache. It would pull #517's plugin-relative index path into the cache.

**R1: the bump PR is open, not merged.**
```
gh pr close <bump-pr> --delete-branch
```

**R2: the bump is merged, and the skill or charter prose misbehaves** (for example, the index is read from the wrong place).
- Roll forward, never back. `claude plugin update` re-copies only on a changed version, and republishing `0.2.0` is not a documented way to downgrade.
- So reverse only the prose hunks and bump to `0.3.1`. Newest first: the Major 4 fix's prose hunks, then #517's:
```
git fetch origin && git switch -c fix/plugin-0.3.1-rollback origin/main
git show --format= <major4-fix-sha> -- skills/review/SKILL.md skills/architect/SKILL.md | git apply -R --check
git show --format= <major4-fix-sha> -- skills/review/SKILL.md skills/architect/SKILL.md | git apply -R
git show --format= 69ecd19 -- skills/review/SKILL.md skills/review/TEMPLATE.md \
  skills/architect/SKILL.md skills/architect/TEMPLATE.md \
  factory/charters/reviewer/CHARTER.md factory/charters/architect/CHARTER.md | git apply -R --check
git show --format= 69ecd19 -- skills/review/SKILL.md skills/review/TEMPLATE.md \
  skills/architect/SKILL.md skills/architect/TEMPLATE.md \
  factory/charters/reviewer/CHARTER.md factory/charters/architect/CHARTER.md | git apply -R
sed -i '' 's/"version": "0.3.0"/"version": "0.3.1"/' .claude-plugin/plugin.json
find factory/templates -name __pycache__ -type d -prune -exec rm -rf {} +
python3 factory_init.py update-manifest
python3 -m unittest discover tests && python3 lint.py && python3 gates.py && python3 gates.py --selftest
git add skills/review/SKILL.md skills/review/TEMPLATE.md skills/architect/SKILL.md \
  skills/architect/TEMPLATE.md factory/charters/reviewer/CHARTER.md \
  factory/charters/architect/CHARTER.md .claude-plugin/plugin.json factory/manifest.json
git commit -m "revert(skills): withdraw the standards-loading step; bump to 0.3.1"
git push -u origin fix/plugin-0.3.1-rollback        # then PR and human merge, as steps 10-11
claude plugin marketplace update skills && claude plugin update idea-to-prod@skills
```
Rehearsal against today's tree:
- `git apply -R --check` on #517's hunks exited 0 and changed 6 files (+20 / −51).
- #527's `[NEEDS CLARIFICATION]` line in `skills/architect/TEMPLATE.md` survived.
- The battery stayed green: `Ran 1793 tests ... OK`, `lint: 0 problem(s) across 25 skills`, `gates: 0 problem(s)`, `selftest: ok`.
- Use the reverse-apply, never `git checkout 69ecd19^ -- <files>`. #527 edited `skills/architect/TEMPLATE.md` after #517, and a checkout would drop that edit too.
- The Major 4 fix will change these files, so re-run both `--check` lines at rollback time.

**R3: K or M misfires in this repo.** A plain `git revert 69ecd19` is not a rollback here:
- At 6742c9f it conflicts in six files:
  ```
  CONFLICT (content): Merge conflict in docs/adr/README.md
  CONFLICT (content): Merge conflict in docs/factory/costs.jsonl
  CONFLICT (content): Merge conflict in docs/features/codex-style-standards-enforcement/breakdown.md
  CONFLICT (content): Merge conflict in factory/manifest.json
  CONFLICT (content): Merge conflict in factory/templates/tools/factory/gates.py
  CONFLICT (content): Merge conflict in gates.py
  ```
- `gates.py` and its payload copy have 6 hunks each, because #527's N and O build on K and M's roster lines and cutoff pattern.
- It would also delete ADR-0073 and the ADR-0004 and ADR-0032 back-fills, against the repo's rule to supersede ADRs rather than rewrite them.

The tested lever unwires the two detectors and leaves their code in place:
```
git fetch origin && git switch -c fix/unwire-k-m origin/main
sed -i '' \
  -e 's/check_staleness, check_standards_drift, check_capture_completeness,/check_staleness,/' \
  -e 's/^    "K": ("STANDARDS-DRIFT", "gates.py", "offline"),/    "K": (None, None, "unused"),/' \
  -e 's/^    "M": ("CAPTURE-COMPLETENESS", "gates.py", "offline"),/    "M": (None, None, "unused"),/' \
  gates.py
find factory/templates -name __pycache__ -type d -prune -exec rm -rf {} +
python3 factory_init.py update-manifest
python3 -m unittest discover tests && python3 lint.py && python3 gates.py && python3 gates.py --selftest
```
Rehearsal results:
- It changed 3 files: `gates.py`, its payload copy, and the manifest. `Ran 1793 tests ... OK`, `lint: 0 problem(s)`, `gates: 0 problem(s)`, `selftest: ok`.
- Dropping only the `CHECKERS` entries is not enough. It fails `test_no_roster_entry_claims_a_letter_no_checker_owns`, so the `DETECTORS` rows must go back to `unused` too.
- The roster docstring still names K and M afterwards, which is a follow-up.
- If a released plugin version carried K and M, bump and propagate as in R2.

**R4: a stamped product repo misbehaves after the refresh.** `update` overwrites `tools/factory/` and the `factory/` mirror together, and step 13 commits them as one refresh commit:
```
git -C <path-to-product-repo> revert --no-edit <factory-refresh-sha>
make -C <path-to-product-repo> check
```

**R5: the index is damaged by a regeneration** (Major 2's lost promotion). `docs/standards.json` is committed data:
```
git checkout <last-good-sha> -- docs/standards.json
python3 gates.py
```
If an ADR changed since that commit, K then reports drift. That is Major 2 itself, and no rollback fixes it.

## Release log

Nothing was released. This pass ran:
- read-only checks in the worktree;
- read-only `gh issue view`, `gh pr view` and `git ls-remote` queries;
- reads of the installed plugin cache and the marketplace clone;
- rollback rehearsals in a scratch clone under the session scratchpad, deleted afterwards.

Hiccups, recorded as they happened:

1. **First secrets scan did not run.** The combined seven-pattern regex was rejected by the shell's `grep` (ugrep: "exceeds complexity limits", exit 2). I re-ran it as seven separate patterns plus the positive control quoted above.
2. **First unit-test run was misread.** The exit code captured was `tail`'s, and the tail showed stray test output instead of the summary. I re-ran it with the log captured: `Ran 1793 tests`, `OK`, exit 0.
3. **Stray revert in the scratch clone.** During rehearsal, a command-composition slip ran an extra `git revert --no-commit 69ecd19` there. `git reset --hard` cleared it before the prose reverse-apply was tested. The worktree was not involved.
4. **Ancestry check said "no".** The marketplace clone's check for 69ecd19 returned "no" because the clone is shallow (`shallow: true`, object absent). I checked its content directly instead.

## Outcome

**Not shipped.** The pre-flight verdict is not ready: verification is red and five review majors are open. The route is the owner's rulings in `review.md`, then Implement (Majors 1, 2 and 4, Major 3 by the owner's route, and Minors 1 and 4 alongside), then Verify, then Review, then Ship again. The version bump comes after Major 4's fix, never before.

## Surfaced for the owner

- **Orientation.** This file makes `next` route the run to Operate. The route back to Implement has to be started by hand.
- **Fresh-install exposure.** Major 4's plugin-relative index path is already reachable through a fresh install or the force-refresh, because the version gate protects only existing caches. Holding the bump does not hold that path back.
- **Version number.** 0.3.0 is proposed from #484's precedent. Confirm it, or pick another, at step 6.
- **Issue #448.** It closed `COMPLETED` at #517's merge. Its acceptance #4 is deferred and Verify criteria 8, 9 and 14 fail. Whether to reopen it is the owner's call.
- **omp packaging.** `package.json`, the second-harness packaging, is still `0.1.0` and was not bumped at 0.2.0 either. Whether it follows `plugin.json` is a convention question this release does not settle.
- **#527.** The bump also ships detectors N and O from another run. That run's own readiness was not assessed here.

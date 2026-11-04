---
stage: verify
run: maintenance:a-rename-the-merge-train-may-not-see
date: 2026-11-04
assumptions: []
---

# Verification: a rename the merge train may not see

Re-verification after the fix loop. Review found two majors; the Owner's
answers fixed them in commit `4024915` ("Fix now" for non-ASCII gate paths,
"Ship REST default" for the `changed-files` default). The first Verify pass
(commit `d0ccebe`) is kept below where it still holds and refreshed where
`4024915` changed what it checked.

## Summary

17 criteria (the brief's Success criteria and the work items' Accept lines,
overlaps merged): 16 PASS, 1 FINDING (the harness-neutral check, below, not
counted as a pass), 0 FAIL. Fail-closed roll-up: three items are unknown or
NOT RUN and are not counted as passes: (1) the GitHub MCP file-list tool's
rename behaviour (unavailable to this run; the profile's refusal to treat it
as a source is verified as text only); (2) the 3000-file cap of the REST
endpoint (not exercised: the largest PR tested has 129 files, so the count
check is verified on a list that matches, not on a truncated one); (3) a live
train run that follows the profile's hook (prose contract only). The two new
criteria, an unquoted non-ASCII or quote-bearing gate path and the REST
default with its count check, each have quoted evidence from an independent
repro. The new real-git tests are red on the pre-fix `fast_path.py` and
green on the fix (`Ran 35 tests ... OK`). `python3 run_tests.py`,
`python3 -m unittest tests.test_fast_path`, `lint.py`, `kb.py drift`,
`gates.py` and `gates.py --selftest` all pass. Finding, not a pass:
`skills/implement-queue/SKILL.md` contains concrete `gh`/`git` commands, and
`4024915` added one more (the REST default row, by the Owner's choice).

## Criteria & evidence

### A gate-path file with a non-ASCII or quote-bearing name is refused with its real path (work item 7)

- Check: fresh temp git repo (`main` holds `notes.txt`, `.github/workflows/validator.yml`, `docs/adr/0001-x.md`); one branch per case adds `docs/adr/0999-café.md`, `.github/workflows/é.yml`, and `docs/adr/0998-a"b.md`. Ran the worktree's `python3 fast_path.py gate main <branch>` and the classifier `python3 fast_path.py main <branch>`.
- Evidence (post-fix, `fast_path.py` at HEAD):
  ```
  == adr
  gate-paths: human (docs/adr/0999-café.md)
  gate exit 1
  fast-path: review (docs/adr/0999-café.md)
  class exit 1
  == wf
  gate-paths: human (.github/workflows/é.yml)
  gate exit 1
  fast-path: review (.github/workflows/é.yml)
  class exit 1
  == quote
  gate-paths: human (docs/adr/0998-a"b.md)
  gate exit 1
  fast-path: review (docs/adr/0998-a"b.md)
  class exit 1
  ```
  Why the old read was wrong, from the same repo:
  ```
  $ git diff --name-only --no-renames main...adr
  "docs/adr/0999-caf\303\251.md"
  $ git diff --name-only -z --no-renames main...quote | tr '\0' '|'
  docs/adr/0998-a"b.md|
  ```
  The same `adr` case against the pre-fix file (`git show 4024915^:fast_path.py`) in a fresh repo:
  ```
  gate-paths: clear
  exit 0
  fast-path: review ("docs/adr/0999-caf\303\251.md")
  exit 1
  ```
  Reproduces review's major exactly: `gate` read the path as `clear` (exit 0), and the classifier named git's quoted string, not the path.
- Result: PASS

### The new tests fail against the pre-fix `fast_path.py`

- Check: `git archive HEAD` extracted to a temp dir, `fast_path.py` replaced by `git show 4024915^:fast_path.py`, tests run there.
- Evidence, the three behavioural reds (run alone):
  ```
  FAIL: test_a_non_ascii_gate_path_in_real_git_is_human (tests.test_fast_path.TestGateMode...)
  AssertionError: Tuples differ: (0, 'gate-paths: clear\n') != (1, 'gate-paths: human (.github/workflows/é.yml)\n')
  FAIL: test_a_non_ascii_gate_path_is_review_with_the_real_path (tests.test_fast_path.TestRealGit...)
  AssertionError: Tuples differ: (1, 'fast-path: review ("docs/adr/0999-caf\\303\\251.md")\n') != (1, 'fast-path: review (docs/adr/0999-café.md)\n')
  FAIL: test_a_quote_in_a_gate_path_is_review_with_the_real_path (tests.test_fast_path.TestRealGit...)
  AssertionError: Tuples differ: (1, 'fast-path: review ("docs/adr/0998-a\\"b.md")\n') != (1, 'fast-path: review (docs/adr/0998-a"b.md)\n')
  Ran 3 tests in 0.452s
  FAILED (failures=3)
  ```
  The whole module against the pre-fix file: `Ran 35 tests in 3.781s` / `FAILED (failures=35)`. That count is inflated and is not the evidence: the tests' `DIFF` constant now holds the `-z` args, so every test that fakes git output or pins the diff args also fails on the old file. The three above fail on behaviour in real git. On the fix: `Ran 35 tests in 2.743s` / `OK`.
- Result: PASS

### A PR that renames a gate-path file into an ungated path is refused, naming the old path (exit 1) (re-confirmed at `4024915`)

- Check: fresh temp repo (`main` holds `.github/workflows/validator.yml`); branch `ren` does `git mv .github/workflows/validator.yml docs/validator.yml`; `python3 fast_path.py gate main ren` and the classifier.
- Evidence:
  ```
  == ren
  gate-paths: human (.github/workflows/validator.yml)
  gate exit 1
  fast-path: review (.github/workflows/validator.yml)
  class exit 1
  ```
- Result: PASS

### A plain ungated edit is still accepted (`clear`, exit 0) (re-confirmed)

- Check: branch `plain` appends a line to `notes.txt`.
- Evidence:
  ```
  == plain
  gate-paths: clear
  gate exit 0
  fast-path: review (notes.txt)
  class exit 1
  ```
  The classifier's `review` here is its existing rule (a path outside `docs/` is reviewed); `gate` is the consent source and reads `clear`.
- Result: PASS

### Edge cases: a rename into a gate path, an empty diff, a bad ref (re-run at `4024915`)

- Check: separate temp repo; branch `into` does `git mv notes.txt .github/workflows/notes.yml`; branch `empty` is `main` with no commit; `gate main nope`.
- Evidence:
  ```
  == into
  gate-paths: human (.github/workflows/notes.yml)
  exit 1
  == empty
  gate-paths: human (empty diff)
  exit 1
  == nope
  fast-path: git diff --name-only -z --no-renames main...nope failed: 'git <command> [<revision>...] -- [<file>...]'
  exit 2
  ```
  The bad-ref problem string now carries `-z`, as the diff args do.
- Result: PASS (empty diff fails closed by design; the bad ref prints the `fast-path:` problem string the profile says to read as a human gate)

### The skill's `changed-files` default is the REST list with a count check, and a mismatch fails closed (work item 8)

- Check: read the skill's hook-default table row and Phase 3 paragraph at HEAD; then ran the skill's command literally against PR #247 (a PR with 19 renames and 129 files, merged 2026-08-11): `gh api repos/mattbutlerengineering/skills/pulls/247/files --paginate` (exit 0) and `gh api repos/mattbutlerengineering/skills/pulls/247 --jq .changed_files`; parsed the paginated output (concatenated JSON arrays).
- Evidence, the skill text:
  ```
  | `changed-files`  | `gh api repos/{owner}/{repo}/pulls/<N>/files --paginate`: every `filename` plus every `previous_filename`; its length must equal `gh api repos/{owner}/{repo}/pulls/<N> --jq .changed_files`, else fail closed |
  With no hook the default in the table above applies: the
  REST file list, whose length is checked against the PR's `changed_files`
  count. A list that reports only a rename's destination, a list whose
  length differs from that count (the endpoint stops at 3000 files and
  flags no truncation), a list the source capped or paged short, ...
  all fail closed: the PR needs a human merge.
  ```
- Evidence, the command:
  ```
  exit 0
  changed_files 129
  files 129
  previous_filename 19
  old absent from filename set 19
  renamed factory/skills/pm/SKILL.md -> factory/charters/pm/CHARTER.md
  renamed tests/test_factory_gates.py -> tests/test_gates.py
  ```
  The file count (129) equals `changed_files` (129), so the count check passes on this PR; `previous_filename` gives 19 old paths, all 19 absent from the `filename`-only set, so reading it is what exposes them.
- Result: PASS for the text and the matching-count case. A list that is short of `changed_files` (the 3000-file cap) was not exercised; see Not verified.

### The skill, the profile and the routine name the same source and agree

- Check: read the skill's row and paragraph, the profile's `## changed-files` section, and the routine's §2/§3 lines (unchanged by `4024915`); `python3 -m unittest tests.test_fast_path` includes the pin test.
- Evidence:
  ```
  skill:   REST `pulls/<N>/files --paginate`, every `filename` plus every `previous_filename`; length must equal `... pulls/<N> --jq .changed_files`, else fail closed; no hook -> this default
  profile: local `python3 fast_path.py gate origin/main HEAD` (reads `git diff --name-only -z --no-renames`); no checkout -> `gh api repos/{owner}/{repo}/pulls/<N>/files --paginate`, "Take every `filename` **and** every `previous_filename`"; length must equal `gh api repos/{owner}/{repo}/pulls/<N> --jq .changed_files`; "A different length (the endpoint stops at 3000 files and flags no truncation) fails closed"; an MCP file-list tool "is not a source until a run records that it reports `previous_filename`"
  routine: "the profile's `changed-files` hook, never another source: a rename's old path counts, a partial list fails closed"
  ```
  The profile keeps its `fast_path.py gate` hook and the same REST command and count check as the skill; the routine defers to the profile. `Ran 35 tests ... OK` includes `test_the_skill_profile_and_routine_name_one_changed_files_source`, which per `defect.md` now pins `**both**`, `fail closed`, `pulls/<N>/files --paginate`, `filename`, `previous_filename` and `changed_files` in the skill and the profile.
- Result: PASS

### Failing tests first: red before the fix, green after (the regression test, first fix commit)

- Check (first pass, `d0ccebe`): extracted `git archive` of that commit, replaced `fast_path.py` with `git show d0ccebe^:fast_path.py`, ran its tests. This pass did not re-run it; the first pass's quoted run stands, and the file it tested is the one `4024915^` builds on. The current tests (35) are green at HEAD; the red run for the second-pass tests is the criterion above.
- Evidence (first pass, quoted):
  ```
  Ran 32 tests in 1.265s
  FAILED (failures=7)
  gate-paths: human (.github/workflows/validator.yml)   # on the fix, exit 1
  ```
  All 7 reds were in `TestGateMode`: the pre-fix tree had no `gate` mode (usage text, exit 2).
- Result: PASS

### The skill names the source and requires rename sources; a partial list fails closed

- Check: the skill's table row and paragraph at HEAD (full quote under the REST criterion); `python3 lint.py` (below).
- Evidence:
  ```
  list holds every file the PR changes, and a rename or move counts as **both** its old path and its new one
  A list that reports only a rename's destination, ... an empty list for a PR that changes files, and a source that failed or is unavailable all fail closed: the PR needs a human merge.
  ```
  The prose no longer calls `none` the default (the earlier row did).
- Result: PASS

### The routine's changed-path wording does not leave the source open

- Check: `docs/factory/merge-train-routine.md` §2 steps 1 and 3 and §3 human-gate bullet (not edited by `4024915`).
- Evidence:
  ```
  hook, never another source: a rename's old path counts, a partial
  list fails closed), review state ...
  - **human gate** — changes a `gate_paths` file (a rename counts by its
    old path as well as its new one; a changed-file list that is partial,
    or a `changed-files` hook that fails, is a human gate too) ...
  ```
- Result: PASS

### The profile's remote source yields a rename's old paths (PR #247)

- Check: the REST criterion above, same command; recorded here as the remote-source line of the profile.
- Evidence (from that run):
  ```
  files 129
  previous_filename 19
  old absent from filename set 19
  ```
  The first pass's 148-path union (129 + 19) is consistent with it.
- Result: PASS

### The skill text stays harness-neutral: no concrete CLI command in `skills/implement-queue/SKILL.md`

- Check: grep of the lines `4024915` added to the skill for a backticked `gh`, `git` or `python3` command; the first pass grepped the whole file and the first fix commit.
- Evidence:
  ```
  $ git show 4024915 -- skills/implement-queue/SKILL.md | grep -E '^\+' | grep -E '`(gh|git|python3)'
  +| `changed-files`  | `gh api repos/{owner}/{repo}/pulls/<N>/files --paginate`: every `filename` plus every `previous_filename`; its length must equal `gh api repos/{owner}/{repo}/pulls/<N> --jq .changed_files`, else fail closed |
  grep exit 0
  ```
  The first pass's grep over `d0ccebe`'s added lines was empty; the file already holds pre-existing commands (`gh run list`, `gh issue edit`, `git fetch origin`, `gh pr checks`, `gh pr merge`, `gh pr update-branch`, REST twins).
- Result: FINDING, not a clean pass. Read literally, the claim "no concrete CLI command appears in the skill" is false of the file, and `4024915` now adds one more, deliberately: the Owner chose "Ship REST default", the option that puts the command in the skill so a consumer without a hook gets a usable source. This follows the table's own convention (the other defaults are commands) and review's second major named it as the fix. Not a regression to route to Implement; whether any neutrality rule is intended is a question for a later seed.

### ADR only if the test holds (`defect.md` Notes)

- Check: `defect.md` Notes carry two lines saying why the protocol's test does not hold (the first pass's, and the 2026-11-04 line for the consumer default); `git show --stat 4024915` lists four files, none under `docs/adr/`.
- Evidence:
  ```
  - 2026-11-04: No ADR for the consumer-default change. The protocol's test
    needs all three legs; the first fails: the default is a table row and
    a paragraph in a skill file, reversible by one edit ...
  .claude/implement-queue.md | skills/implement-queue/SKILL.md | fast_path.py | tests/test_fast_path.py
  ```
- Result: PASS (the Accept line allows a line in Notes; the judgement is the Implement stage's and is not re-derived here)

### Backlog line 144 is claimed

- Check: `git show --stat d0ccebe` and the marker on line 144 (not touched by `4024915`).
- Evidence:
  ```
   docs/backlog.md                     |  2 +-
  (claimed: maintenance:a-rename-the-merge-train-may-not-see)
  ```
- Result: PASS

### `python3 run_tests.py`

- Check: ran at load average 7.80 (`uptime` before), 12.18 after the remaining checks. Passed on the first run, so no re-run was needed.
- Evidence:
  ```
  tests: 3989 tests across 126 modules in 28.3s on 8 workers, 0 problem(s)
  ```
- Result: PASS

### `python3 -m unittest tests.test_fast_path`

- Evidence:
  ```
  Ran 35 tests in 1.868s

  OK
  ```
- Result: PASS

### `python3 lint.py`, `python3 kb.py drift`, `python3 gates.py && python3 gates.py --selftest`

- Evidence (this run, at `f705cf2`, before the commit of this artifact):
  ```
  lint: 0 problem(s) across 35 skills
  drift: 0 problem(s)
  gates: 0 problem(s)
  selftest: ok
  ```
  Detector E: no mirrored file changed (`fast_path.py`, the skill, the profile and the routine are root-only per `defect.md`), so `update-manifest` was not needed. The final `gates.py` run, after this artifact is written, is in the hand-off.
- Result: PASS

## Failures

none that route back to Implement. One finding, kept visible: the skill file holds concrete CLI commands, and the second fix added one by the Owner's choice (see the harness-neutral criterion). Earlier first-pass note kept: the regression's docs-pin test is green on a pre-fix copy by construction.

## Not verified

- The GitHub MCP file-list tool's report for a rename: NOT RUN, unknown. No MCP tool was available. The profile says it is not a source until a run records `previous_filename`; only that text was checked.
- The 3000-file cap and a list shorter than `changed_files`: NOT RUN, unknown. PR #247 (129 files) is the largest case queried; the count check was verified on a matching list only. That a truncated list actually differs in length from `changed_files` rests on GitHub's documented cap, not on an observation here.
- A live train run: none was exercised. The `gate` mode and the REST list were tested directly; that the train agent follows the skill's default and the profile's hook is a prose contract pinned by tests on the text, not observed behaviour.
- The first pass's `d0ccebe^` red run (`failures=7`) was not re-run in this pass; the second-pass red run (3 behavioural failures) is quoted above.
- The `defect.md` claim that no renames occurred in merged PRs since the train's first run (108 PRs) was not re-run; only PR #247 was re-queried.
- Non-ASCII and quote handling was verified for `docs/adr/`, `.github/workflows/` and a `"` in a name; backslash, newline and other control-character names were not run (`-z` lists them raw by construction; the tests do not cover them).

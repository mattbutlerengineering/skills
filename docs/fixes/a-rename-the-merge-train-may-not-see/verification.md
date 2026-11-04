---
stage: verify
run: maintenance:a-rename-the-merge-train-may-not-see
date: 2026-11-03
assumptions: []
---

# Verification: a rename the merge train may not see

## Summary

14 criteria (the brief's Success criteria and the work items' Accept lines, overlaps merged): 13 PASS, 1 FINDING (the harness-neutral check, below, not counted as a pass), 0 FAIL. One further item is unknown and NOT RUN: the GitHub MCP file-list tool's rename behaviour (unavailable to this run, so the profile's refusal to treat it as a source is verified as text only). The regression is red on the pre-fix `fast_path.py` (`FAILED (failures=7)`) and green on the fix (`Ran 32 tests ... OK`). `python3 run_tests.py`, `lint.py`, `kb.py drift`, `gates.py` and `gates.py --selftest` all pass. Finding, not a pass: `skills/implement-queue/SKILL.md` as a whole does contain concrete `gh`/`git` commands (the pre-existing hook-default table and its REST twins); the lines this fix added contain none, and the new `changed-files` default is "none". Also unverified: the gate runs inside a real train run; no train run was exercised (see "Not verified").

## Criteria & evidence

### A PR that renames a gate-path file into an ungated path is refused, naming the old path (exit 1)

- Check: fresh temp git repo (`main` holds `.github/workflows/validator.yml` and `notes.txt`); branch `ren` does `git mv .github/workflows/validator.yml docs/validator.yml`; the worktree's `python3 fast_path.py gate main ren`. Also the bare local diff for contrast.
- Evidence:
  ```
  == ren
  gate-paths: human (.github/workflows/validator.yml)
  exit 1
  == bare diff
  $ git diff --name-only main...ren
  docs/validator.yml
  ```
- Result: PASS

### A plain ungated edit is still accepted (`clear`, exit 0)

- Check: branch `plain` appends a line to `notes.txt`.
- Evidence:
  ```
  == plain
  gate-paths: clear
  exit 0
  ```
- Result: PASS

### Edge cases: a rename into a gate path, an empty diff, a bad ref

- Check: branch `into` does `git mv notes.txt .github/workflows/notes.yml`; branch `empty` is `main` with no commit; `gate main nope`.
- Evidence:
  ```
  == into
  gate-paths: human (.github/workflows/notes.yml)
  exit 1
  == empty
  gate-paths: human (empty diff)
  exit 1
  == badref
  fast-path: git diff --name-only --no-renames main...nope failed: 'git <command> [<revision>...] -- [<file>...]'
  exit 2
  ```
- Result: PASS (empty diff fails closed by design, since it cannot be told from a failed read; the bad ref prints the `fast-path:` problem string the profile says to read as a human gate)

### Failing tests first: red before the fix, green after (the regression test)

- Check: extracted `git archive HEAD` to a temp dir, replaced `fast_path.py` with `git show d0ccebe^:fast_path.py`, ran `python3 -m unittest tests.test_fast_path` (the fix commit's tests); then ran the same on this tree.
- Evidence:
  ```
  pre-fix:
  FAIL: test_a_failed_git_exits_2_with_a_problem_string (tests.test_fast_path.TestGateMode...)
  FAIL: test_a_gate_path_among_ungated_ones_is_human (tests.test_fast_path.TestGateMode...)
  FAIL: test_an_edit_to_an_ungated_file_in_real_git_is_clear (tests.test_fast_path.TestGateMode...)
  FAIL: test_an_empty_list_fails_closed (tests.test_fast_path.TestGateMode...)
  FAIL: test_a_plain_edit_to_an_ungated_file_is_clear (tests.test_fast_path.TestGateMode...)
  FAIL: test_a_rename_out_of_a_gate_path_in_real_git_is_human (tests.test_fast_path.TestGateMode...)
  FAIL: test_the_same_diff_args_as_the_classifier_are_used (tests.test_fast_path.TestGateMode...)
  AssertionError: Tuples differ: (2, 'usage: python3 fast_path.py <base> <h[110 chars]d\n') != (1, 'gate-paths: human (.github/workflows/[13 chars])\n')
  Ran 32 tests in 1.265s
  FAILED (failures=7)

  fix:
  Ran 32 tests in 1.314s

  OK
  ```
  The pre-fix tree has no `gate` mode, so main prints the usage text with exit 2. The 32nd test (skill, profile and routine name one source) reads the docs at HEAD and so passes in the pre-fix copy; the 7 reds are the `TestGateMode` cases, including the real-git rename.
- Result: PASS

### The skill names the source and requires rename sources; a partial list fails closed

- Check: `git show d0ccebe -- skills/implement-queue/SKILL.md`, the added Phase 3 paragraph and the `gate_paths` and `changed-files` rows.
- Evidence:
  ```
  | `gate_paths` ... | A PR changing a match, old path of a rename included, always needs a human merge ...
  | `changed-files`  | none: no `gate_paths` check can pass, so under `merge: auto` every PR needs a human merge
  **The changed-file list.** The `gate_paths` check reads one source, the
  `changed-files` hook, and only that source. Its list holds every file
  the PR changes, and a rename or move counts as **both** its old path and
  its new one ... A list that reports only a rename's destination, a list the
  source capped or paged short, a list read in part, an empty list for a
  PR that changes files, and a source that failed or is unavailable all
  fail closed: the PR needs a human merge.
  ```
  `python3 lint.py` output is under the full-gate criterion.
- Result: PASS

### The profile and routine name the same source as the skill

- Check: grep for `changed-files`, `fast_path.py gate` and `pulls/` across the three files.
- Evidence:
  ```
  skills/implement-queue/SKILL.md:54:| `changed-files`  | none: no `gate_paths` check can pass, ...
  skills/implement-queue/SKILL.md:199:- changes a file `gate_paths` matches, judged on the `changed-files`
  skills/implement-queue/SKILL.md:203:`changed-files` hook, and only that source. ...
  .claude/implement-queue.md:57:## changed-files
  .claude/implement-queue.md:59:    python3 fast_path.py gate origin/main HEAD
  .claude/implement-queue.md:74:    gh api repos/{owner}/{repo}/pulls/<N>/files --paginate
  docs/factory/merge-train-routine.md:55:   `hold_labels`, `gate_paths`, and the `fast-path`, `changed-files`,
  docs/factory/merge-train-routine.md:61:   labels, changed paths against `main` (the profile's `changed-files`
  docs/factory/merge-train-routine.md:85:  or a `changed-files` hook that fails, is a human gate too), or carries
  ```
  All three point at the profile's `changed-files` hook (skill: the hook name; routine: "the profile's `changed-files` hook, never another source"; profile: the command). `tests.test_fast_path` pins the three to one source and is green.
- Result: PASS

### The profile's remote source (`gh api .../pulls/<N>/files --paginate`) yields a rename's old paths (PR #247)

- Check: ran `gh api repos/mattbutlerengineering/skills/pulls/247/files --paginate` (the profile's command with `{owner}/{repo}` filled), exit 0; collected every `filename` and every `previous_filename`.
- Evidence:
  ```
  files 129
  renamed 19
  filename+previous set 148 previous_filename count 19
  renamed factory/skills/architect/SKILL.md -> factory/charters/architect/CHARTER.md
  renamed factory/skills/planner/SKILL.md -> factory/charters/planner/CHARTER.md
  renamed factory/skills/pm/SKILL.md -> factory/charters/pm/CHARTER.md
  old paths in set: True old absent from filename-only: 19
  ```
  129 files, 19 renames, 148 distinct paths (129 + 19 old ones); all 19 old paths are in the union and all 19 are absent from the `filename`-only set, so taking `previous_filename` is what exposes them. `--paginate` returned all 129 (a count above the 100 cap that `gh pr view --json files` stops at, per `defect.md`).
- Result: PASS

### The skill text stays harness-neutral: no concrete CLI command in `skills/implement-queue/SKILL.md`

- Check: grep of the file for `gh `, `git `, `python3 `; and of the lines the fix commit added for a backticked command.
- Evidence:
  ```
  43:| `preflight`      | `gh run list --branch main --limit 5` ...
  44:| `transition`     | `gh issue edit` swapping the state labels ...
  46:| `base-freshness` | `git fetch origin` and confirm ...
  49:| `ci-status`      | `gh pr checks <N>` plus the presence check below
  52:| `merge-command`  | `gh pr merge <N> --auto --squash --delete-branch`
  53:| `update-branch`  | `gh pr update-branch <N>`
  68-78: REST twins (`gh api -X POST repos/{owner}/{repo}/issues/<N>/labels ...`)
  97/100: `gh issue list ...`, `gh api 'repos/{owner}/{repo}/issues?...'`
  175: Snapshot `git status --porcelain` before each reviewer dispatch ...

  $ git show d0ccebe -- skills/implement-queue/SKILL.md | grep -E '^\+' | grep -E '`(gh|git|python3)'
  (no match; grep exit 1)
  ```
- Result: FINDING, not a clean pass. Read literally, the file does contain concrete CLI commands, so the claim "no concrete CLI command appears in the skill" is false of the file. What holds: the fix added none (the grep over its added lines is empty), the new Phase 3 paragraph and the `changed-files` row name the hook, not a command, and the commands for this source live in the profile. The commands above predate this run (hook defaults and their REST twins). Recorded in Failures as a finding; it does not route to Implement.

### The routine's changed-path wording does not leave the source open

- Check: `git show d0ccebe -- docs/factory/merge-train-routine.md`, §2 steps 1 and 3, §3 human-gate bullet.
- Evidence:
  ```
  `gate_paths`, and the `fast-path`, `changed-files`,
  labels, changed paths against `main` (the profile's `changed-files`
  hook, never another source: a rename's old path counts, a partial
  list fails closed), review state ...
  - **human gate** — changes a `gate_paths` file (a rename counts by its
    old path as well as its new one; a changed-file list that is partial,
    or a `changed-files` hook that fails, is a human gate too) ...
  ```
- Result: PASS

### ADR only if the test holds (`defect.md` Notes)

- Check: `defect.md` Notes carry a line saying why the protocol's test does not hold, and no ADR was added by the fix commit (`git show --stat d0ccebe` lists six files, none under `docs/adr/`).
- Evidence:
  ```
  - 2026-11-03: No ADR. The protocol's test needs all three legs; this
    fails them: a hook name plus a `fast_path.py` mode is easy to reverse, ...
  ```
- Result: PASS (the Accept line allows "a line in Notes saying why the test does not hold"; the judgement itself is the Implement stage's, and is not re-derived here)

### Backlog line 144 is claimed

- Check: `git show --stat d0ccebe` for the diffstat; `sed -n 144p docs/backlog.md | grep -o '(claimed:[^)]*)'`.
- Evidence:
  ```
   docs/backlog.md                     |  2 +-
  (claimed: maintenance:a-rename-the-merge-train-may-not-see)
  ```
- Result: PASS (one line changed, and line 144 carries the marker)

### `python3 run_tests.py`

- Check: ran at load average 5.13 (`uptime` before), 10.02 after the remaining checks.
- Evidence:
  ```
  tests: 3986 tests across 126 modules in 27.2s on 8 workers, 0 problem(s)
  ```
- Result: PASS

### `python3 -m unittest tests.test_fast_path`

- Evidence:
  ```
  Ran 32 tests in 1.314s

  OK
  ```
- Result: PASS

### `python3 lint.py`, `python3 kb.py drift`, `python3 gates.py && python3 gates.py --selftest`

- Evidence:
  ```
  lint: 0 problem(s) across 35 skills
  drift: 0 problem(s)
  gates: 0 problem(s)
  selftest: ok
  ```
  Detector E: no mirrored file changed (`fast_path.py`, the skill, the profile and the routine are root-only per `defect.md`), so `update-manifest` was not needed, and `gates.py` reporting `0 problem(s)` covers E on this tree. This run re-ran `gates.py` before the commit; the final run is in the hand-off.
- Result: PASS

## Failures

none that route back to Implement. One finding, kept visible: the skill file as a whole holds concrete CLI commands (see the harness-neutral criterion). It is pre-existing hook-default text, not added by this fix. Whether the neutrality rule should reach those defaults is a question for Review or a later seed, not a regression of this run.

## Not verified

- The GitHub MCP file-list tool's report for a rename: NOT RUN, unknown. No MCP tool was available. The profile says it is not a source until a run records `previous_filename`; only that text was checked.
- A live train run: none was exercised. The `gate` mode and the REST list were tested directly; that the train agent follows the profile's `changed-files` hook is a prose contract pinned by tests on the text, not observed behaviour.
- The Implement stage's own load note (a clean suite at load average 6.63) was not re-derived; this run's suite is the one quoted.
- The pre-fix red run used the fix commit's tests and docs with only `fast_path.py` swapped, so the docs-pin test is green there by construction.
- The `defect.md` claim that no renames occurred in merged PRs since the train's first run (108 PRs) was not re-run; only PR #247 was re-queried.

---
stage: verify
run: feature:pr-body-preflight
date: 2026-10-16
assumptions:
  - "Run unattended under autorun; no live interview. The criteria list is the PRD's seven success criteria plus the breakdown's acceptance points not already covered by one (dual-membership pin, VERBS row, no skills/ or plugin.json change, not in factory_init.MIRRORS, settings.local.json untouched)."
  - "End-to-end hook evidence is produced by a scratchpad harness (outside the repo, deleted with the session) that reads the exact command string from .claude/settings.json and runs it through /bin/sh with CLAUDE_PROJECT_DIR set and a synthetic PreToolUse JSON payload on stdin. The work-order token used in the synthetic passing bodies is built at runtime so this artifact carries no literal four-digit token (detector C scans it)."
  - "False-block hunt sample: the 60 most recently merged PRs (gh pr list --state merged --limit 60, PRs #868 to #985, merged 2026-10-14 to 2026-10-17 UTC), each replayed in three shapes: the quoted-delimiter heredoc the brief names, a single-quoted literal --body (shlex.quote), and a relative --body-file. The brief asked for at least 30; 60 was the cheap superset. 'B accepts' is judged by gates.pr_body_problems on the body as the API returns it."
  - "A control run was added that the brief did not name: each sampled body with its closing tokens stripped (knowledge_plane.CLOSES_TOKEN.sub) must be refused through the heredoc form with exactly B's strings. Without it, 120 silent exits could mean 'judged and passed' or 'never judged'."
  - "The live-session refusal was observed with the false && form only; a bare gh pr create was never run, per the brief."
  - "Re-verify 2026-10-16: the false-block hunt reuses the same 60-body sample saved by the first verify (scratchpad merged.json, fetched read-only from gh) rather than re-fetching, so the before/after comparison is over identical bodies. No newer merge was added."
  - "Re-verify 2026-10-16: the compound-command evidence now uses `cd docs && gh pr create …` from the repository cwd. The first verify's `cd <tmp> && …` leaves the checkout, and the review fix loop made that fail open by the Owner's decision, so it no longer demonstrates a judged compound command."
  - "Re-verify 2026-10-16: Review's `cd ../eat-sheet` reproduction was rerun as written. On this machine /Users/mbutler/github/eat-sheet is a plain directory, not a git checkout, so a second case cds into a real sibling checkout with a different remote (../car-search) to show the other-checkout arm."
  - "Re-verify 2026-10-16: each transcript-replay exit 2 is confirmed as a body B rejects by extracting the quoted-delimiter heredoc from the command, rendering it through /bin/bash's own cat, and passing the output to gates.pr_body_problems. Commands are never executed whole (they include git push)."
  - "Re-verify 2026-10-16: hook latency, which the first verify left unmeasured, was timed through the registered command (20 runs each) as a cheap extra, not as a criterion."
---

# Verification: PR-body preflight hook

> **Re-verify, 2026-10-16, after the review fix loop.** The first verify
> (commit `4ddd443`, same date) passed 7 of 7 criteria against the code as
> it stood before Review: 0 false blocks over 180 runs on 60 real merged
> bodies, one coverage observation (single-quoted bodies holding `$` or a
> backtick fail open). Review then found two criticals, both false blocks
> the first verify's shapes did not exercise: a plain heredoc body or a
> comment tail parsed as a command, and an unquoted heredoc body with a
> backslash-newline (fixed in `eacc548`). It also found one major: a PR
> aimed at another repository was judged by this repository's rule.
> Implement fixed the first critical and the major in `8189351`
> (architecture.md steps 2b and 8, breakdown Milestone 3). Everything
> below was re-run against HEAD `2329d23` and describes the current code.

## Summary

7 of 7 PRD success criteria PASS on the current code, plus the
breakdown's remaining acceptance points, Milestone 3 included. Review's
reproductions all exit 0 now. Shell text that never runs gets the `saw
"gh pr create" but found no such command` note. Another repository or a
`cd` out of the checkout gets a target note. A same-repository `-R`, in
any spelling or case, still refuses a failing body. False-block hunt:
the same 60 real merged bodies, 180 hook runs, **0 refusals**. The
control was refused 60 of 60 with B's exact strings. Transcript replay:
9,096 historical Bash commands gave **2 exit 2s**. Both are real
`gh pr create` runs whose bodies B also rejects, the same two as before
the fix. The four CI checks are green with 3,284 tests. Verdict: ready
for Review's re-check.

## Criteria & evidence

Unless stated otherwise, hook evidence below comes from the registered
command, read from `.claude/settings.json`:

```
[ ! -f "$CLAUDE_PROJECT_DIR/pr_body_preflight.py" ] || python3 "$CLAUDE_PROJECT_DIR/pr_body_preflight.py"
```

It runs through `/bin/sh -c` with `CLAUDE_PROJECT_DIR=/Users/mbutler/github/skills`
and a payload `{"tool_name": "Bash", "tool_input": {"command": ...}, "cwd": ...}`
on stdin. The cwd is the repository unless a case says otherwise.
`GH_REPO` is unset in the harness environment except where a case sets
it.

### 1. A readable failing body is refused: exit 2, B's own strings on stderr

- Check: a literal `--body` missing each line, and one missing both; `-F`
  with a real failing file; a failing quoted-delimiter heredoc body; a
  compound command that stays in the checkout.
- Evidence (re-run 2026-10-16):
  ```
  --- 3 missing work-order line
  exit=2
  stderr: B: PR body cites no work-order id
  stderr: pr-body-preflight: the body contract is docs/kb/pr-body-contract.md
  --- 4 missing closing line
  exit=2
  stderr: B: PR body has no Closes #N link
  stderr: pr-body-preflight: the body contract is docs/kb/pr-body-contract.md
  --- 5 both missing
  exit=2
  stderr: B: PR body cites no work-order id
  stderr: B: PR body has no Closes #N link
  stderr: pr-body-preflight: the body contract is docs/kb/pr-body-contract.md
  --- 7 -F real failing file (absolute)
  exit=2
  stderr: B: PR body cites no work-order id
  stderr: B: PR body has no Closes #N link
  stderr: pr-body-preflight: the body contract is docs/kb/pr-body-contract.md
  --- 9 heredoc quoted delimiter, failing
  exit=2
  stderr: B: PR body cites no work-order id
  stderr: B: PR body has no Closes #N link
  stderr: pr-body-preflight: the body contract is docs/kb/pr-body-contract.md
  --- 10 compound cd docs && gh pr create, failing (cwd=repo)
  exit=2
  stderr: B: PR body cites no work-order id
  stderr: B: PR body has no Closes #N link
  stderr: pr-body-preflight: the body contract is docs/kb/pr-body-contract.md
  ```
  The same-repository arm of the new target check still refuses (see
  "Review's reproductions" below for `-R`, `--repo=`, a URL, an empty
  `GH_REPO=` and `GH_REPO` in the hook's environment).
  Live session: the hook is active in this re-verifying session. Running
  `false && gh pr create --body "x"` (gh can never execute) was refused
  by the Claude Code harness:
  ```
  PreToolUse:Bash hook error: [[ ! -f "$CLAUDE_PROJECT_DIR/pr_body_preflight.py" ] || python3 "$CLAUDE_PROJECT_DIR/pr_body_preflight.py"]: B: PR body cites no work-order id
  B: PR body has no Closes #N link
  pr-body-preflight: the body contract is docs/kb/pr-body-contract.md
  ```
- Result: PASS

### 2. A body B accepts passes (exit 0), and so does every non-`gh pr create` command

- Check: a passing literal body (work-order token form and `No work
  order:` form); a passing `--body-file` (relative, resolved against the
  payload cwd); a passing heredoc body holding inner `"` and `'`; a
  passing compound command; a non-gh command; `echo "gh pr create"`; and,
  new at re-verify, shell text that only mentions `gh pr create`.
- Evidence (re-run 2026-10-16):
  ```
  --- 1 passing literal --body
  exit=0
  --- 2 passing No-work-order body
  exit=0
  --- 6 --body-file real passing file (relative, cwd=tmp)
  exit=0
  --- 8 heredoc quoted delimiter, passing
  exit=0
  --- 11 compound cd docs && gh pr create, passing (cwd=repo)
  exit=0
  --- 15 non-gh command
  exit=0
  --- 16 echo mentioning gh pr create
  exit=0
  stderr: pr-body-preflight: not checked — saw "gh pr create" but found no such command
  ```
  Live session: this heredoc file write, whose body holds a failing
  `gh pr create` line, ran without a refusal:
  ```
  $ cat > <scratchpad>/v2/live-heredoc.txt <<'EOF'
  Example:
    gh pr create --title x --body "WIP"
  EOF
  $ cat <scratchpad>/v2/live-heredoc.txt
  Example:
    gh pr create --title x --body "WIP"
  ```
  Real bodies: see the false-block hunt below (0 refusals in 180 runs).
- Result: PASS

### 3. Unreadable bodies and unparseable commands fail open with a one-line note

- Check: `--fill`, `--fill-first`, `--web`, `--editor`, `--body-file -`,
  a `$VAR` body, a missing body file, an unclosed quote, and the
  registration guard. `--template`, `--recover`, flag clusters, a raising
  owner, a stdin read failure, an unclosed `$(` and a `<<` with no word
  are covered by the replay tests (criterion 5).
- Evidence (re-run 2026-10-16):
  ```
  --- 12 --fill
  exit=0
  stderr: pr-body-preflight: not checked — --fill leaves the body to gh
  --- 12b --fill-first
  exit=0
  stderr: pr-body-preflight: not checked — --fill-first leaves the body to gh
  --- 13 --web
  exit=0
  stderr: pr-body-preflight: not checked — --web leaves the body to gh
  --- 13b --editor
  exit=0
  stderr: pr-body-preflight: not checked — --editor leaves the body to gh
  --- 14 --body-file -
  exit=0
  stderr: pr-body-preflight: not checked — --body-file - reads the body from stdin
  --- 17 unparseable (unclosed quote)
  exit=0
  stderr: pr-body-preflight: not checked — cannot parse the command: No closing quotation
  --- 18 $VAR in body
  exit=0
  stderr: pr-body-preflight: not checked — the body holds $ or a backtick the hook cannot expand
  --- 19 missing body file
  exit=0
  stderr: pr-body-preflight: not checked — no body file at /nonexistent/nope.md
  --- 21 guard: script absent
  exit=0
  ```
  Case 21 runs the same registered command with `CLAUDE_PROJECT_DIR`
  pointed at an empty temp directory, so there is no script.
- Result: PASS

### 4. The check's patterns have one owner; the hook delegates to B

- Check: grep counts of the regex definitions and B's problem strings
  across tracked non-test Python (excluding `factory/templates/`); the
  hook's references and imports; the delegation test; `one_owner.py`.
- Evidence (re-run 2026-10-16):
  ```
  == 'cites no work-order id'
  gates.py:1
  gates_selftest.py:1
  validator.py:1
  == 'has no Closes #N link'
  gates.py:1
  validator.py:1
  == 'NO_WO_DECLARATION ='
  gates.py:1
  == 'WO_TOKEN ='
  knowledge_plane.py:1
  == 'CLOSES_TOKEN ='
  knowledge_plane.py:1
  -- hook references:
  9:owner gates.pr_body_problems, before the PR exists.
  570:        problems = gates.pr_body_problems(body)
  -- hook imports (top level):
  import json / import os / import re / import shlex / import sys / from pathlib import Path
  -- hook imports (lazy): import cli (lines 384, 440, 472), import gates (line 556)
  ```
  The `gates_selftest.py` and `validator.py` hits predate this branch, as
  the first verify showed: a selftest assertion on B's output, and
  detector V's own `V: ...` strings. The fix loop's import changes
  (`git diff 4ddd443 HEAD`) are `+import os` and two more lazy
  `import cli` sites. The hook still imports only the standard library,
  `gates` and `cli`, as Milestone 3 requires.
  Delegation test (patches `gates.pr_body_problems` to a sentinel):
  ```
  test_a_raising_owner_fails_open (tests.test_pr_body_preflight.TestOneOwner.test_a_raising_owner_fails_open) ... ok
  test_the_hook_judges_through_gates (tests.test_pr_body_preflight.TestOneOwner.test_the_hook_judges_through_gates)
  B's one owner, not a copy: a sentinel from the patched owner ... ok
  ```
  `python3 one_owner.py` prints `one-owner: 9 problem(s)`. A grep of its
  output for `pr_body|WO_TOKEN|CLOSES_TOKEN|work-order id|Closes #N`
  counts `0`.
- Result: PASS

### 5. A replay test covers the required fixture shapes

- Check: `python3 -m unittest tests.test_pr_body_preflight -v`. The
  module grew from 42 tests (first verify) to 62.
- Evidence (excerpt of the new Milestone 3 classes; full module green):
  ```
  test_a_comment_after_a_real_command_does_not_hide_it (…TestTextTheShellNeverRuns…) ... ok
  test_a_comment_line_is_not_a_command (…TestTextTheShellNeverRuns…) ... ok
  test_a_heredoc_inside_a_substitution_hides_its_body (…TestTextTheShellNeverRuns…) ... ok
  test_a_heredoc_with_no_delimiter_line_hides_the_rest (…TestTextTheShellNeverRuns…) ... ok
  test_a_real_command_after_a_heredoc_is_still_judged (…TestTextTheShellNeverRuns…) ... ok
  test_every_heredoc_operator_spelling_hides_its_body (…TestTextTheShellNeverRuns…) ... ok
  test_lookalikes_of_a_heredoc_are_not_heredocs (…TestTextTheShellNeverRuns…) ... ok
  test_a_cd_inside_this_repository_is_still_judged (…TestOtherRepository…) ... ok
  test_a_cd_out_of_this_repository_fails_open (…TestOtherRepository…) ... ok
  test_a_cd_the_hook_cannot_place_fails_open (…TestOtherRepository…) ... ok
  test_a_named_repository_with_no_remote_to_compare_fails_open (…TestOtherRepository…) ... ok
  test_a_repo_flag_naming_another_repository_fails_open (…TestOtherRepository…) ... ok
  test_a_worktree_shares_its_clones_remotes_and_checkout (…TestOtherRepository…) ... ok
  test_gh_repo_naming_another_repository_fails_open (…TestOtherRepository…) ... ok
  test_main_reads_gh_repo_from_its_environment (…TestOtherRepository…) ... ok
  test_naming_this_repository_is_still_judged (…TestOtherRepository…) ... ok
  test_unquoted_delimiter_with_a_backslash_fails_open (…TestHeredoc…) ... ok
  test_dash_heredoc_strips_leading_tabs (…TestHeredoc…) ... ok
  ...
  Ran 62 tests in 0.161s
  OK
  ```
  The end-to-end harness above independently covers each PRD-named shape
  (a passing body, each missing line, `--body-file` with a real file, a
  heredoc, a compound command, `--fill`, a non-gh command) through the
  real registration.
- Result: PASS

### 6. The hook is registered in the checked-in `.claude/settings.json` as a PreToolUse hook on Bash

- Check: file contents; whether `settings.local.json` changed on the
  branch.
- Evidence (re-read 2026-10-16, unchanged by the fix loop):
  ```
  "PreToolUse": [ { "matcher": "Bash", "hooks": [ { "type": "command",
    "command": "[ ! -f \"$CLAUDE_PROJECT_DIR/pr_body_preflight.py\" ] || python3 \"$CLAUDE_PROJECT_DIR/pr_body_preflight.py\"",
    "timeout": 10 } ] } ]
  $ git diff --name-only main...HEAD | grep -c settings.local
  0
  ```
  The live-session refusal under criterion 1 shows the registration loads.
- Result: PASS

### 7. The four CI checks pass

- Evidence (re-run 2026-10-16 at HEAD `2329d23`, clean tree):
  ```
  tests: 3284 tests across 106 modules in 14.6s on 8 workers, 0 problem(s)
  run_tests exit=0
  lint: 0 problem(s) across 34 skills
  lint exit=0
  drift: 0 problem(s)
  drift exit=0
  gates: 0 problem(s)
  selftest: ok
  gates chain exit=0
  ```
  `gates chain` is `python3 gates.py && python3 gates.py --selftest`.
- Result: PASS

### Breakdown acceptance points not covered above

- Check: plugin version and skills untouched (ADR-0095); hook not
  mirrored; dual-membership pin and `factory.VERBS` row; Milestone 3's
  replay rule (no exit 2 that B would not give, none on a command whose
  `gh pr create` never runs).
- Evidence:
  ```
  $ git diff --stat main...HEAD -- skills/ .claude-plugin/plugin.json | wc -l
         0
  $ grep -c pr_body_preflight factory_init.py
  0
  ```
  The dual-membership pin (`tests/test_dual_membership.py`) and the
  verb-table pins (`tests/test_factory_cli.py`) are inside the passing
  3,284-test run. Milestone 3's replay rule is shown under "Transcript
  replay" below.
- Result: PASS

## Review's reproductions (the fix loop's targets)

- Check: each Review reproduction through the registered command, as
  written in review.md, plus the same-repository cases that must still
  refuse.
- Evidence (2026-10-16):
  ```
  ## Review finding 1 reproductions
  --- R1 cat > notes.md <<'EOF' body holding a failing gh line
  exit=0
  stderr: pr-body-preflight: not checked — saw "gh pr create" but found no such command
  --- R2 git commit -F - <<'EOF'
  exit=0
  stderr: pr-body-preflight: not checked — saw "gh pr create" but found no such command
  --- R3 cat <<'EOF' > x with an assignment-prefixed line
  exit=0
  stderr: pr-body-preflight: not checked — saw "gh pr create" but found no such command
  --- R4 word-start comment
  exit=0
  stderr: pr-body-preflight: not checked — saw "gh pr create" but found no such command
  --- R4b comment, Implement's tightened fixture
  exit=0
  stderr: pr-body-preflight: not checked — saw "gh pr create" but found no such command
  ## Review finding 2 (eacc548): backslash-newline in an unquoted heredoc
  --- R5 unquoted heredoc, Closes \<newline>#12
  exit=0
  stderr: pr-body-preflight: not checked — an unquoted heredoc body holds $, a backtick or a backslash
  ## Review finding 3: other repositories
  --- R6 -R other/repo
  exit=0
  stderr: pr-body-preflight: not checked — the PR targets mattbutlerengineering/eat-sheet, not this repository
  --- R7 GH_REPO=other/repo prefix
  exit=0
  stderr: pr-body-preflight: not checked — the PR targets other/repo, not this repository
  --- R8 cd ../eat-sheet &&
  exit=0
  stderr: pr-body-preflight: not checked — a cd before gh pr create leaves this repository
  --- R9 cd ../elsewhere (no such directory) &&
  exit=0
  stderr: pr-body-preflight: not checked — a cd before gh pr create the hook cannot place
  --- R10 cd ../car-search (another real checkout) &&
  exit=0
  stderr: pr-body-preflight: not checked — a cd before gh pr create leaves this repository
  --- R11 GH_REPO=other/repo in the hook's own environment
  exit=0
  stderr: pr-body-preflight: not checked — the PR targets other/repo, not this repository
  ## Same repository still judged
  --- S1 -R mattbutlerengineering/skills, failing body
  exit=2
  stderr: B: PR body cites no work-order id
  stderr: B: PR body has no Closes #N link
  stderr: pr-body-preflight: the body contract is docs/kb/pr-body-contract.md
  --- S2 --repo=MattButlerEngineering/Skills, failing body
  exit=2
  (same three lines)
  --- S3 -R https://github.com/mattbutlerengineering/skills, failing
  exit=2
  (same three lines)
  --- S4 GH_REPO= (empty) prefix, failing
  exit=2
  (same three lines)
  --- S5 heredoc with apostrophe, then failing gh pr create
  exit=2
  (same three lines)
  --- S6 GH_REPO=mattbutlerengineering/skills in the hook's environment, failing
  exit=2
  (same three lines)
  ```
  The repository's remote is
  `git@github.com:mattbutlerengineering/skills.git`, so S1 to S3 also show
  the scp-to-slug normalisation and case-insensitive compare. S5 is the
  case that made Review's 61 `No closing quotation` parses: an apostrophe
  in a heredoc body. It no longer hides the real command after it.
- Result: PASS. Every reproduction that was an exit 2 now exits 0 with a
  note, and no same-repository refusal was lost.

## False-block hunt (the PRD's top risk)

- Check: the 60 merged PR bodies the first verify fetched read-only
  (`gh pr list --state merged --limit 60 --json number,body,mergedAt`,
  PRs #868 to #985). Each body is judged by `gates.pr_body_problems`.
  Each one B accepts is wrapped as
  `gh pr create --title t --body "$(cat <<'EOF'` / body / `EOF` / `)"`
  (the delimiter is lengthened if the body holds an `EOF` line), as
  `--body '<body>'` via `shlex.quote`, and as `--body-file b<N>.md`
  relative to the payload cwd. Each is then run through the registered
  command.
- Evidence (re-run 2026-10-16 against the fixed code):
  ```
  merged PRs fetched: 60; B accepts: 60; B rejects (skipped): 0
  hook invocations: 180; refusals (exit 2): 0
  exit 0 with note [single-quoted] x58: pr-body-preflight: not checked — the body holds $ or a backtick the hook cannot expand  PRs [985, 983, 982, ..., 869, 868]
  ```
  The heredoc and body-file forms gave 120 runs, all exit 0 and silent
  (judged and passed). Control: the same bodies with every closing token
  stripped, so B rejects them, through the heredoc form:
  ```
  mutated bodies B rejects: 60; hook refused with B's exact strings: 60; mismatches: 0
  ```
- Result: PASS. There is no false block, and the numbers match the first
  verify exactly. The new comment and heredoc cutting did not hide a
  real body. The control still refuses 60 of 60, which it would not do
  if step 2b had cut a `$(cat <<…)` body.

## Transcript replay (Milestone 3's replay rule)

- Check: every Bash command in this project's local Claude Code
  transcripts, read-only, through `preflight()` with each record's own
  cwd. It runs on the pre-fix snapshot (Review's harness, `before`) and
  on HEAD (`after`).
- Evidence (2026-10-16):
  ```
  files=42 bash commands=9096 with 'pr create'=210

  before: full replay exit codes {0: 9094, 2: 2}
      74 a body file is read only from the first command
      61 cannot parse the command: No closing quotation
      44 no --body or --body-file
      13 the body holds $ or a backtick the hook cannot expand
       7 judged-pass
       7 saw "gh pr create" but found no such command
       2 no body file at <path>
       2 exit2

  after: full replay exit codes {0: 9094, 2: 2}
     120 a body file is read only from the first command
      50 no --body or --body-file
      16 saw "gh pr create" but found no such command
      13 the body holds $ or a backtick the hook cannot expand
       6 judged-pass
       2 no body file at <path>
       2 exit2
       1 a cd before gh pr create the hook cannot place
  ```
  Both `after` exit 2s are the same two commands as `before`: real
  `gh pr create` runs (one after `git push … &&`) with quoted-delimiter
  heredoc bodies. Each was confirmed as a body B rejects. The heredoc
  was rendered by `/bin/bash`'s own `cat`, and the output was judged by
  B itself:
  ```
  exit-2 verdicts: 2 distinct commands: 2
  hook: ['B: PR body has no Closes #N link'] | B on bash-rendered body: ['B: PR body has no Closes #N link'] | agree: True
  hook: ['B: PR body has no Closes #N link'] | B on bash-rendered body: ['B: PR body has no Closes #N link'] | agree: True
  ```
  The counts match Implement's breakdown note (74 + 46 = 120, 44 + 6 =
  50, 7 + 9 = 16). The record count rose from 9,094 to 9,096 because
  this session's own transcript grew.
- Result: PASS. There is no exit 2 that B would not give, and none on a
  command whose `gh pr create` never runs.

## Failures

None.

## Observations for Review

- **Real coverage is unchanged at about 3 to 4%.** 8 of 210 historical
  `pr create` commands are judged (6 pass, 2 exit 2), against 9 before.
  The fix turned the 61 `No closing quotation` parses into parses, but
  46 of them now land on `a body file is read only from the first
  command`. That is the `cat > F <<'EOF' … EOF` then `--body-file F`
  shape. Review's major finding 4, binding a heredoc to the body file
  it writes, is still the lever, and it remains deferred. This is not a
  criterion failure.
- **The single-quoted `$`/backtick gap stands** (58 of 60 real bodies in
  that synthetic shape). Review graded it minor and deferred it. It is
  unchanged.
- **Latency rose slightly** (new measurement, 20 runs each through the
  registered command). `ls -la` took a median 38.1 ms (max 48.7). A
  judged `-R`-same-repository candidate took a median 53.2 ms (max
  57.4). Review's pre-fix figures were 33.9 ms and 50.2 ms on a
  different run. Both are far inside the 10 s timeout.

## Not verified

- A bare `gh pr create` in a live session was not run, by design. Only
  the `false &&` form was observed live, and the hook judges that
  segment the same way.
- The hook under the cloud routines' harness (merge train, hourly
  improvement) was not exercised. Those sessions load the same checked-in
  `.claude/settings.json`, and they often run in worktrees. The worktree
  arm is covered by `test_a_worktree_shares_its_clones_remotes_and_checkout`
  only, not by a live routine run.
- The accepted limit in architecture.md step 8 was not probed. A shell
  already sitting in another checkout after an earlier Bash call's `cd`
  is still judged, because the payload cwd is taken as this repository.
- The false-block hunt did not re-fetch merged PRs. Bodies merged after
  the first verify's fetch are not in the sample.
- `one_owner.py`'s 9 problems were not re-diffed against `main`. None
  names the hook or B's patterns or strings (shown above).

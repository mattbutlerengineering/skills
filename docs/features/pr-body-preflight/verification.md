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
---

# Verification: PR-body preflight hook

## Summary

7 of 7 PRD success criteria PASS, plus the breakdown's remaining
acceptance points. False-block hunt: 60 real merged bodies that detector B
accepts, 180 hook invocations across three command shapes, **0
refusals**; the control (same 60 bodies with the closing line stripped)
was refused 60 of 60 with B's exact strings. One coverage observation for
Review (not a failure): a single-quoted literal `--body` holding `$` or a
backtick fails open, which left 58 of the 60 real bodies unchecked in that
shape. Verdict: ready for Review.

## Criteria & evidence

Unless stated otherwise, hook evidence below comes from the registered
command, read from `.claude/settings.json`:

```
[ ! -f "$CLAUDE_PROJECT_DIR/pr_body_preflight.py" ] || python3 "$CLAUDE_PROJECT_DIR/pr_body_preflight.py"
```

It runs through `/bin/sh -c` with `CLAUDE_PROJECT_DIR=/Users/mbutler/github/skills`
and a payload `{"tool_name": "Bash", "tool_input": {"command": ...}, "cwd": ...}`
on stdin. Temp paths are shown as `<tmp>`.

### 1. A readable failing body is refused: exit 2, B's own strings on stderr

- Check: literal `--body` missing each line and both; `-F` with a real
  failing file; a failing quoted-delimiter heredoc body; a compound
  command.
- Evidence:
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
  --- 10 compound cd x && gh pr create, failing
  exit=2
  stderr: B: PR body cites no work-order id
  stderr: B: PR body has no Closes #N link
  stderr: pr-body-preflight: the body contract is docs/kb/pr-body-contract.md
  ```
  The strings are B's own, from `gates.pr_body_problems`:
  ```
  353:def pr_body_problems(body):
  ...
  360:        problems.append("B: PR body cites no work-order id")
  ...
  362:        problems.append("B: PR body has no Closes #N link")
  ```
  Live session: the hook is active in this verifying session. Running
  `false && gh pr create --body "x"` (gh can never execute) was refused
  by the Claude Code harness:
  ```
  PreToolUse:Bash hook error: [[ ! -f "$CLAUDE_PROJECT_DIR/pr_body_preflight.py" ] || python3 "$CLAUDE_PROJECT_DIR/pr_body_preflight.py"]: B: PR body cites no work-order id
  B: PR body has no Closes #N link
  pr-body-preflight: the body contract is docs/kb/pr-body-contract.md
  ```
- Result: PASS

### 2. A body B accepts passes (exit 0), and so does every non-`gh pr create` command

- Check: passing literal body (work-order token form and `No work order:`
  form), passing `--body-file` (relative, resolved against payload `cwd`),
  passing heredoc body holding inner `"` and `'`, passing compound
  command, a non-gh command, and `echo "gh pr create"`.
- Evidence:
  ```
  --- 1 passing literal --body
  exit=0
  --- 2 passing No-work-order body
  exit=0
  --- 6 --body-file real passing file (relative, cwd=tmp)
  exit=0
  --- 8 heredoc quoted delimiter, passing
  exit=0
  --- 11 compound cd x && gh pr create, passing
  exit=0
  --- 15 non-gh command
  exit=0
  --- 16 echo mentioning gh pr create
  exit=0
  stderr: pr-body-preflight: not checked — saw "gh pr create" but found no such command
  ```
  Real bodies: see the false-block hunt below (0 refusals in 180 runs).
- Result: PASS

### 3. Unreadable bodies and unparseable commands fail open with a one-line note

- Check: `--fill`, `--web`, `--body-file -`, `$VAR` body, missing body
  file, unclosed quote. `--fill-first`, `--editor`, `--template`,
  `--recover`, clusters, a raising owner and a stdin read failure are
  covered by the replay tests (criterion 5).
- Evidence:
  ```
  --- 12 --fill
  exit=0
  stderr: pr-body-preflight: not checked — --fill leaves the body to gh
  --- 13 --web
  exit=0
  stderr: pr-body-preflight: not checked — --web leaves the body to gh
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
  ```
  Guard: the same registered command with `CLAUDE_PROJECT_DIR` pointed at
  an empty temp directory (no script):
  ```
  --- 21 guard: script absent
  exit=0
  ```
- Result: PASS

### 4. The check's patterns have one owner; the hook delegates to B

- Check: grep counts of the regex definitions and problem strings across
  non-test Python (excluding `factory/templates/`), the hook's references,
  the delegation test, and `one_owner.py`.
- Evidence:
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
  289:        problems = gates.pr_body_problems(body)
  ```
  The `gates_selftest.py` and `validator.py` hits predate this branch and
  are not copies of B's rule: on `main`, `gates_selftest.py:588` is a
  selftest assertion on B's output, and `validator.py:299`/`302` are
  detector V's own `V: ...` strings; `git diff --stat main...HEAD --
  gates_selftest.py validator.py` is empty. The hook defines none of the
  three regexes.
  Delegation test (patches `gates.pr_body_problems` to a sentinel):
  ```
  B's one owner, not a copy: a sentinel from the patched owner ... ok
  Ran 2 tests in 0.001s
  OK
  ```
  `python3 one_owner.py` prints `one-owner: 9 problem(s)`; a grep of its
  output for `pr_body|WO_TOKEN|CLOSES_TOKEN|work-order id|Closes #N`
  counts `0`.
- Result: PASS

### 5. A replay test covers the required fixture shapes

- Check: `python3 -m unittest tests.test_pr_body_preflight -v`.
- Evidence (excerpt; full module):
  ```
  test_a_body_file_after_another_command_fails_open ... ok
  test_a_missing_body_file_fails_open ... ok
  test_a_non_utf8_body_file_fails_open_with_the_read_problem ... ok
  test_body_file_stdin_fails_open ... ok
  test_quoted_delimiter_failing_body_is_refused_verbatim ... ok
  test_unquoted_delimiter_with_a_dollar_fails_open ... ok
  test_unclosed_quote_fails_open_with_a_note ... ok
  test_a_stdin_read_failure_fails_open ... ok
  test_a_raising_owner_fails_open ... ok
  test_a_failing_body_is_refused_through_the_registration ... ok
  test_flags_that_leave_the_body_to_gh_fail_open ... ok
  ...
  Ran 42 tests in 0.135s
  OK
  ```
  The end-to-end harness above independently covers each PRD-named shape
  (passing body, each missing line, `--body-file` with a real file,
  heredoc, compound, `--fill`, non-gh) through the real registration.
- Result: PASS

### 6. The hook is registered in the checked-in `.claude/settings.json` as a PreToolUse hook on Bash

- Check: file contents; whether `settings.local.json` changed on the
  branch.
- Evidence:
  ```
  "PreToolUse": [ { "matcher": "Bash", "hooks": [ { "type": "command",
    "command": "[ ! -f \"$CLAUDE_PROJECT_DIR/pr_body_preflight.py\" ] || python3 \"$CLAUDE_PROJECT_DIR/pr_body_preflight.py\"",
    "timeout": 10 } ] } ]
  ```
  `git diff --name-only main...HEAD | grep -c settings.local` gives `0`.
  The live-session refusal under criterion 1 shows the registration loads.
- Result: PASS

### 7. The four CI checks pass

- Evidence:
  ```
  tests: 3264 tests across 106 modules in 14.3s on 8 workers, 0 problem(s)
  run_tests exit=0
  lint: 0 problem(s) across 34 skills
  drift: 0 problem(s)
  gates: 0 problem(s)
  selftest: ok
  ```
  (`python3 gates.py && python3 gates.py --selftest` exit 0.)
- Result: PASS

### Breakdown acceptance points not covered above

- Check: plugin version and skills untouched (ADR-0095); hook not
  mirrored; dual-membership pin and `factory.VERBS` row.
- Evidence:
  ```
  $ git diff --stat main...HEAD -- skills/ .claude-plugin/plugin.json | wc -l
         0
  $ grep -c pr_body_preflight factory_init.py
  0
  ```
  The dual-membership pin
  (`tests/test_dual_membership.py`) and the verb-table pins
  (`tests/test_factory_cli.py`) are inside the passing 3264-test run.
- Result: PASS

## False-block hunt (the PRD's top risk)

- Check: `gh pr list --state merged --limit 60 --json number,body,mergedAt`
  (read-only). Each body judged by `gates.pr_body_problems`; each one B
  accepts is wrapped as
  `gh pr create --title t --body "$(cat <<'EOF'` / body / `EOF` / `)"`
  (delimiter lengthened if the body holds an `EOF` line), as
  `--body '<body>'` via `shlex.quote`, and as `--body-file b<N>.md`
  relative to the payload `cwd`, then run through the registered command.
- Evidence:
  ```
  merged PRs fetched: 60; B accepts: 60; B rejects (skipped): 0
  hook invocations: 180; refusals (exit 2): 0
  exit 0 with note [single-quoted] x58: pr-body-preflight: not checked — the body holds $ or a backtick the hook cannot expand  PRs [985, 983, ..., 868]
  ```
  Heredoc and body-file forms: 120 runs, all exit 0 and silent (judged
  and passed). Control: the same bodies with every closing token
  stripped, so B rejects them, through the heredoc form:
  ```
  mutated bodies B rejects: 60; hook refused with B's exact strings: 60; mismatches: 0
  ```
- Result: PASS. No false block. The silent exits are real judgements,
  since the control shows the same shape refuses when B would.

## Failures

None.

## Observations for Review

- **Single-quoted literal bodies are not checked when they hold `$` or a
  backtick.** Inside single quotes the shell expands neither, so such a
  body is in fact readable. The hook judges after `shlex` has removed the
  quotes, so it cannot tell, and it fails open. On real bodies this left
  58 of 60 unchecked in that shape: markdown code spans use backticks.
  It is safe (fail open, CI's B still judges), but it reduces coverage for
  one plausible shape. The heredoc and body-file shapes, which are the
  common ones in this repo, were all judged. This is a candidate
  refinement, not a criterion failure.

## Not verified

- A bare `gh pr create` in a live session was not run, by design. Only the
  `false &&` form was observed live, and the hook judges that segment the
  same way.
- The hook under the cloud routines' harness (merge train, hourly
  improvement) was not exercised. Those sessions load the same checked-in
  `.claude/settings.json`, but no routine run was observed here.
- `one_owner.py`'s 9 problems were not re-diffed against `main` in this
  stage. Implement recorded the same 9 on `main`, and none names the hook
  or B's patterns or strings (shown above).
- Hook latency against the 10-second timeout was not measured. Every
  harness run completed well inside it, but no timing was recorded.

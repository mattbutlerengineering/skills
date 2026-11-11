---
stage: verify
run: feature:pr-body-hook-coverage
date: 2026-11-09
assumptions:
  - "The Owner named no snapshot path, so the default was used: ~/.cache/pr-body-hook-coverage-verify/snapshot.jsonl (mode 600, outside every repository, never committed). The harness scripts live in ~/.cache/pr-body-hook-coverage-verify/harness/ and are throwaway; their SHA-256 values are listed under Not verified."
  - "The snapshot was extracted twice. The first file (never measured) was discarded because its dedupe preferred a transcript line that holds no cwd; the second prefers a line with a cwd, then the earliest timestamp. Only the second was measured. Both hold 1817 rows."
  - "Judged means exit 2, or exit 0 with no 'not checked' line on a body the hook read. Both hooks ran with an empty environment and the row's cwd, so a body file read from disk and a cd placed against the checkout depend on the disk of this day: the snapshot freezes the commands and their cwd, not the disk."
  - "The pre-change hook is a4b32bf (git show a4b32bf:pr_body_preflight.py, the whole tree at that commit extracted outside the repository), per the Implement hand-off; the changed hook is origin/main at 3f2b7a9."
  - "No command text, PR body text, repository name or path from the corpus appears here: counts, hashes and shape names only."
---

# Verification: Judge the same-call heredoc body

## Summary

Run on `origin/main` at 3f2b7a9 in an isolated worktree. All eight PRD
success criteria PASS and no criterion FAILs: on one frozen snapshot of 1817
`gh pr create` commands the judged share rose from 229 (12.60%) to 479
(26.36%), delta +250 commands (+13.76 points), against a 25% target (455
commands needed; margin 24) and a reachable ceiling of 778 (42.82%). The
false-block oracle paired 250 of 250 commands judged through the heredoc
binding, with 0 unpaired and 0 disagreements. Qualifications, not softened:

- The margin over 25% is 24 commands and depends on the disk of this day.
  Without a cwd the same snapshot gives 158 and 348 (19.15%), under 25%; 263
  rows carry no cwd and 873 rows name a cwd directory that is gone. 57
  commands bind but are stopped afterwards by the target check (55 `cd`
  placements, 2 other-repository targets); see Criterion 3.
- Unverified by the oracle: the between-commands rule (the oracle never runs
  those commands). Only 8 bound commands have a command between writer and
  reader, so the hand sample is 8 of 8, not the 20 the hand-off asked for;
  242 of the 250 have nothing between, so that rule decided almost none of
  the verified refusals.
- Counted gaps: 1 criterion element NOT RUN (the by-hand read of "the first
  false refusal", because the oracle found 0 false refusals; the first
  refusal through the binding was read instead) and 1 unknown (the
  between-commands rule beyond the 8 corpus cases). 0 criteria FAIL.
- `one_owner.py` exits 1 on 4 problems that do not touch
  `pr_body_preflight.py`; they exist on main and are not this run's.

## Criteria & evidence

### Criterion 1 (PRD): the demo runs as written and exits 2 with B's strings, then the pointer

- Check: the demo payload through `preflight()` and through the registered hook command exactly as `TestRegistration` runs it (`/bin/sh -c <command from .claude/settings.json>`, `CLAUDE_PROJECT_DIR` set to the worktree).
- Evidence:
  ```
  == demo (bad body)
  preflight(): (2, ['B: PR body cites no work-order id', 'B: PR body has no Closes #N link', 'pr-body-preflight: the body contract is docs/kb/pr-body-contract.md'])
  registered hook: 2 'B: PR body cites no work-order id\nB: PR body has no Closes #N link\npr-body-preflight: the body contract is docs/kb/pr-body-contract.md\n'
  ```
  Fixture: `TestSameCallHeredoc.test_the_demo_payload_is_refused_before_the_pr_exists`.
- Result: PASS

### Criterion 2 (PRD): the passing twin exits 0 and prints nothing

- Check: the same payload with a `No work order: <reason>` line and a `Closes #1673` line, both entry points.
- Evidence:
  ```
  == passing twin
  preflight(): (0, [])
  registered hook: 0 ''
  ```
  Fixture: `test_its_passing_twin_is_silent`.
- Result: PASS

### Criterion 3 (PRD): judged share of at least 25% on one frozen snapshot, ceiling beside it

- Check: freeze the snapshot once; run the a4b32bf hook and the changed hook over every row (in process with an empty environment, then again as the real script through `env`-less subprocesses; both entry points agree on every row). Re-derive the ceiling and the survival funnel.
- Snapshot: path `~/.cache/pr-body-hook-coverage-verify/snapshot.jsonl` (default; the Owner picked none), mode 600, written once, sorted by command, de-duplicated by command text. Extraction: `python3 ~/.cache/pr-body-hook-coverage-verify/harness/extract.py` (every line of every `~/.claude/projects/-Users-mbutler*/**/*.jsonl`, main and subagent, whose `message.content` holds a `tool_use` named `Bash` whose `input.command` contains `gh pr create`; row = command, the cwd and timestamp of its preferred occurrence). 
  ```
  files scanned 4900 rows 1817
  71c8ffb8327b4444167fd98f256296ba12070f6cf8d62a8d81294ddca781d99f  snapshot.jsonl
  1817 snapshot.jsonl
  ```
  263 rows carry no cwd (the command appears only in request-blob lines); 873 rows name a cwd directory that no longer exists.
- Evidence (harness output, `run_hook.py`, then `funnel.py`):
  ```
  baseline (a4b32bf):  rows 1817 judged 229 exit2 195 err 0 bound_cmds 0
  changed  (3f2b7a9):  rows 1817 judged 479 exit2 361 err 0 bound_cmds 307
  cli subprocess cross-check, baseline: judged 229 exit2 195 disagree_with_inprocess 0
  cli subprocess cross-check, changed:  judged 479 exit2 361 disagree_with_inprocess 0

  pre-change judged 229 of 1817 12.60%
  changed judged 479 26.36% delta 250 13.76 pts
  lost by changed (judged before, not now): 0
  judged gained by changed not via binding: 0
  ```
  25% of 1817 is 454.25, so 455 commands are needed; 479 clears it by 24.
- Ceiling: pre-change judged (229) plus the commands the pre-change hook does not judge that have a not-first `--body-file` reader whose file an earlier writer of any shape wrote (a write redirect to the same token, or `tee`, `cp`, `mv`, `install`, `touch`, `ln` with it as an argument):
  ```
  same-call commands not judged pre-change (any-shape writer): 549 ceiling 778 42.82%
    (writer shape found, i.e. `cat > F <<D` or later stages): 486 ceiling 715 39.35%
  ```
  #1633's 681 same-call and the architecture probe's 548 compare with 549 here; the 158 of #1633 reproduces only when no cwd is given (see below), 229 with the row's cwd.
- Survival funnel, per not-first `--body-file` reader (693 readers in the snapshot; 143 have no earlier writer of any shape; every reader is one command), in the hand-off's order. The harness re-implements `_bound_body`'s checks in this order, and agrees with the real `_bound_body` on all 693 (0 mismatches):
  ```
  readers whose file an earlier writer (any shape) wrote: 550
    lost    4 at: spelling rule -> left 546
    lost   59 at: writer shape -> left 487
    lost   29 at: unquoted heredoc ($, backtick, backslash) or unterminated -> left 458
    lost  100 at: chain: writer behind && with a newline before the reader -> left 358
    lost   22 at: chain: a |, (, ), lone &, ||, ; ; or shell keyword between -> left 336
    lost   29 at: between-commands rule -> left 307
    lost    0 at: before-the-writer rules (descriptor, function, alias, trap, steering name) -> left 307
    lost    0 at: $' guard -> left 307
    bound readers: 307
  ```
  After binding, the hook's own target check stops 57 of the 307 (the funnel row the architecture's table lacks): 55 with `a cd before gh pr create the hook cannot place`, 2 with `the PR targets another repository / remote unreadable`. Of the 57, 15 rows have no cwd and 27 name a cwd directory that is gone. So 307 bound commands become 250 judged:
  ```
  commands where _bound_body returned a text: 307  of which hook judged: 250  bound but not judged: 57
  ```
  Reconciliation: 229 + 250 = 479 judged; the ceiling's 778 less 479 is 299 = 242 lost in the rules above + 57 lost at the target check. The $' guard and the before-the-writer rules cost nothing on this corpus.
- Context, measured separately and not the criterion: the same snapshot with no cwd in any payload judges 158 (baseline) and 348 (changed, 19.15%).
  ```
  baseline no-cwd judged 158
  changed  no-cwd judged 348
  ```
- Result: PASS (479 of 1817 = 26.36% >= 25%, margin 24 commands, with the disk dependence above recorded)

### Criterion 4 (PRD): the hook exits 2 iff `gates.pr_body_problems` is non-empty on the file a real shell writes (false-block oracle)

- Check: for each of the 250 commands judged through the binding (those where the harness-wrapped `_bound_body` returned a text and the hook judged), build a span from the WRITER ALONE found by regex over the raw command text (`cat > <scratch>` + the original heredoc operator and delimiter word + body + delimiter line; the rest of the operator's line dropped; no other command of the Owner's was run), run it under `sandbox-exec` (network denied, writes denied outside the scratch directory, scratch HOME, `HOME` the only variable, cwd the scratch directory, 5-second timeout; a timeout, zero spans, an unclosed span or more than one distinct span counts as unpaired). The file the shell wrote is the only reference body. Then compare B's verdict on that file with the hook's.
- Sandbox sanity (`sandbox_check.py`; a failing write gives shell exit 1):
  ```
  write inside scratch: (0, '') True
  write outside scratch: (1, '… line ') False
  write to HOME-outside file: (1, '… line ') False
  network: (1, '… conne')
  ```
- Evidence (`oracle.py`):
  ```
  bound commands judged-through-binding, readers: 250 bound commands not judged: 57
  pairs 250 unpaired 0 disagreements 0 cmd-level disagree 0 identical text 250
  refusals by hook among pairs: 166 by oracle: 166
  false blocks (hook refuses, B on shell file does not): 0  missed (hook passes, B refuses file): 0
  ```
  250 pairs, 0 unpaired, 0 disagreements, 166 refusals and 84 passes on each side, and the shell-written file is byte-identical (same SHA-256) to the text the hook judged in all 250.
- The "first refusal B would not give" has nothing to read: there are 0. The first refusal the hook gave through the binding was read by hand instead: a Summary / Why / Test plan body that carries no work-order token, no `No work order:` line and no closing keyword; B's own strings are the two the hook printed. Agreed.
- Blind spot (stated, not papered over): the oracle never runs the commands between writer and reader. Of the 250, 242 have nothing between; 8 have a command between: 5 a `cd` and 3 a read-only `grep`; F is absolute in all 8, so the `cd` leaves it bound (a `grep -c` whose argument names F, which only reads). Read by hand against the inert list: all 8 consistent with the rule, 0 would be a false block. That is 8 of 8, short of the 20 the hand-off asked for because only 8 exist; the hand sample cannot reach the `git`, `gh`, `printf`, assignment or `export` branches of the inert list, which no judged command in this corpus exercises.
- Result: PASS (0 disagreements on 250 pairs; the between-commands rule is covered by the 8-command hand read and the fixtures only)

### Criterion 5 (PRD): a binding the hook cannot establish passes with a "not checked" note, exit 0, no exception escapes

- Check: the fixtures that name each shape, a malformed payload, and a binding that raises.
- Evidence:
  ```
  malformed JSON: (0, [])
  non-dict payload: (0, [])
  no command: (0, [])
  raising binding: (0, ['pr-body-preflight: not checked — RuntimeError: injected'])
  ```
  Fixtures: `test_an_unquoted_delimiter_with_an_expansion_is_a_note` (shell expansion in the heredoc text), `test_a_verb_off_the_list_between_is_a_note`, `test_a_write_redirect_between_is_a_note`, `test_any_command_between_writer_and_reader_is_a_note` (a file rewritten or removed between), `test_a_cleanup_after_the_reader_does_not_unbind` (cleanup after the reader still judged), `test_a_reader_naming_a_different_file_keeps_todays_note`, `test_a_malformed_payload_or_a_raising_binding_fails_open`, `test_a_raising_owner_fails_open`. On the corpus: 0 of 1817 rows raised or timed out (`err 0`).
- Result: PASS

### Criterion 6 (PRD): fixture tests cover each shape, and every test that passed before still passes

- Check: `python3 -m unittest tests.test_pr_body_preflight`; then the a4b32bf copy of the test file run against the changed hook.
- Evidence:
  ```
  Ran 166 tests in 0.271s
  OK
  ```
  `TestSameCallHeredoc` holds 99 of them. Named fixtures: the demo and twin (above); `test_a_quoted_delimiter_is_judged_verbatim`; `test_an_unquoted_delimiter_without_expansion_is_a_pair`; `test_a_dash_heredoc_with_tab_indented_lines_is_a_pair`; `test_a_leading_cd_to_the_repository_is_a_pair`; `test_two_readers_are_each_bound_to_their_own_writer`; `test_a_body_holding_its_own_heredoc_snippet_is_judged_on_the_text`; `test_a_log_redirect_before_a_first_command_body_file_reads_from_disk`. The pre-feature test file against the changed hook:
  ```
  Ran 67 tests in 0.165s
  OK
  ```
- Result: PASS

### Criterion 7 (PRD): the check's patterns have one owner

- Check: `TestOneOwner` (in the 166 above: `test_the_hook_judges_through_gates`, `test_a_raising_owner_fails_open`) and `python3 one_owner.py`, filtered for the hook.
- Evidence:
  ```
  one-owner: assembly_line.py:28 COMPLETED and conductor.py:182 COMPLETED state the same value — one fact, one owner
  one-owner: assembly_line.py:40 HERE and trigger_eval.py:45 ROOT state the same value — one fact, one owner
  one-owner: assembly_line.py:58 _history and board.py:49 run_entry read the same payload keys (stage, state) — one fact, one owner
  one-owner: eval_trends.py:42 DAY and kb.py:60 ISO_DATE state the same value — one fact, one owner
  one-owner: 4 problem(s)
  ```
  Lines naming `pr_body_preflight`: 0. `one_owner.py` exits 1 on those four, none this run's.
- Result: PASS

### Criterion 8 (PRD): `run_tests.py`, `lint.py`, `gates.py`, `gates.py --selftest`

- Check: each command in the worktree at 3f2b7a9.
- Evidence:
  ```
  tests: 4311 tests across 134 modules in 26.1s on 8 workers, 0 problem(s)
  run_tests exit 0
  lint: 0 problem(s) across 35 skills
  lint exit 0
  gates: 0 problem(s)
  gates exit 0
  selftest: ok
  selftest exit 0
  ```
- Result: PASS

### Breakdown acceptance: the kb page and docstring say a same-call heredoc is readable, drift clean

- Check: `python3 kb.py drift` and `python3 kb.py lint` (and `lint.py` above).
- Evidence:
  ```
  drift: 0 problem(s)
  kb drift exit 0
  kb: 0 problem(s)
  kb lint exit 0
  ```
  `docs/kb/pr-body-contract.md` names the same-call heredoc in its hook paragraph.
- Result: PASS

### Breakdown acceptance: the replay specification of the hand-off (nine points)

- Check: each point against what was run. (1) one frozen sorted de-duplicated snapshot with cwd, outside the repository, at the default path the Owner did not override: done. (2) both hooks over every row, a4b32bf baseline, empty environment, row cwd: done. (3) judged definition and 25% target: Criterion 3. (4) ceiling counting pre-change judged once: Criterion 3. (5) funnel row by row including the two post-table rows and the target-check row: Criterion 3. (6) only SHA-256, count, extraction command and measured numbers recorded: this file. (6a) binding-judged commands identified by wrapping `_bound_body`: Criterion 4. (7)(8) writer-span oracle under `sandbox-exec`, unpaired never agreement: Criterion 4. (9) blind spot and the between-commands list: Criterion 4.
- Evidence:
  ```
  snapshot: 71c8ffb8327b4444167fd98f256296ba12070f6cf8d62a8d81294ddca781d99f  1817 rows  -rw-------
  hooks:    baseline a4b32bf judged 229 | changed 3f2b7a9 judged 479 (empty environment, row cwd)
  oracle:   pairs 250 unpaired 0 disagreements 0 | between-commands bound readers: 8 of 250
  ```
- Result: PASS

## Failures

none. The judged share is 26.36%, at or above 25%, and the oracle found 0 false blocks on 250 pairs.

## Not verified

- NOT RUN: the by-hand read of the first refusal "B would not give" (criterion 4): there is none to read, since the oracle found 0 disagreements. The first refusal through the binding was read instead.
- The between-commands rule is unverified by the oracle by construction. The hand sample is 8 of 8 existing cases, not 20, and holds only `cd` and `grep`; the `git`, `gh`, `printf`, assignment and `export` branches of the inert list are covered by fixtures only, not by any corpus command.
- The 25% result carries 24 commands of margin and is sensitive to the disk: 57 bound commands were stopped by the target check (42 of them on a cwd that is absent or gone), and the same snapshot with no cwd is 19.15%. A rerun on another day or machine on the same snapshot file can give a different judged count for first-command body files read from disk and for `cd` placement; the hashes below reproduce the commands, not the disk.
- A recorded PR body was not used as a reference (by the PRD's design); whether the PRs those commands opened passed B in CI was not checked.
- The pre-change 158 of #1633 reproduces only with no cwd; with the row's cwd the pre-change hook judges 229 (relative body files that exist on disk today). Why #1633's 681 same-call count differs from 549 here is not explained.
- Throwaway harness (outside the repository, `~/.cache/pr-body-hook-coverage-verify/harness/`), SHA-256: `extract.py` aec56556fa41f3eeef6b60c048a757b660d5b162e2e6c018dc25f039ccf822f7; `run_hook.py` b021449b52949573044e7ef03ff89b58658dc6b644e19dca825e35a4724fbb19; `cli_check.py` ded7809fb8d9f303afbbbfbad1c553a46068707107d9648492c74a9e80646358; `funnel.py` 95f510245aa565d040207eb48874731660134410c372894510f02e42856a8313; `oracle.py` e7e5a87da054bb3b6fac511b2fa8ac0d7b6b2d03e61dc077233e484342acf6e6; `between.py` (edited once after the run to print one more column; hash is of the edited version) cced8047d0e8c86814cace74c5d3e6362d679b4ff8c3254612efd0ddff3b2b18; `nocwd.py` 59e44643c52d11cf8c4e4c399ba4bafdf1bfe4a48ca978ce00ba1c11c84d0294; `sandbox_check.py` 252f06d103d2e914c7ac02e411e5dbf82e20d6cc8ff89dfc9b8e9bf1628fa2b3. The snapshot is not committed (private PR bodies); the Owner holds it.

## Re-verification 2026-11-11: the lean sweep (issue #1677)

An addition; nothing above is rewritten. Review finding 1 of #1676 (deferred by the Owner on 2026-11-09, cut-list tag speculative) named branches of `pr_body_preflight.py` that no corpus command uses. Each was disabled one at a time, the frozen snapshot replayed through the hook, and every one that lost nothing and added no refusal was cut. The release's carried-risks paragraph required a fresh Verify after any edit to the live hook; this is it.

### What was run

- Snapshot: the frozen `~/.cache/pr-body-hook-coverage-verify/snapshot.jsonl`, read in place, SHA-256 `71c8ffb8327b4444167fd98f256296ba12070f6cf8d62a8d81294ddca781d99f`, 1817 rows, unchanged. Nothing in that directory was written: the harness scripts were copied to a scratch directory, `run_hook.py` was pointed at a copy of each hook tree, and `oracle.py` (two path edits: the tree and the results file) wrote its `oracle.json` to the scratch directory. The frozen results and hashes above stand.
- Hooks: baseline is `origin/main` at 6499643 (both post-Verify commits, 157d568 and f74c247, included); each variant is that tree with one branch disabled; final is the tree with the three cuts that stand. Empty environment, the row's cwd, in process, as in Criterion 3. Judged is as defined above: exit 2, or exit 0 with no "not checked" line.
- Compared per command (by snapshot row), not by total: a branch counts as losing a command when the row goes from judged to not judged, and as gaining a refusal when the row goes to exit 2 from a code that was not 2. A third column compares every row's exit code, judged flag, note flag and line count, so a changed note is seen too.

### Baseline

Baseline today: 474 of 1817 judged (26.09%), 357 exit 2, 0 errors, 307 commands bound through the heredoc, 249 of them judged (58 stopped at the target check: 56 `a cd the hook cannot place`, 2 `the PR targets another repository / remote unreadable`). The 2026-11-09 run recorded 479 (26.36%) and 250: the five-command difference is the disk (see below), not a code change by this sweep. 455 are needed for 25%, so the margin is 19 commands today, not 24.

### Per-branch result

Each row is the baseline against the hook with only that branch disabled. "Rows changed" counts every row whose exit code, judged flag, note flag or line count differs.

| Branch disabled | Judged | Commands lost | Gained a refusal | Rows changed | Decision |
|---|---|---|---|---|---|
| `_inert_git` (with `_long_option`, `GIT_VERBS`, `GIT_CONFIG_SCOPES`) | 474 | 0 | 0 | 0 | cut |
| `_inert_gh` (with `GH_VERBS`, `GH_API_WRITES`) | 474 | 0 | 0 | 0 | cut |
| assignment and `export` branch of `_inert` (with its `STEERING_NAME` read) | 474 | 0 | 0 | 0 | cut |
| descriptor-prefix marker (`FD_PREFIX`, `FD_WORD`, `_unmark`'s digit part, `_Unrun`'s digit branch, the digit absorption in `_simple_commands`, the `lstrip(DIGITS)` branch of `_write_redirect`) | 474 | 0 | 0 | 0 | **kept** (see below) |

`_long_option` and the constant sets are called only from the two `_inert_*` functions, so they were measured with them. The marker is one mechanism spread over six sites, so it was disabled at its source (`_Unrun` stops producing digit markers) and the rest then has nothing to read. It lost 0 commands on the snapshot, but the snapshot has no command that carries a standalone steering assignment or a digit-prefixed redirect between writer and reader, so 0 rows changed says nothing about the shapes below, and the differential check (next section) found that cutting it adds refusals. The issue's own rule is that a cut only adds notes, never a refusal, so the marker was put back: its code is byte for byte as on `origin/main`, and its tests are `origin/main`'s with one entry changed (`git status 2>/dev/null` became `cat x 2>/dev/null`, since a `git` command between writer and reader is now a note) and two regression tests added. `_shadows` and `_opens_descriptor` were not disabled and are untouched, as the issue says. The `{NAME}` marker (`FD_NAME_PREFIX`, `FD_NAME_WORD`) was not on the list and stays: `_opens_descriptor` reads it.

### Why the marker is kept: the differential check

Measuring commands lost on the snapshot is not enough for a cut that "only adds notes": the snapshot cannot show a refusal on a shape it does not hold. A throwaway differential harness (outside the repository) imported the hook of `origin/main` and the hook under test, generated commands from a list of snippets, and ran both on every command with a passing and with a failing body. Snippets: a steering assignment or `export` (`PATH`, `LD_*`, `DYLD_*`, `BASH_ENV`, `GH_*`, `*PAGER`, `HOME`, `IFS`) and plain ones, alone and carrying a digit-prefixed redirect; digit-prefixed duplications, closes, reads, writes to `/dev/null`, `<>`, `>&file`, here-strings and here-documents (expanding and literal); `exec` with each; a `git` or `gh` read and write; each placed before the writer, between writer and reader, after the reader, and with a command between writer and reader as well, for two writer spellings.

On the earlier head of this branch (all four cuts), 7056 commands: 649 went from exit 0 to exit 2 (and 1298 went from note to judged). The classes:

- A standalone steering assignment or `export` that carries a digit-prefixed redirect (`PATH=… 2>/dev/null`, `export BASH_ENV=… 2>/dev/null`, `LD_PRELOAD=… 2>&1`), before the writer or, for the names that only matter with a command between, between writer and reader. Without the marker the digit is a word of the command, `_shadows` reads the assignment as a one-shot prefix of a command named by that digit and stops flagging it. This is a false block (the reviewer showed it): with a fake `cat` first on `PATH`, the body the shell writes passes B while the hook refuses. The issue says `_shadows` guards against false blocks and must not be cut; cutting the marker weakened it in behaviour.
- Prefixed redirects that were a note and became a refusal though none writes the body file: `3<> /dev/null`, `3<>/dev/stderr`, `1>&/dev/null` and `2>&/dev/null` between writer and reader or after the reader, and before the writer `exec 3<> /dev/null`, `exec 3<<<x`, `exec 2>&/dev/null` and `exec 3<<EOF` with an expanding body.

At commit `28660ca` this entry claimed that the only place a cut added a judgement was a prefixed here-document or here-string. That was wrong: the marker cut also adds refusals. Cutting it fails the issue's rule, so the marker and its constants are as on `origin/main`, and its tests differ from `origin/main`'s only as the paragraph above says.

### Final hook

The three cuts that stand (`_inert_git`, `_inert_gh`, the assignment and `export` branch of `_inert`), replayed the same way: 474 of 1817 judged (26.09%), 357 exit 2, 0 errors, 307 bound, 0 commands lost against the baseline, 0 gained a refusal, 0 rows changed in any column. 474 is above the 455 needed: margin 19. The final tree is the head recorded in the pull request; `_shadows` and `_opens_descriptor` are byte-identical to `origin/main`.

False-block oracle on the final hook, `oracle.py` as recorded (writer span alone under `sandbox-exec`, B on the file a real shell wrote):

```
bound commands judged-through-binding, readers: 249 bound commands not judged: 58
pairs 249 unpaired 0 disagreements 0 cmd-level disagree 0 identical text 249
refusals by hook among pairs: 166 by oracle: 166
false blocks (hook refuses, B on shell file does not): 0  missed (hook passes, B refuses file): 0
```

0 disagreements on 249 pairs. The baseline hook gives the identical oracle figures (249 pairs, 0 disagreements, 166 refusals each side), so the cuts changed none of them.

Differential check on the final hook against `origin/main`, the same generator: 7056 commands (each with a passing and a failing body), 0 went from exit 0 to exit 2, 0 went from note to judged, and 592 went from judged to a note. The 592 are the expected effect of the three cuts: a `git` or `gh` command, or a standalone assignment or `export`, between writer and reader (plain or with a redirect) is now a note naming the command, where the read-only and non-steering forms were judged. No exit code changed from 0 to 2 for any of the reviewer's shapes (every steering-with-redirect and prefixed-redirect shape above gives the same exit code as `origin/main`).

### Behaviour the cuts change, outside the corpus

None of this moves a corpus command; it is the change in the shapes the cut branches used to see through, pinned in `TestSameCallHeredoc`:

- A `git` or `gh` command, a standalone `NAME=value` and an `export` between writer and reader are now a note naming the command (`git status`, `gh pr view`, `gh api`, `T=`, `export`), where the read-only forms were judged. Nothing else changes: the digit prefix is as on `origin/main`.

### State the figures depend on

- The disk and cwd of 2026-11-11: 263 rows carry no cwd (unchanged) and 980 rows name a cwd directory that no longer exists (873 on 2026-11-09). The first-command body files read from disk and the `cd` placements are the part that moves: 474 here against 479 then, with the same hook logic. A run on another day or machine can differ again.
- Both trees ran from copies outside the repository, with the real `gates.py` of that copy. `run_tests.py`, `lint.py`, `kb.py drift` and `gates.py` with its selftest are reported in the pull request, not here.

### Not verified

- The between-commands rule is still unverified by the oracle by construction (the oracle never runs the commands between), and the corpus still has only 8 such commands (5 `cd`, 3 `grep`), so none of the three cuts was tested against a command that used the cut branches: the 0 lost is the absence of a user, not a measured equivalence. The new fixtures pin the new notes and nothing else.
- The margin over 25% is 19 commands and rests on the disk of this day.
- Whether any session outside this snapshot (later commands, other machines) uses a cut shape was not checked; for such a command the cost is a "not checked" note, never a refusal (the differential check found no exit-0 to exit-2 change on 7056 generated commands, which is a sample of shapes, not a proof).
- The differential generator is a fixed list of snippets; a shape outside it was not tried. It compares exit code and the not-checked line only, not the note text. It ran each hook in process with an empty environment and no cwd.

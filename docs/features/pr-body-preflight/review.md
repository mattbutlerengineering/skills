---
stage: review
run: feature:pr-body-preflight
date: 2026-10-16
assumptions:
  - "Run unattended under autorun; no live arbitration of severity. Severities are the reviewer's draft, using the brief's definition of the top risk: any exit 2 on a body detector B would accept, or on a command whose `gh pr create` never runs, is critical. Where frequency evidence argues for a lower grade it is stated beside the grade, so the Owner can downgrade."
  - "Review fixes a critical finding itself only when the fix is trivial (one condition, one test); anything needing a design change is routed to Implement, per the skill's fix loop. One critical was fixed here, one is routed."
  - "False-block frequency was measured by replaying every Bash command in this project's local Claude Code transcripts (~/.claude/projects/-Users-mbutler-github-skills*/*.jsonl, 42 files) through preflight(), read-only, with each record's own cwd. The transcripts stay where they are; nothing from them is copied here beyond counts and two command fragments."
  - "Probes ran from a scratchpad harness outside the repo. Latency was timed through the registered command from .claude/settings.json under /bin/sh with CLAUDE_PROJECT_DIR set, 20 runs each, on the Owner's machine (python3 is /opt/homebrew/bin/python3)."
  - "Domain passes: none selected (no changed path matches payments, migrations or dependencies). Standards filtered to domain `factory`: stdlib-only and adr0032-one-way-mirror, both advisory."
---

# Review: PR-body preflight hook

## Scope

`git diff main...HEAD` on `feat/pr-body-preflight`, commits `3204083` back
to the branch point, plus this stage's fix commit `eacc548`. Code:
`pr_body_preflight.py`, the `gates.pr_body_problems` extraction in
`gates.py` and its payload copy with `factory/manifest.json`, the
`factory.py` VERBS row, `.claude/settings.json`, and the three test
modules. Docs: ADR-0106, ADR-0091's status line, `docs/adr/README.md`,
`docs/backlog.md`, and the run artifacts.

The baseline was green before review: `python3 run_tests.py` gave
`tests: 3264 tests across 106 modules in 14.3s on 8 workers, 0 problem(s)`,
and lint and gates were clean.

Probing used real runs of `pr_body_preflight.preflight(...)` and of the
registered command. Shapes tried: odd quoting, `--body=` and `-b` joined
forms, repeated flags, `;` `||` `|` compounds, newlines, `gh -R x pr create`,
`GH_REPO=x`, `env gh`, an echo or a heredoc of another command, very long
commands, non-UTF-8 stdin and files, malformed JSON, and a body file that
is a directory, a symlink, unreadable, `/dev/stdin` or `/dev/zero`, or
sits under a cwd that does not exist.

## Findings

### Critical: text the shell never runs is parsed as commands, so a plain heredoc or a comment can trigger a false block

- Scenario: the hook masks only `$(cat <<D … D)` substitutions. It never
  masks a plain heredoc's body (`cat > f <<'EOF'`, `git commit -F - <<'EOF'`,
  `python3 - <<'EOF'`), and it sets `commenters=""`. shlex splits on
  newlines and control operators, so a heredoc line or a comment tail that
  reads like `gh pr create --body <literal>` gets judged as a command.
  Reproduced:

  ```
  cat > notes.md <<'EOF'
  Example:
    gh pr create --title x --body "WIP"
  EOF
  → (2, ['B: PR body cites no work-order id', 'B: PR body has no Closes #N link', 'pr-body-preflight: the body contract is docs/kb/pr-body-contract.md'])

  git commit -F - <<'EOF' … gh pr create --body "fix stuff" is refused now … EOF   → exit 2, same strings
  cat <<'EOF' > x … X=1 gh pr create --body 'nope' … EOF                           → exit 2, same strings
  true # later ; gh pr create --body 'bad'                                         → exit 2, same strings
  ```

  None of these commands runs `gh pr create`, so the session is blocked
  from writing a file or making a commit. The refusal names detector B,
  which teaches the session to stop using Bash heredocs. The Owner's own
  CLAUDE.md recommends Bash heredocs for writing files. The risk is
  highest when writing docs or tests about this hook or about PR bodies.
- Frequency, so the Owner can weigh the grade: none of the 9,084
  historical Bash commands in this project's transcripts hit it. That
  replay gave 2 exit-2 verdicts, and both were real `gh pr create`
  commands whose bodies lacked a closing line (true positives). Two things
  keep it rare today. Any apostrophe in a heredoc body makes shlex raise
  `No closing quotation`, which fails open. And the trigger needs a
  heredoc line that starts with `gh pr create` and carries a literal
  failing body.
- Fix direction (route to Implement; the architecture's step 2 changes):
  before tokenizing, cut every heredoc body from the raw string, not only
  `$(cat <<…)` ones. Find the `<<[-]?['"]?D['"]?` operator, then drop the
  lines up to the delimiter line. Also strip word-start `#` comments to
  the end of the line. Add both shapes above as replay fixtures that
  expect exit 0.
- Standard: none.
- Decision: **unfixed. Routed to Implement, re-verify after. This blocks
  Ship.**

### Critical (fixed): an unquoted heredoc body with a backslash-newline was refused although B accepts it

- Scenario: in an unquoted-delimiter heredoc the shell joins a
  backslash-newline. The hook judged the raw text:

  ```
  gh pr create --title x --body "$(cat <<EOF
  No work order: probe
  fixes the bug. Closes \
  #12
  EOF
  )"
  before → (2, ['B: PR body has no Closes #N link', 'pr-body-preflight: the body contract is docs/kb/pr-body-contract.md'])
  bash renders the body as 'No work order: probe\nfixes the bug. Closes #12\n' → gates.pr_body_problems → []
  ```

- Fix: commit `eacc548`, test-first. A backslash now makes an unquoted
  heredoc body unreadable, the same as `$` and a backtick, and the note
  reads `an unquoted heredoc body holds $, a backtick or a backslash`.
  architecture.md step 2 is amended to match. RED: the new test
  `test_unquoted_delimiter_with_a_backslash_fails_open` failed with
  `(2, ['B: PR body has no Closes #N link', …]) != (0, [note…])`. GREEN:
  `Ran 43 tests … OK`. Full suite:
  `tests: 3265 tests across 106 modules in 14.1s on 8 workers, 0 problem(s)`.
  After the fix the probe gives `(0, ['pr-body-preflight: not checked —
  an unquoted heredoc body holds $, a backtick or a backslash'])`.
- Standard: none.
- Decision: fixed.

### Major: the hook judges B's contract on PRs for other repositories

- Scenario: `-R`/`--repo` is skipped as an ordinary value flag, and leading
  `NAME=value` assignments are skipped, so `GH_REPO` is ignored too. A PR
  opened from this repo's sessions into a repository without detector B
  is still refused:

  ```
  gh pr create -R mattbutlerengineering/eat-sheet --title x --body 'fix login'  → exit 2, B's two strings
  GH_REPO=other/repo gh pr create --title x --body 'fix'                         → exit 2
  cd ../eat-sheet && gh pr create --title x --body 'fix'                         → exit 2
  ```

  The PRD scopes the hook to "a session in this repo". Its rule is this
  repo's CI rule. A stamped repo also runs B, so for those targets the
  refusal is right. For any other repo it is a false block on a command
  that would succeed and stay green. The architecture does not mention
  `-R` or `GH_REPO`. No historical command hit this.
- Fix direction: fail open with a note when `-R`/`--repo` or a leading
  `GH_REPO=` names anything other than this repo. A `cd` elsewhere can't
  be resolved cheaply. Leave it judged and record that as an accepted
  limit in the architecture.
- Standard: none.
- Decision: open. Recommended to go with the critical fix in the same
  Implement re-entry, since it is small. The Owner may defer it.

### Major: real coverage is about 4%: most historical `gh pr create` commands go unjudged

- Scenario: replaying the 210 historical Bash commands that contain
  `pr create`:

  ```
  74 a body file is read only from the first command
  61 cannot parse the command: No closing quotation
  44 no --body or --body-file
  13 the body holds $ or a backtick the hook cannot expand
   7 judged-pass
   7 saw "gh pr create" but found no such command
   2 exit2
   2 no body file at <scratchpad path>
  ```

  Only 9 of 210 were judged. The dominant shape in this repo, from
  2026-08-31 through 2026-10-16, is
  `cat > F <<'EOF' … EOF` then `gh pr create … --body-file F` in one
  Bash call. The 74 come from the first-command rule: the file is written
  by the same call, so at hook time it is absent or stale, and the rule is
  correct. The 61 are the unmasked heredoc bodies from the critical
  finding: an apostrophe in prose breaks shlex. Every PRD criterion is
  still met, because the criteria name literal and readable bodies. But
  the PRD's problem, unattended routines whose B goes red, is mostly
  produced in the shape the hook cannot see.
- Fix direction: the critical fix's heredoc masking turns the 61 into
  parses. A further step would cover the 74 and is a design change for
  Architect: bind a heredoc to the file it writes (`cat > F <<D`) and
  treat `--body-file F` later in the same compound as that heredoc's
  body.
- Standard: none.
- Decision: open, for the Owner. Recommend measuring again after the
  critical fix, then deciding whether the heredoc-to-file binding is a
  follow-up seed in `docs/backlog.md` rather than part of this run.

### Minor: single-quoted literal bodies holding `$` or a backtick go unchecked (Verify's reported gap)

- Scenario: shlex drops the quoting, so `--body 'costs $5'` can't be told
  apart from a real expansion. The hook returns `(0, ['… the body holds $
  or a backtick the hook cannot expand'])`. Verify saw this on 58 of 60
  real bodies in that synthetic shape. In the real history it is 13 of
  210. It fails open, so it is a coverage gap, never a false block.
  Covering it needs quote-aware tokenizing (shlex posix can't report which
  quote a character came from), which is a design change.
- Standard: none.
- Decision: deferred. It is fail-open by design, it is smaller in
  practice than the heredoc shapes above, and the documented heredoc
  shape is covered.

### Minor: a `--dry-run` with a failing body is refused

- Scenario: `gh pr create --dry-run --title x --body 'bad'` → exit 2. No
  PR is created. The same body would fail B if submitted, so the refusal
  is arguably useful, but it blocks a preview.
- Standard: none.
- Decision: deferred. The verdict is true of the body, and the block
  costs one edit.

### Minor: pathological command sizes run past the 10 s timeout

- Scenario: through the registered command, a 1 MB single-word command
  that contains the three trigger words took 9,306 ms, because shlex
  builds a token one character at a time. 20,000 unclosed `$(cat <<X`
  openings (200 KB) took 21,331 ms, because `_heredoc_at` rescans to the
  end for each opening. Both exit 0. Past 10 s, the architecture expects
  Claude Code to treat the timeout as a non-blocking error. That claim
  was not observed in this review. Realistic sizes are fast: a 200 KB
  heredoc file write took 77 ms in-process, and 50,000 `--label` flags
  took 237 ms end to end.
- Standard: none.
- Decision: deferred. No realistic command reaches these sizes, and both
  cases fail open, or time out, which also fails open.

### Minor: every Bash call pays a Python start-up

- Scenario: the hook runs on every Bash call. Measured through the
  registered command: a non-candidate (`ls -la`) took a median 33.9 ms
  (max 35.1); a judged candidate took a median 50.2 ms (max 53.6).
  Verify did not measure this. It is fine against the 10 s timeout. It is
  a fixed tax on every Bash call in this repo's sessions and routines.
- Standard: none.
- Decision: deferred. The cost is acceptable, and a shell-side
  pre-filter would have to consume stdin before Python could read it.

## Passes with no findings

- **Correctness**, apart from the findings above: joined `--body=` and `-b…`,
  `|`/`||`/`;` compounds, repeated body flags (note), `--title=--body`,
  an unclosed quote (note), `echo "gh pr create …"` and bare
  `echo gh pr create …` (both pass through), malformed JSON, a JSON list,
  a non-string command, empty stdin, and non-UTF-8 stdin
  (`UnicodeDecodeError` note, exit 0). All behaved as designed. Body-file
  reads cover a symlink to a good body (judged, pass), a directory, a
  missing cwd, `/dev/stdin` and `/dev/zero`. `cli.read_file`'s `is_file`
  guard returns "no body file" for the last four, so neither the hook's
  own consumed stdin nor an endless device is ever read. A mode-000 file
  and a non-UTF-8 file each give a note, exit 0.
- **Security**: there is no subprocess or shell execution. The hook reads
  only regular files that the command itself names as its body, through
  the guarded `cli.read_file`. It never echoes file content, only B's two
  fixed strings or a read problem naming the path. The catch-all in
  `preflight` and `main` turns any exception into exit 0, which is the
  PRD's fail-open contract. The registered command is quoted
  (`"$CLAUDE_PROJECT_DIR/…"`) and skips cleanly in a checkout without the
  script.
- **Design**: B's rule has one owner, `gates.pr_body_problems`, and
  `check_pr_traceability` delegates to it. The hook is root-only, matching
  ADR-0060 and the brief. The VERBS row matches
  `test_factory_cli`'s every-CLI-module rule and ADR-0054's convention
  column. Apart from the step-2 amendment made with the fix, the code
  matches architecture.md's pipeline. The `-R` gap is an unconsidered
  case, not a deviation.
- **Complexity**: nothing to cut. Each helper has one caller and owns one
  stage of the architecture's pipeline. `main`'s argv usage branch exists
  for the VERBS rule, and its `stdin` parameter for the tests. The diff
  adds no `lean:` markers.
- **ADR compliance**: `adr_status.py .` lists 106 ADRs. The ones that
  bear on this diff hold. ADR-0021 and ADR-0037 to ADR-0040: no new
  shared module; the hook is a leaf caller. ADR-0050 and ADR-0060: the
  payload copy of `gates.py` is regenerated and detector E is clean; the
  hook is root-only because no payload tool imports it. ADR-0051: the
  hook's lines carry their own `pr-body-preflight:` label, and B's
  strings are unchanged. ADR-0075: the body file goes through
  `cli.read_file`, and the hook keeps its own missing-file arm, per
  decision 5. ADR-0091: only its status line is edited, with the change
  carried by a new ADR. ADR-0095: `.claude-plugin/plugin.json` is
  untouched.
- **ADR test**: ADR-0106 is provisional. It moves an accepted ADR's
  measurement table, so it holds under this repo's supersede-don't-rewrite
  rule and ADR-0097's precedent. The other decisions record themselves in
  architecture.md and fail the "hard to reverse" leg, so no ADR is owed.
  Those are registering a checked-in PreToolUse hook on every Bash call
  (reverted by deleting one settings block), the fail-open policy, and
  the first-command body-file rule.
- **Standards**: stdlib-only holds (`json`, `re`, `shlex`, `sys`,
  `pathlib`, plus repo modules). adr0032-one-way-mirror is not touched.
- **Domain passes**: none selected.

## Verdict

**Not ready to ship.** One critical finding is unfixed: plain heredoc
bodies and comment tails are tokenized as commands, which can false-block
a command that never runs `gh pr create`. Route it to Implement, fix it
test-first with the two reproductions above as fixtures, then re-verify.
The second critical, the unquoted-heredoc backslash false block, is
fixed in `eacc548`. Two majors need an Owner decision before Ship, to fix
or defer: the other-repository false block, recommended for the same
re-entry, and the about-4% real coverage, recommended for a re-measure
after the fix. The four minors are deferred with reasons.

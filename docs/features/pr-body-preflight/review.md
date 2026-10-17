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
  - "Re-review 2026-10-16: Severity follows the brief's definition literally. Every exit 2 on a body B accepts, on a command whose `gh pr create` never runs, or on a PR for another repository is critical, whatever its frequency. Three of the five new criticals need shapes that no observed command contains, and their frequency is stated beside the grade so the Owner can downgrade."
  - "Re-review 2026-10-16: Each new critical was fixed here, not routed, because each fix is one condition (the line-continuation fix is the same condition in the two contexts the shell applies it in) with its own test, written first and seen failing. The continuation fix changes what gets judged (8 to 40 of 210 historical `pr create` commands), so every exit 2 it produces was checked against B on the body as bash renders it before the commit."
  - "Re-review 2026-10-16: Whether `gh` runs was decided by executing each probe under bash and zsh, with a stub `gh` first on PATH, in a scratchpad directory. Transcript commands were never executed. They were only replayed through `preflight()`, and their quoted-heredoc bodies were rendered by bash's `cat`."
  - "Re-review 2026-10-16: architecture.md step 2b gets a dated amendment line for the three fix commits. It is committed with review.md, because an undocumented deviation would itself be a design finding."
  - "Re-review 2026-10-16: Findings 4 to 8 keep the deferral the Owner authorized for the review fix loop (breakdown.md Milestone 3). Their status is restated here with re-measured numbers, not re-decided."
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

## Re-review 2026-10-16

### Scope

This pass covers the review fix loop: `git diff 4fd75d4..HEAD --
pr_body_preflight.py tests/` (commit `8189351`), a full read of the
current `pr_body_preflight.py`, and the amendments to architecture.md
(steps 2b and 8, with their accepted limits). It also covers this pass's
own fix commits `0715189`, `b745415` and `b276426`. Probes ran against
the module in-process. Each "does `gh` run" claim was checked by
executing the probe under bash and zsh with a stub `gh` first on PATH.
The repository logic was probed in hand-built checkouts: two remotes
(ssh and https, mixed case), a worktree `.git` file with `commondir`, a
`.git` directory with no config, a random-bytes config, a garbage `.git`
file, a symlinked cwd, and an `ssh://` remote.

### Prior findings, re-judged

- **Finding 1 (critical, heredoc/comment false block): closed.** All four
  reproductions now give `(0, ['… saw "gh pr create" but found no such
  command'])`. So do nested heredocs, a delimiter-like line inside the
  body (`  EOF`, `EOFX`), two heredocs on one line, `<<-` with tabs, a
  heredoc in `"$( )"`, in `<( )`, in a function body and in a `for`
  loop, and `cat <<E | grep x` and `cat <<E && ls`. Each matches bash,
  where `gh` never runs. `<<EOF` inside single or double quotes, `#` in
  a URL, `${#x}`, `$#`, `a#b`, `\#`, `$((1<<2))` and `<<<x` all leave a
  real `gh pr create` judged, as bash runs it. The pass found residual
  shapes of the same class, listed below under New findings, and fixed
  them.
- **Finding 3 (major, other-repository judging): closed.** `-R`/`--repo`
  in every spelling, `GH_REPO` (prefix, `export`, environment) and a
  `cd` out of the checkout all fail open, with `the PR targets <v>, not
  this repository` or `a cd before gh pr create leaves this repository`.
  This repository named in any case, as `owner/name`, as a URL or as
  `host/owner/name` is still judged. That holds from a worktree (whose
  `.git` file is followed through `commondir`) and from a symlinked
  cwd. A `.git` with no config, a corrupt config, a garbage `.git`
  file, or an unreadable remote fails open with `… remote cannot be
  read` or `… cannot place`. One residual shape, a continued line
  carrying `-R`, was fixed (the line-continuation critical below). One
  residual is a minor (every remote counts as this repository).
- **Findings 4 to 8: still deferred, as the Owner authorized for the fix
  loop** (breakdown.md Milestone 3). Re-measured:
  - 4 (major, coverage): of the 210 historical `pr create` commands,
    40 are now judged (32 pass, 8 exit 2), up from 8. That is about
    19%. The rise comes from the line-continuation fix. The dominant gap is
    unchanged: 138 are `a body file is read only from the first
    command`, so binding a heredoc to the `--body-file` it writes is
    still the lever.
  - 5 (minor, single-quoted `$`): unchanged. The merged-PR replay is
    still 58 of 60 in the single-quoted form.
  - 6 (minor, `--dry-run` refused): unchanged.
  - 7 (minor, pathological sizes): unchanged in kind. A 1 MB command
    takes 1.2 to 2.3 s in-process, against 1.1 s before the unrun pass.
    This pass's own `${ }` fix briefly made 20,000 `${a ` openings take
    11.8 s. `b745415` brought that back to 68 ms; see the quadratic
    `${ }` minor below.
  - 8 (minor, start-up per Bash call): unchanged, since the
    non-candidate path is untouched.

### New findings

#### Critical (fixed): a backslash-newline split one `gh pr create` in two, and kept itself inside a double-quoted body

- Scenario: shlex saw a line continuation as a newline token, so the
  hook judged the first line as the whole command. This predates the
  fix loop, and the first review missed it.

  ```
  gh pr create --body bad \<newline>  --web
      → (2, [B's two strings]); the design says --web fails open
  gh pr create --body fix \<newline>  -R other/repo
      → (2, …); the PR is for another repository (finding 3's class)
  gh pr create --body "WO-0003 per breakdown. Closes \<newline>#108"
      → (2, ['B: PR body has no Closes #N link', …])
      bash passes the body as "… Closes #108", and B accepts it
  ```

  The common multi-line form `gh pr create \<newline> --title … \<newline>
  --body …` was also never judged (`no --body or --body-file`).
- Fix: `b276426`, test-first. `_Unrun` drops a backslash-newline in
  unquoted and double-quoted text, as the shell does. Single quotes keep
  it. RED: `test_a_line_continuation_joins_the_lines` failed with
  `(2, ['B: PR body cites no work-order id', …]) != (0, ['… --web leaves
  the body to gh'])`. GREEN: `Ran 67 tests … OK`. After the fix:
  `--web` → the `--web` note, `-R other/repo` → `the PR targets
  other/repo, not this repository`, and the `Closes \<newline>#108`
  body → `(0, [])`. The transcript replay's exit 2 count went from 2 to
  8. All 8 agree with `gates.pr_body_problems` on the bash-rendered
  body. Each is a `gh pr create` in this repository, either from its
  own cwd, after `cd /Users/mbutler/github/skills`, or with `-R
  mattbutlerengineering/skills`. The merged-PR replay still has 0
  refusals in 180 invocations.
- Decision: fixed.

#### Critical (fixed): a heredoc inside backticks reached the tokenizer as commands

- Scenario: `_Unrun` kept a backtick span whole, and shlex does not know
  backticks. `` x=`cat <<'EOF'⏎gh pr create --body bad⏎EOF⏎` `` → exit 2.
  bash and zsh: `gh` never runs. This is the residual of finding 1. It
  is rare, since backticks are legacy syntax, but it is a plain,
  non-adversarial shape.
- Fix: `0715189`. A backtick span holding `<<` raises, so the command
  fails open with `cannot parse the command: a heredoc inside
  backticks`. RED: `test_a_heredoc_inside_backticks_fails_open` failed
  for `<<EOF` and `<<'EOF'` (exit 2). GREEN with the suite.
- Decision: fixed.

#### Critical (fixed, frequency ≈ 0): `#` right after a line continuation was kept as text

- Scenario: `echo a \⏎# ; gh pr create --body bad` → exit 2. The shell
  joins the lines into `echo a # ; …`, a comment, so `gh` never runs.
  No observed command has this shape.
- Fix: `0715189` kept the word boundary across the join, and
  `b276426`'s removal of the pair subsumes that. RED:
  `test_a_comment_after_a_line_continuation_is_a_comment` failed (exit
  2). GREEN. `--body x\⏎#1` is still judged as `x#1`.
- Decision: fixed.

#### Critical (fixed, frequency ≈ 0): a `<<` shift in a `(( ))` command was read as a heredoc

- Scenario: `((y = 1<<2))⏎echo '⏎2⏎gh pr create --body bad⏎' "' #"` →
  exit 2. The fake heredoc's "body" swallowed the quote that hides the
  `gh` line from the shell. This needs a hand-built quote resync. The
  plain shape `(( n <<= 1 ))⏎gh pr create …` failed open, which lost
  coverage.
- Fix: `0715189`. `((` at a word start is kept whole, like `$(( ))`.
  RED: `test_an_arithmetic_command_shift_is_not_a_heredoc` failed (exit
  2). GREEN. The plain shape is now judged. Accepted limit: `(( ))`
  inside `$( )` miscounts the depth and fails open as unclosed.
- Decision: fixed.

#### Critical (fixed, frequency ≈ 0): a blank-then-`#` inside `${ }` was cut as a comment

- Scenario: `echo ${x:- #'⏎gh pr create --body bad⏎' "' #"}` → exit 2.
  In bash, `#` inside `${ }` is not a comment, and the `gh` line sits
  in single quotes. This also needs a hand-built quote resync.
- Fix: `0715189`, then `b745415`. A `#` comment or `<<` inside an
  unquoted `${ }` raises, so the command fails open with `a ${ } holding
  # or << the hook cannot read`. A depth counter tracks this. RED:
  `test_a_parameter_expansion_holding_a_comment_or_heredoc_fails_open`
  failed (exit 2). GREEN. `${#x}` is still plain text.
- Decision: fixed.

#### Minor (fixed in this pass): this pass's first `${ }` check was quadratic

- Scenario: `0715189` searched from each `${` to the next `}`. 20,000
  `${a ` openings (80 KB) took 11,766 ms in-process, past the 10 s hook
  timeout. Before that commit the same input took 73 ms. The input fails
  open either way.
- Fix: `b745415` replaced the search with a depth counter. Timing is
  68 ms, with the same verdicts on every test and on the 9,098-command
  replay. There is no timing test, because one would be flaky. The
  measurement is recorded here.
- Decision: fixed.

#### Minor: every remote counts as "this repository"

- Scenario: step 8 accepts a named target that matches any `[remote …]`
  URL. In a checkout with an `upstream` remote for a repository that
  does not run B, `gh pr create -R up/stream --body x` is judged by B.
  Probed in a temp checkout: exit 2. This clone has exactly one remote
  (`origin`), so there is no trigger today. A fork of this repository
  would have `upstream` pointing at this repository, which does run B.
- Decision: deferred. No trigger exists today. Narrowing to `origin`
  would break a fork's `-R upstream`, which is correctly judged.

### Passes

- **Security**: no findings. The new reads are the `.git` file, a
  `commondir`, and a git config. All go through `cli.read_file`, whose
  `is_file` guard refuses directories, FIFOs and devices. Contents are
  parsed only for `url`/`pushurl` lines and are never echoed. A note
  echoes only the command's own `-R`/`GH_REPO` value. A `gitdir:` or
  `commondir` can point anywhere, but the read is read-only, and the
  `.git` entry is the user's own: git refuses to check out a tracked
  `.git` path. `cd` targets get only `is_dir`. There is no size cap on
  these reads, which matches the body-file read. There is still no
  subprocess or shell execution.
- **Complexity**: 633 lines, under the 800-line ceiling. Each helper has
  one caller, so no cut-list line applies. The step-8 code (about 110
  lines) is what the Owner asked for. One concern is about shape, not
  size, so it goes to `deepen` and is not refactored here: the command
  is lexed three times with overlapping quote knowledge (the
  `HEREDOC_OPEN` regex mask, `_Unrun`, then shlex). Every accepted
  limit in step 2b, and the six residuals above, sit in the gaps
  between those three lexers. A single quote-aware pass that emits
  words would retire `_mask_heredocs`, `_heredoc_at` and the shlex
  configuration.
- **Design**: the code matches architecture.md steps 2b and 8. This
  pass's three fix commits are recorded as a dated amendment line in
  step 2b.
- **ADR compliance**: the delta touches only `pr_body_preflight.py`, its
  tests and run documents. ADR-0075 holds, since every new file read
  goes through `cli.read_file`. The module is still root-only
  (ADR-0060), and `.claude-plugin/plugin.json` is untouched (ADR-0095).
  No new decision passes the ADR test: the target-repository rule is
  reversible and recorded in the architecture.
- **Standards**: stdlib-only holds (`os` added).

### Verification after this pass

`python3 run_tests.py`: `tests: 3289 tests across 106 modules in 15.3s
on 8 workers, 0 problem(s)`. `python3 lint.py`: `lint: 0 problem(s)
across 34 skills`. The transcript replay (9,098 Bash commands, 42
files) gives exit 2 exactly 8 times, and all 8 agree with B. The
merged-PR replay gives 0 refusals in 180 invocations.

### Re-review verdict

**No critical or high finding is unfixed.** Findings 1 and 3 are
closed. Seven new findings came from this pass. Five are criticals, and the
line-continuation one predates the fix loop. One is a minor of this
pass's own making. All six are fixed test-first in `0715189`,
`b745415` and `b276426`. The seventh is a minor. Finding 4
(major, coverage, now about 19%) and the minors 5 to 8 stay deferred, as
the Owner authorized. That seventh finding, every remote counting as
this repository, is deferred with its reason. Ready for Ship. The one-line
`deepen` hand-off on the three-lexer shape is advisory.

---
stage: architect
run: feature:pr-body-preflight
date: 2026-10-16
ux: skipped — CLI hook only (a PreToolUse hook on Bash); no screens or flows.
assumptions:
  - "No live interview: every trade-off below was settled from autorun-brief.md and the code, taking the recommended option. Nothing the brief left open needed a guess on an irreversible or expensive choice."
  - "Hook contract read from the official security-guidance plugin's hooks.json and script in the local plugin cache (matcher on the tool name, type command, JSON on stdin with tool_name and tool_input, exit 2 blocks and feeds stderr back, exit 0 proceeds), plus the user's own settings.json timeout field. No field is used that neither shows."
  - "Recommended default taken: the hook is a root-level script (pr_body_preflight.py), not under .claude/hooks/. That matches every other root-only tool here (kb.py, one_owner.py, run_tests.py), lets it import gates with no sys.path change, and keeps it inside one_owner.py's scan."
  - "Recommended default taken: a body file (--body-file, or $(cat file)) is read only when gh pr create is the first simple command of its compound command. Any earlier segment could write that file or change the directory, so the file on disk is not known to be the body gh will send."
  - "Re-entry 2026-10-16: the hook is a factory verb because tests/test_factory_cli.py derives the verb set from every root __main__ guard (ADR-0054); disguising the guard to dodge the scan was not considered a real option. The registered hook command still runs the script by filename, since ADR-0054 decides that files invoke tools by filename and the front door's callers are humans."
  - "Re-entry 2026-10-16: an argv given to main (only a human can give one; the registered command passes none) prints usage on stderr and exits 0, not 2, so the rule that only a judged failing body exits 2 has no exception."
  - "Re-entry 2026-10-16: the dual-membership growth is recorded in ADR-0106 (provisional), shaped on ADR-0097, and ADR-0091's status line and index row are updated to name it, as the ADR index's own rule asks. ADR-0097 is left unedited: its decision stands and only its count moves."
  - "Re-entry 2026-10-16: the structural identity test (pr_body_preflight.pr_body_problems is gates.pr_body_problems) contradicts the lazy import of gates that the cost line asks for, since a function-level import leaves no module attribute. The lazy import is kept and the identity test is replaced by a delegation test, below."
---

# Architecture: PR-body preflight hook

## Approach

A root-only stdlib script, `pr_body_preflight.py`, registered in the
checked-in `.claude/settings.json` as a `PreToolUse` hook on `Bash`. It
reads the hook JSON from stdin. A cheap substring pre-filter returns 0
for any command that cannot be a `gh pr create`, before anything is
imported. For a candidate, the script locates each `gh pr create` simple
command, recovers its body only from a shape it can read exactly, and
judges that body with a new body-only function in `gates.py`,
`pr_body_problems(body)`. That function is lifted verbatim out of
`check_pr_traceability`, which now calls it. The hook blocks (exit 2,
B's strings on stderr) only on a body it read and judged failing. Any
other outcome is exit 0, and the script's whole body sits in a
catch-all so that a crash also exits 0. The second shape considered was
a hook that synthesises a CI event file and calls
`check_pr_traceability` through `FACTORY_EVENT_PATH`. It needs no
`gates.py` change, but it writes a temp file on every judged call and
couples the hook to `cli.read_event`'s environment names. The extraction
is a five-line move, and it gives B one owner of the rule and of its
strings.

## Components

### `gates.pr_body_problems` (policy)

- Responsibility: the one statement of detector B's body rule. Given a
  body string, it returns the B problem strings, the same two
  `check_pr_traceability` emits today, in the same order. The regexes
  stay where they are: `WO_TOKEN` and `CLOSES_TOKEN` in
  `knowledge_plane.py`, `NO_WO_DECLARATION` in `gates.py`.
- Collaborators: `check_pr_traceability`, which keeps the event read,
  the silent skip and the `B: <error>` path and delegates the body to
  this function; and the hook.

### `pr_body_preflight.py` (adapter, root-only)

- Responsibility: translate one hook payload into one verdict. The
  stages are: pre-filter, mask heredocs, tokenize, split on control
  operators, find each `gh pr create`, recover its body, then judge it
  or call it unreadable.
- Collaborators: `gates.pr_body_problems`, and `cli.read_file` for body
  files (ADR-0075's guarded read). It is not in `factory_init.MIRRORS`
  and no payload tool imports it, so it stays root-only (ADR-0060's
  rule).

### `.claude/settings.json` registration

- Responsibility: wire the hook. The file is `{}` today and becomes:

  ```json
  {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{
    "type": "command",
    "command": "[ ! -f \"$CLAUDE_PROJECT_DIR/pr_body_preflight.py\" ] || python3 \"$CLAUDE_PROJECT_DIR/pr_body_preflight.py\"",
    "timeout": 10}]}]}}
  ```

  The `[ ! -f … ] ||` guard is there because Python exits **2** when it
  cannot open its script. Suppose a session's settings were loaded and
  the checkout then moved to a commit without the script (a
  `git checkout` of an older branch mid-session). A bare `python3 path`
  would then block every Bash call, including the checkout back. With
  the guard, a missing script is exit 0.

## Data model

There is no storage. The one record is the per-command verdict the
adapter derives internally:

- `judged(body, problems)`: problems is `pr_body_problems(body)`, and an
  empty list passes;
- `unreadable(reason)`: a one-line reason for the stderr note.

The hook's exit code is decided by the set of verdicts: exit 2 if any
`judged` verdict carries problems, else exit 0. One compound command
can hold several `gh pr create` calls, and each one is judged.

## Interfaces & contracts

### `gates.pr_body_problems(body: str) -> list[str]`

- Input: the body text, where `""` stands for a missing body
  (`check_pr_traceability` keeps its `or ""`).
- Output: a subset, in order, of `"B: PR body cites no work-order id"`
  and `"B: PR body has no Closes #N link"`. The strings are exact and
  unchanged.
- Failure modes: none. It is a pure function over a string.
- Accepted behaviour changes from the refactor: none. Run old and new B
  over any event and they give the same output, because the body logic
  is moved, not edited. The existing `TestPrTraceability` cases and
  `gates_selftest`'s B cases pin this unchanged. `gates.py` is mirrored
  with the identity transform, so the payload copy changes and
  `python3 factory_init.py update-manifest` runs with the change
  (`docs/kb/manifest-regen.md`).

### Hook process: stdin JSON in, exit code and stderr out

- Input: the Claude Code `PreToolUse` payload. It reads
  `tool_input.command` (a string) and `cwd`. Every other field is
  ignored. If the payload is not JSON, is not an object, or has no
  string command, the result is exit 0 with no note.
- Output:
  - exit 2, with stderr carrying each judged-failing body's B strings
    one per line, then one line pointing at `docs/kb/pr-body-contract.md`;
  - exit 0, with a one-line `pr-body-preflight: not checked — <reason>`
    note per unreadable `gh pr create`;
  - exit 0 and silence for everything else.

  Claude Code shows exit-0 stderr only in the transcript, so a note is
  for a human reading the log, not a message to the model. That is
  acceptable, because CI's B still judges that PR.
- Failure modes: every exception after stdin is read, including an
  `ImportError` or `SyntaxError` from `gates` mid-edit, is caught and
  becomes exit 0 with a note. The 10 s timeout also fails open: Claude
  Code treats a hook timeout as a non-blocking error. Retrying is safe,
  since the hook has no side effects and reads files only.
- Cost: one Python start-up (about 20 ms) on every Bash call. `gates`
  (about 60 ms measured) is imported only once the pre-filter matches.

### Body recovery (internal, pinned by the replay fixtures)

The steps run in this order:

1. **Pre-filter.** If `gh`, `pr` and `create` are not all substrings of
   the command, exit 0 at once.
2. **Mask heredoc substitutions on the raw string.** Each
   `$(cat <<'D'` / `<<"D"` / `<<D` / `<<-D` … `\nD\n)` is cut out and
   replaced by a placeholder word. Its body text is kept verbatim. This
   happens before tokenizing because `shlex` does not know a `$( )`
   opens a new quoting context: the probe turned `it's "q"` inside a
   heredoc into `it's q`. A body with a quoted delimiter is literal. A
   body with an unquoted delimiter is literal only if it has no `$`, no
   backtick and no backslash; otherwise it is unreadable (the shell would
   expand it, or join a backslash-newline; amended at Review).
   *(Amended 2026-10-16, review fix loop: step 2b below now runs between
   this step and step 3.)*
3. **Tokenize.** Use `shlex.shlex(posix=True,
   punctuation_chars=";&|()<>\n")`, with `whitespace_split=True`,
   `whitespace=" \t"` and `commenters=""`. Probed: with the defaults, a
   newline is whitespace (it merges two commands), and `#` ends a word
   mid-token (`-b a#1` loses `#1`). A `ValueError` (an unclosed quote)
   makes every candidate unreadable. *(Amended 2026-10-16: `commenters`
   stays empty, and comments are cut in step 2b instead, where quoting
   and word starts are known.)*
4. **Split** on the operator tokens (`&&`, `||`, `;`, `|`, `&`, newline,
   parentheses). A simple command is a `gh pr create` when its words,
   after leading `NAME=value` assignments, start with `gh` (or a path
   ending in `/gh`), `pr`, `create`. Prefixes such as `bash -c`, `env`,
   `xargs` or `command` are not looked through. *(Amended 2026-10-16: the
   skipped assignments are still read for `GH_REPO` in step 8.)* If the pre-filter
   matched but no simple command qualifies, there is one note
   (`saw "gh pr create" but found no such command`) and exit 0.
5. **Find the body source** among the args:
   - `--body V`, `--body=V`, `-b V`, `-bV` and `-b=V` give a body value;
   - `--body-file`, `-F` and their joined forms give a file;
   - `--fill`, `--fill-first`, `--fill-verbose`, `--web`/`-w`,
     `--editor`/`-e`, `--template`/`-T` and `--recover` make the body
     unreadable;
   - no body source at all, or more than one, is unreadable;
   - a single-dash cluster of more than two characters that holds `b`
     or `F` anywhere but second place (`-db`) is unreadable.
6. **Resolve the value.**
   - A placeholder alone is that heredoc's body.
   - A value containing `$` or a backtick is unreadable (a variable,
     `$'…'`, or a substitution the hook cannot expand), except for the
     exact shape `$(cat PATH)` or `$(< PATH)` with a plain path, which
     is treated as a body file.
   - Anything else is the literal body.
7. **Read a body file**, only if the `gh pr create` is the first simple
   command of the compound (see the assumptions). `-` (stdin) is
   unreadable. A relative path resolves against the payload `cwd`, and
   with no `cwd` it is unreadable. The file is read with
   `cli.read_file(path, shown, str)`. Absent, unreadable or non-UTF-8
   is unreadable, with the problem text as the reason.

#### Amended 2026-10-16 (review fix loop: review findings 1 and 3)

Review found that text the shell never runs reached the tokenizer, and
that a PR aimed at another repository was judged by this repository's
rule. Both break the guarantee: exit 2 only on a body read and judged
failing, in a `gh pr create` that will run against this repository. Two
steps are added; steps 1 to 7 above are otherwise unchanged.

2b. **Cut the text the shell never runs** (`_Unrun`, after step 2,
    before step 3). One quote-aware pass over the masked string tracks
    single quotes, `$'…'`, double quotes, backticks, `$( … )` (unquoted
    again inside double quotes) and `$(( … ))`. In unquoted text:
    - a `#` at a word start (string start, after unescaped whitespace or
      an operator character) drops to the end of the line; a `#`
      mid-word (`a#1`, `=#1`, after an escaped space) is kept;
    - `<<` (not `<<<`, not inside `$(( ))`) is a heredoc operator:
      optional `-`, blanks, then a delimiter word whose quotes and
      backslashes are removed (`<<'EOF'`, `<<"EOF"`, `<<\EOF`,
      `<<E'O'F`). The operator and its word stay, so step 4 drops them as
      a redirection. At the end of that line, each queued body and its
      delimiter line (tab-stripped for `<<-`) is cut. A body whose
      delimiter never comes runs to the end, as in bash.
    - It raises, and every candidate becomes unreadable, on an unclosed
      quote (`No closing quotation`, the same note shlex gave), an
      unclosed substitution or backtick (the shell rejects both, so no
      `gh` runs), a delimiter holding `$` or a backtick, or `<<` with no
      word.
    Accepted limits, each failing open or unchanged from before: a
    `case` pattern's `)` inside `$( )` closes it early, and shlex still
    knows nothing of `$'…'` or of quotes nested in `"$( )"`.
    *(Amended 2026-10-16, re-review, commits `0715189`, `b745415` and
    `b276426`:)* a backslash-newline outside single quotes is removed,
    as the shell removes it, so a continued `gh pr create` stays one
    command, a double-quoted body is joined, and a `#` right after the
    join is a comment exactly when it would be without it. A
    `(( … ))` command at a word start is kept whole, like `$(( … ))`.
    Two shapes raise, and so fail open: a backtick span holding `<<` (a
    heredoc inside backticks), and a `#` comment or `<<` inside an
    unquoted `${ … }`, tracked by a depth counter so the pass stays
    linear. Accepted limit: a `(( ))` inside `$( )` miscounts the
    substitution's depth and fails open as unclosed.

8. **Check the target repository** (after the body is recovered, so
   every step-5-to-7 note is unchanged; before judging).
   - Named targets: every `-R`/`--repo` value in any spelling
     (`-R v`, `-Rv`, `-R=v`, `--repo v`, `--repo=v`), plus `GH_REPO` as gh
     would see it: the hook's environment (`main` passes `os.environ`;
     `preflight(payload_text, environ=None)` treats None as empty), then
     each earlier `GH_REPO=` word in the compound (`export GH_REPO=…`),
     then the command's own prefix. The last one wins and an empty value
     means unset.
   - "This repository" is decided without git or network: the cwd's
     checkout is found by walking up to `.git`. A worktree's `.git` file
     is followed through its `gitdir` and `commondir` to the clone's one
     config. That config's `[remote …]` `url`/`pushurl` values are
     parsed as `host/owner/name`, scp-like, https or ssh. A named target
     normalises the same way (a bare `owner/name` is on `github.com`) and
     is compared case-insensitively. A target not among them gives
     `the PR targets <v>, not this repository`. No cwd, no checkout or no
     parsable remote gives `the PR targets <v> and this repository's
     remote cannot be read`.
   - Directory changes: if any earlier simple command is `cd`, `pushd` or
     `popd`, each is applied in order from the payload cwd. Each takes
     exactly one plain argument: no option, no `~`, no `$` or backtick,
     and an existing directory. `popd` is never placed. When it cannot
     be placed, or the cwd has no checkout, the note is `a cd before gh
     pr create the hook cannot place`. A final directory whose checkout
     config differs from the cwd's gives `… leaves this repository`. A
     `cd` into a subdirectory or another worktree of the same clone
     stays judged. This supersedes Review's suggestion to leave `cd`
     judged as an accepted limit, because the Owner asked for it to fail
     open, and resolving it is a few `is_dir` and config lookups.
   - Accepted limit: the payload cwd itself is taken as this repository.
     A session whose shell already sits in another checkout, after a `cd`
     in an earlier Bash call, is still judged when its command names no
     other repository and changes no directory.

## Stack & dependencies

- Python 3 standard library only (`json`, `shlex`, `re`, `sys`,
  `pathlib`), as CLAUDE.md requires.
- Imports `gates` and `cli`, which already live at the root. No new
  shared module: the hook is the second caller of an existing function,
  and nothing gets a new seam.

## Test strategy

The tests go in `tests/test_pr_body_preflight.py`. The script exposes a
pure `main(stdin_text) -> (exit_code, stderr_lines)` plus a thin
`__main__`. *(Amended 2026-10-16: the pure seam is `preflight`, and
`main` takes `argv`; see "Amended 2026-10-16" under Decisions.)* Fixtures are complete hook payloads (JSON with
`tool_name: "Bash"`, `tool_input.command` and `cwd`), replayed through
`main`. Body files sit in a temp directory used as `cwd`. The cases are:

- a passing literal body: exit 0, silent;
- the work-order line missing, the closing line missing, and both
  missing: exit 2, with stderr lines equal to
  `gates.pr_body_problems(body)` for the same body;
- `--body-file` and `-F` with a real file (both pass and fail), and
  with a missing file (note);
- a quoted-delimiter heredoc body with inner `"` and `'` (judged), and
  an unquoted-delimiter heredoc holding `$X` (note);
- `$(cat file)`;
- a compound `cd x && gh pr create --body …` (judged), and the same
  with `--body-file` (note);
- two commands separated by a newline;
- `--fill`, `--web` and `--body-file -` (note, exit 0);
- an unclosed quote (exit 0);
- a non-gh command, `echo "gh pr create"` and
  `git commit -m "gh pr create"` (exit 0);
- a non-JSON payload (exit 0).

Two structural tests close the set. One subprocess run of the real
script through the exact command string in `.claude/settings.json`
(`CLAUDE_PROJECT_DIR` set to the repo root) proves the registration, the
exit-2 path and the guard. The guard is also run with a non-existent
`CLAUDE_PROJECT_DIR` and gives exit 0. The second test asserts that
`pr_body_preflight.pr_body_problems is gates.pr_body_problems`, so the
check has one owner *(amended 2026-10-16: replaced by a delegation
test; see below)*, and `python3 one_owner.py` is the review pre-pass
on top. `tests/test_gates.py` gains direct `pr_body_problems` cases
beside `TestPrTraceability`.

## Decisions & alternatives

- **Extract `gates.pr_body_problems`** over synthesising an event file
  for `check_pr_traceability`: that path writes a temp file on every
  judged call and couples the hook to `read_event`'s environment names.
  It also costs a payload and manifest regen, which is accepted.
- **Extract the function** over importing the three regexes into the
  hook: that would make a second owner of the rule and of B's strings.
- **Root-level `pr_body_preflight.py`** over `.claude/hooks/`: root is
  where root-only tools live, and imports work without a `sys.path`
  change.
- **Mask heredocs before `shlex`** over tokenizing first and
  pattern-matching the token: probed, `shlex` strips quotes inside
  `$( )`, which can turn `#12"` into `#12x` and lose B's word boundary.
  That is a false block.
- **Configured `shlex`** (newline as an operator, no commenters) over
  the defaults: probed, the defaults merge commands across newlines and
  cut `a#1` to `a`.
- **Body files read only from the first simple command** over reading
  them anywhere: an earlier segment may write the file, so a stale file
  could cause a false block.
- **Fail open on every unrecognised shape** over a fuller shell parser:
  a false block teaches sessions to route around the hook, and CI's B
  still catches whatever passes.
- **The `[ ! -f … ] ||` guard** over a bare `python3 path`: a bare call
  exits 2 on a missing script, which blocks every Bash call.
- **Exit-0 stderr notes** over JSON `permissionDecision` output: exit
  codes are the contract this machine's hooks already use, and a note
  needs no model-visible channel.

### Amended 2026-10-16 (Architect re-entry from Decompose)

Decompose found two pinned repo rules the design above did not account
for (`breakdown.md`, "Design gaps found"). A sweep of the other pinned
walks over root modules found a third conflict, inside this document.
The decisions above stand except where named here.

1. **Entry point: the hook is a `factory` verb, with an `argv` main
   and a separate pure seam.** `tests/test_factory_cli.py` (ADR-0054)
   requires one `factory.VERBS` row per root module that carries a
   `__main__` guard, named after the module, and a `main` whose first
   positional parameter is `argv` (or that has none at all).
   - `factory.VERBS` gains `"pr-body-preflight": ("pr_body_preflight",
     "argv")`. The module's docstring first line is the index line
     `factory.py help` prints, in the usual `pr-body-preflight: …`
     form.
   - The pure test seam is `preflight(payload_text: str) -> (int,
     list[str])`: the hook payload text in, the exit code and stderr
     lines out. Body-recovery steps 1 to 7 and the catch-all run inside
     it, so a `gates` failure is still exit 0 with a note when driven
     through the seam. It writes nothing and reads only body files.
   - `main(argv, stdin=None)` is the thin adapter. With a non-empty
     `argv` it prints the docstring usage to stderr and returns 0. A
     human is the only one who can pass an argument, and exit 2 would
     mean "block" to a hook. Otherwise it reads `stdin`, or
     `sys.stdin` when `stdin` is None (looked up at call time, not
     bound as a default), passes the text to `preflight`, writes the
     lines to stderr and returns the code. A failure reading stdin is
     exit 0 with a note. `__main__` is `sys.exit(main(sys.argv[1:]))`.
     The `stdin` keyword has a default, so the `argv` row stays
     correct. `fast_path.main(argv, git=…)` and
     `sweeps.main(argv, run=…)` are the precedent for keyword ports
     after `argv`.
   - The `.claude/settings.json` command is unchanged: it runs
     `pr_body_preflight.py` by filename, not
     `factory.py pr-body-preflight`. ADR-0054 decides that files invoke
     tools by filename and that the front door's callers are humans.
     Routing through the front door would also add `factory.py` and its
     import to every Bash call, and the `[ ! -f … ] ||` guard would have
     to cover two files.
   - Replay tests call `pr_body_preflight.preflight(json.dumps(payload))`
     and assert `(code, lines)`. One test drives
     `main([], stdin=io.StringIO(…))` and captures stderr. One drives
     `main(["x"])` and gets exit 0 with the usage text. The existing
     `TestVerbTableIsDerived` and `TestDispatch` cover the row with no
     new test.

2. **The dual-membership set grows by two pairs, recorded in
   ADR-0106.** `pr_body_preflight` imports the mirrored `gates`
   (`pr_body_problems`) and `cli` (`read_file`). That makes 43 pairs
   over the same nine modules: `cli.py` gets 19 importers and
   `gates.py` gets 2. Leaving the set unchanged would mean copying B's
   rule, hand-writing the guarded read, a subprocess over a synthetic
   event, or moving a repo-only adapter into mirrored `gates.py`. Each
   of those is worse than one recorded edge, and ADR-0106 gives the
   reasons. `tests/test_dual_membership.py` sees function-level imports
   too, so the lazy import does not hide either edge. Updating that pin
   (two pairs, and its comment's count) is Implement's work on the Hook
   core item. The ADR is written here.

3. **The identity test is replaced; the lazy import of `gates` stays.**
   The cost line imports `gates` only after the pre-filter matches, so
   `pr_body_preflight` has no module attribute `pr_body_problems` for
   the structural test to compare with `is`. Importing at the top
   instead would put about 60 ms on every Bash call. The replacement
   proves the same thing, that the hook judges through B's one owner
   and not through a copy:
   - with `gates.pr_body_problems` patched to return a sentinel list
     for a body that would pass, `preflight` exits 2 and its stderr
     carries that sentinel;
   - the existing patched-to-raise case gives exit 0 and a note.

   `python3 one_owner.py` stays the review pre-pass.

**Other pinned root-module rules checked, none tripped by this design:**

- `tests/test_gates.py`'s ready-label walk: the hook names no
  `wo:ready-for-agent` literal.
- `gates.label_declarers` (detector J): the hook assigns no
  module-level `LABELS`.
- `tests/test_fake_gh.py`: it walks `tests/`. The hook's tests need no
  gh fake, so they must not define a function taking only `args` that
  answers a gh command.
- `tests/test_shadowed_definitions.py`: no name defined twice at one
  scope.
- `tests/test_factory_init.py`: MIRRORS↔payload pins, and gates' lazy
  imports must ship. The hook is not mirrored, and `gates` gains no
  `import_module`.
- `tests/test_run_tests.py` and `tests/timings.json`: a module missing
  from the timings file is scheduled at 0 s. `--record` is optional.
- `kb_drift`: it reads `.claude/settings.json` only for
  `enabledPlugins`, so a `hooks` key is ignored, and its directory
  surfaces do not include the repo root.
- `one_owner.py`: B's strings and regexes stay in `gates` and
  `knowledge_plane` only, as already designed.
- `factory.py`'s count-claim pin: the docstring is unchanged.

## ADRs

None — no decision met the ADR bar. Every decision above is cheap to
reverse: deleting one settings entry and one script removes the hook,
and the extracted function is a move.

Amended 2026-10-16: ADR-0106 (provisional), "pr_body_preflight joins
the root-only importers of gates.py and cli.py". It does not pass the
protocol's three-leg test either; it exists because
`tests/test_dual_membership.py` makes any change to ADR-0091's pinned
set an ADR by rule, and ADR-0097 is the precedent for one new edge.

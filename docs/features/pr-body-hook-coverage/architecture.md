---
stage: architect
run: feature:pr-body-hook-coverage
date: 2026-11-09
ux: skipped — CLI hook only (a PreToolUse hook on Bash); no screens or flows.
assumptions:
  - "No live interview: the trade-offs below were settled from prd.md, idea.md, the hook's code and tests, and one read-only probe of the Owner's session transcripts, taking the recommended option each time. The three decisions that could have gone another way are named in the hand-off message for the Owner to overrule."
  - "The probe (not the Verify measurement) re-extracted every unique Bash command containing `gh pr create` from ~/.claude/projects, main and subagent transcripts: 1817 commands, of which the unchanged hook judges 158, the same count as #1633. A rough regex over the same-call shape found 497 `cat > F <<D` writers read back by `--body-file F`, and 222 of those (45%) name F through a shell variable (`cat > \"$S/body.md\"` after `S=<dir>` earlier in the command). #1633's 681 is a wider count than the probe's regex; the probe is used for shape, never for a headline number."
  - "Recommended default taken: the binding judges the heredoc text with no filesystem read, so it needs no cwd and works for a relative path with no cwd in the payload."
  - "Recommended default taken: the binding applies to `--body-file`/`-F` only, as the PRD words it. `--body \"$(cat F)\"` after a same-call heredoc keeps today's note."
  - "Open question 3 (the corpus snapshot) is a Verify decision; this document records a recommendation and hands it off. Nothing here fixes it."
---

# Architecture: Judge the same-call heredoc body

## Approach

Inside the one parse the hook already does, record each statement-level heredoc's text instead of discarding it, keep each simple command's redirections and the operator that joined it, and, when a `gh pr create --body-file F` is not the compound's first command, look F up in a **ledger of heredoc-written files** built by one forward walk over the earlier simple commands. A file is *bound* to its heredoc text when exactly `cat > F <<D` wrote it, unconditionally, and nothing in between may have changed what F names or holds. A bound F is judged through `gates.pr_body_problems` exactly as a body file read from disk is today; every other outcome raises `_Unreadable` with a reason, which is the hook's existing "not checked" note and exit 0. The binding reads no file, so it is pure and adds no I/O, timeout or side effect to the hook.

The second shape considered was to actually run the heredoc part of the command in a sandbox at hook time and read back the file a real shell wrote. It would be exactly the oracle the PRD uses at Verify, but a hook that executes shell text has side effects and a start-up cost on every `gh pr create`, and it makes the hook's own safety depend on the sandbox. It stays a Verify-time oracle only. The third shape was a standalone `heredoc_binding.py` module; see Decisions.

## Components

### Heredoc capture (`_Unrun`, extended)

- Responsibility: today it cuts every heredoc body and comment so neither is tokenized as a command, and throws the bodies away. It now also returns, per statement-level heredoc in operator order, `(text, literal, terminated)`: the file text a shell would write (each body line plus a newline; leading tabs stripped for `<<-`), whether the body is literal, and whether its delimiter line was found. `literal` is true when any part of the delimiter word was quoted or backslashed, or when the body holds no `$`, backtick or backslash (the rule `_heredoc_at` already applies to the `$(cat <<D` form).
- Collaborators: `_tokens`, the binding. It does not touch the `$(cat <<'D' … )` masking, which keeps its own placeholder path.

### Command splitter (`_simple_commands`, extended)

- Responsibility: today it returns word lists and drops each redirection with its target. It now returns, per simple command, `words`, `redirects` (an ordered list of `(operator, target)`, where a heredoc redirection carries its operator-order ordinal) and `joiner` (the control operator that precedes it). `_working_directory`, `_gh_repo` and `_create_args` read `words` and are otherwise unchanged.
- Collaborators: `_verdicts`, the binding.

### Heredoc binding (`_bound_body`, new, in `pr_body_preflight.py`)

- Responsibility: the one owner of "which heredoc wrote the file this `gh pr create` will read, and is that still true". It owns the writer shape, the spelling rule for F, the unconditional-chain rule and the table of what may sit between writer and reader. Nothing else in the hook knows those rules.
- Collaborators: the splitter's records, the capture's heredoc list, and `_body`, its only caller. Source dependencies point toward policy: the binding imports nothing; `gates.pr_body_problems` still sees only a string.

### Body source (`_body` / `_read_body_file`, changed)

- Responsibility: unchanged in kind: pick the one body source of a `gh pr create` and return its text or raise `_Unreadable`. For a `file` source that is not the compound's first command it now asks the binding first. If the binding finds no writer for that spelling, the old reason (`a body file is read only from the first command`) is raised unchanged, so every note that is pinned today stays word for word.
- Collaborators: the binding, `cli.read_file` (disk reads for a first-command file, unchanged).

### `gates.pr_body_problems` (policy, unchanged)

- Responsibility: B's one statement of the body rule. This run adds no caller-side copy of any pattern, so `TestOneOwner` and `one_owner.py` still pass without edit.

### Fixture tests and the Verify replay

- Responsibility: `tests/test_pr_body_preflight.py` gains a `TestSameCallHeredoc` class of full-payload fixtures, in the style of `TestHeredoc` and `TestBodyFile`. The replay and the false-block oracle are Verify's, run against a frozen snapshot (see Interfaces and Decisions).
- Collaborators: `preflight()` only; the fixtures go through the same pure seam as every existing test.

### `docs/kb/pr-body-contract.md` and the module docstring

- Responsibility: say what is now read. The kb page's one-paragraph description of the hook gains the same-call heredoc as a readable shape; the page's `verified:` is refreshed by the author of the change and `kb.py drift` stays clean. No new page.
- Collaborators: `kb.py`, `lint.py`.

## Data model

There is no storage; no run of the hook leaves state behind. The records live for one `preflight()` call.

- `Heredoc`: `text: str` (the bytes a shell writes), `literal: bool`, `terminated: bool`, indexed by operator order.
- `Simple`: `words: list[str]`, `redirects: list[(op, target-or-heredoc-ordinal)]`, `joiner: str` (`""` for the first, else one of `;` `&&` `||` `|` `&`, newline, or a parenthesis).
- `Ledger`: a mapping from F's *spelling* (the exact token) to `Live(text, writer_index)` or `Dead(reason)`, built by walking `Simple` records in order up to the reader and consulted once.

Access patterns, from the PRD: (1) at one `gh pr create`, "what text does this spelling stand for here?" (one lookup); (2) for each earlier simple command, "may this change what the spelling names or holds?" (one pass, linear in the compound). Consistency: none beyond a single process; the walk is a pure function of the command string, with no clock, disk or environment.

**The writer shape.** A simple command is a writer of F when its words are exactly `cat`, it has exactly one `>` redirection (the target F) and exactly one heredoc redirection, in either order: `cat > F <<D` or `cat <<D > F`. `>>`, `>|`, `&>`, a file-descriptor prefix, `tee`, `cp`, any other verb and any second redirection are not writers. A later writer of the same spelling replaces an earlier one.

**The spelling rule.** F is a spelling the hook can compare when it holds no backtick, no `$(`, no glob character (`*?[]`), no brace, no leading `~`, and no `$` other than `$NAME` or `${NAME}`. Two words bind when their spelling is identical, and the variables they name are not reassigned between. The hook never resolves `$NAME` to a value: the same token in the same shell state names the same file whatever its value, including unset. This is what makes the 222 variable-path commands in the probe reachable (see Decisions). A relative spelling also needs no `cd`, `pushd` or `popd` between writer and reader.

**The chain rule.** A writer binds only if its execution is implied by the reader's. Every operator from the compound's start through the reader must be `;`, `&&` or a newline; a `|`, `||`, `&`, a parenthesis, or a leading shell keyword (`if then else elif fi for while until do done case esac {`, `}`, `!`, `function`) in any simple command on the way unbinds. A writer that failed to write (a missing directory, a full disk) is an accepted limit, below.

**What may sit between writer and reader (open question 2).** The binding survives an intervening simple command only if it is on this inert list, and it is dropped by any command not on it. A command that is on it still unbinds F when one of its redirect targets spells F.

| Inert | Notes |
|---|---|
| a standalone `NAME=value` or `export NAME=value` | unbinds F when NAME is a variable F's spelling names |
| `cd`, `pushd`, `popd` | unbinds a relative F only |
| `echo`, `printf`, `true`, `:`, `sleep` | |
| `cat`, `grep`, `egrep`, `fgrep`, `head`, `tail`, `wc`, `ls`, `test`, `[`, `diff`, `cmp`, `stat` | read-only verbs; a redirect to F still unbinds |
| `git` with subcommand `add commit push fetch status diff log show branch rev-parse remote ls-files config symbolic-ref rev-list describe` | the subcommands that leave working-tree files alone; `checkout`, `switch`, `restore`, `reset`, `stash`, `clean`, `rm`, `mv`, `merge`, `pull`, `rebase`, `apply` are off the list |
| `gh` | a gh command writes no local file except `gh run download` and `gh release download`, which are off the list |

`rm`, `mv`, `cp`, `tee`, `sed`, `truncate`, `python3` and every other verb are off the list. The PRD's `>`, `>>`, `rm`, `mv`, `tee` are all covered, and so is every verb nobody thought to name. Commands that follow the reader never matter: a cleanup after `gh pr create` does not unbind.

## Interfaces & contracts

### `preflight(payload_text, environ=None) -> (exit_code, stderr_lines)` (unchanged contract)

- Input: the PreToolUse payload. It reads `tool_input.command` and `cwd`, as today.
- Output: exit 2 with B's strings from `gates.pr_body_problems(text)` then the pointer line, when the hook read a body and B fails it; exit 0, silent, when it read a body B accepts; exit 0 with one `pr-body-preflight: not checked — <reason>` line per unreadable `gh pr create`.
- Failure modes: unchanged. Every exception after the payload parses is caught and becomes exit 0 with a note, so no exception escapes. Exit 2 comes only from a body the hook read exactly and B judged failing. Retry is safe: the hook has no side effects and the binding reads no file. Cost is one forward walk over the compound's simple commands, linear, with no new I/O or import.

### `_bound_body(commands, heredocs, position, spelling) -> str`

- Input: the splitter's `Simple` records for the whole compound, the capture's heredoc list, the index of the `gh pr create` and the exact `--body-file` / `-F` value.
- Output: the file text a real shell leaves at that spelling when the compound runs up to `position`: the writer's heredoc text.
- Failure modes: raises `_Unreadable(reason)`. This is the open-question-1 answer: a binding the hook cannot establish is reported through the channel the hook already has, as a note, never as exit 2, and the caller needs no new case. The reasons are:

| Situation | Reason in the note |
|---|---|
| no writer of that spelling anywhere earlier (a different file, a file from an earlier call) | `a body file is read only from the first command` (today's text) |
| writer found, heredoc body holds `$`, a backtick or a backslash under an unquoted delimiter | `an unquoted heredoc body holds $, a backtick or a backslash` (today's text) |
| writer found, delimiter line never closes | `the heredoc that writes <F> has no closing delimiter` |
| writer found, not on an unconditional chain | `the heredoc that writes <F> is not certain to run before gh pr create` |
| F spells an expansion the hook cannot compare | `<F> names a file through an expansion the hook cannot compare` |
| a command between them is off the inert list, redirects to F, or reassigns a variable F names | `<F> may be rewritten or removed by <verb> between the heredoc and gh pr create` |
| a relative F and a directory change between them | `a cd between the heredoc and gh pr create may change what <F> names` |

The first row is why "a `--body-file` that names a different file" needs no row of its own: a reader whose spelling no writer wrote is indistinguishable from today's not-first case and keeps today's note.

### The Verify replay and the false-block oracle (hand-off, with a recommendation)

- Input: one frozen file of unique `gh pr create` command strings; the pre-change hook (the merge-base commit's `pr_body_preflight.py`) and the changed hook.
- Output: for each hook, the count of commands exiting 2 or exiting 0 silently on a body it read, over the snapshot size; and for each command judged through the binding, a verdict from `gates.pr_body_problems` on the file a sandboxed `bash` leaves when only the heredoc part runs, with the two compared.
- Failure modes: a refusal B would not give fails the run (PRD criterion 4). To keep the sandbox from running `git push`: run the text up to and including the last heredoc delimiter line in a temporary directory with a `PATH` whose `git` and `gh` are shims that exit 0, never the whole command. A command the sandbox cannot run to that point is reported, not counted as agreement.

## Stack & dependencies

- Python 3 standard library only, unchanged (`stdlib-only`): the binding uses `re` and nothing else. No new import edge, so ADR-0106's dual-membership pin and `tests/test_dual_membership.py` are untouched.
- The hook stays root-only and in one file; it still imports `gates` lazily, after the pre-filter.

## Requirement trace

| PRD item | Where |
|---|---|
| Demo payload exits 2 with B's two strings then the pointer | binding returns the heredoc text; `_body` hands it to `gates.pr_body_problems` |
| Same payload with a passing body exits 0 and prints nothing | the same path; a body B accepts yields no lines |
| Judged share ≥ 40% on one frozen snapshot, ceiling re-derived | spelling-identity rule (so `$S/x` paths bind); replay and snapshot are Verify's |
| Exit 2 iff B fails the file a real shell writes | writer shape, literal rule and the chain and inert-list rules exist for this; sandbox oracle is Verify's |
| Unestablishable binding passes with a note, no exception escapes | `_Unreadable` reasons table above; `preflight()`'s catch-all, unchanged |
| Fixtures: each shape plus quoted, unquoted, `<<-`, leading `cd` | `TestSameCallHeredoc` |
| One owner of B's patterns | the binding holds no B regex; `TestOneOwner` and `one_owner.py` still pass |
| `run_tests.py`, `lint.py`, `gates.py`, `gates.py --selftest` | no gate, mirror or manifest file changes; the kb page's `verified:` is refreshed |
| User stories 1 to 3 (refuse early; same for routines; no false block) | the refusal path; the same hook runs for unattended runs; the sound inert list and chain rule |
| User story 4 (frozen corpus before and after) | the replay hand-off |

## Test strategy

Fixtures are full payloads through `preflight()`, in `TestSameCallHeredoc`. Each pairs a refused body (exit 2, lines equal to `gates.pr_body_problems(body) + [POINTER]`) with a passing body (exit 0, `[]`). Cases: the demo payload; quoted delimiter; unquoted delimiter without expansion; unquoted with `$` (note); `<<-` with tab-indented lines; a leading `cd` to the repository; the redirect before and after the heredoc (`cat <<D > F`); a `$S/b.md` path after `S=<dir>`; a `${S}` spelling; a different file; `>>` (note); a rewrite by `sed -i`, `mv`, `rm`, `tee`, `echo >` and `cp` between (each a note); a read-only `grep F` between (still judged); a cleanup `rm F` after `gh pr create` (still judged); a `||`, a pipeline and an `if` in front of the writer (note); a relative F with a `cd` between (note); a missing closing delimiter (note); two `gh pr create` in one command, each bound to its own writer. Every test that passes today is unchanged and still passes, including `test_a_body_file_after_another_command_fails_open`, because a reader with no writer keeps today's note.

## Accepted behaviour changes

Comparing the old rule (a body file is read only from the compound's first simple command) with the new one over the inputs where they differ: they differ only where the `gh pr create` is not the first simple command and `--body-file F` is bound by a `cat > F <<D` earlier in the same command.

- Old: note, exit 0, the body unjudged. New: judged; exit 2 if B fails the heredoc text, exit 0 silent if B accepts it.
- No other input changes. A first-command body file, an inline `--body`, a `$(cat F)` value and every shape that fails open today give the same output, since the binding runs only on the not-first path and falls back to today's reason when it finds no writer.
- Accepted limit: if the writer itself fails (an unwritable directory, a full disk), gh reads whatever the file held, not the heredoc. The hook still judges the heredoc text. A body B would accept on disk could be refused only if the writer failed and a stale passing file was there; that needs two coincidences and leaves a recoverable refusal, since fixing the body is what the refusal asks.
- Accepted limit: `'$S/x'` (single-quoted, a file literally named `$S/x`) and `"$S/x"` tokenize alike. Both ends would have to be spelled differently for this to bind wrongly, and the Verify oracle compares against the real file.
- Accepted limit: a command on the inert list is trusted to leave F alone unless it redirects to F. The list is chosen so that none of its verbs writes a file it is not told to write.

## Decisions & alternatives

- **The binding lives inside `pr_body_preflight.py`, as one new function fed by two extended records** over a new module (`heredoc_binding.py`): the rules need `_Unrun`'s heredoc bodies and the splitter's redirections, so a separate module would have to import both or be handed them, and exposes the parser's internals for one caller. Deleting it would not remove complexity from the hook, only move it. Answers open question 1. Standards: `stdlib-only`.
- **A binding it cannot establish is an `_Unreadable` note** over a new return type (`Bound | Unbound(reason)`): the hook already routes every unreadable body this way, and a second channel would be a second case in `_verdicts` for no new fact.
- **F is matched by spelling identity, never resolved to a value** over a variable table (`S=<dir>` then `$S/b.md` expanded) and over binding literal paths only. The probe found 222 of 497 same-call writers in variable paths, so a literal-only rule reaches roughly 29% (scaling #1633's 681 by the probe's 275-of-497 literal share gives about 375, plus 158 judged now, of 1817; an inference from a rough probe) against a 40% target and a ceiling near 46%. A table resolves values the hook cannot know (`$TMPDIR`, a value with `$(mktemp)`), and identical spelling in unchanged state names the same file without knowing them.
- **What may sit between writer and reader is an inert allowlist** over a deny-list of `>`, `>>`, `rm`, `mv`, `tee`. A deny-list passes every verb nobody listed (`sed -i`, `cp`, `python3`), and each of those is a refusal B would not give. The allowlist costs coverage where an intervening command is outside it, which Verify measures against the 40% target; the probe's intervening commands were mostly `cd`, `git`, `grep`, `echo`. Answers open question 2.
- **The chain from the compound's start to the reader must be `;`, `&&` or newline** over accepting `||`, `|`, `&` or a conditional body: a writer that may not have run leaves a stale file, which is the exact false-block mode the Owner named.
- **The path is judged with no disk read and no cwd** over reading the file the heredoc just wrote: the file does not exist yet at hook time, which is the whole problem.
- **The replay snapshot is a local, uncommitted file and only its SHA-256 and count are recorded in `verification.md`** over committing the corpus: the commands carry PR bodies from the Owner's private repositories. Frozen means one sorted, de-duplicated JSONL file written once, at the start of Verify, outside the repository (the Owner picks the path); both the baseline and the changed hook run over it, and `verification.md` records the extraction command, the count, the SHA-256 and each measured number so a rerun on the same file reproduces them. The replay harness is a throwaway script, not a repository tool. Answers open question 3 as a recommendation; the Owner confirms at Verify.
- **`--body "$(cat F)"` after a same-call writer keeps today's note** over binding it too: the PRD names `--body-file`, and it is a separate spelling that the replay did not count.

## ADRs

none — no decision met the ADR bar. The closest, spelling identity with an inert allowlist (the false-block policy), fails the first leg: it is private to one hook function with no stored data and no public interface, so reversing it is a one-function edit, and the Verify replay is built to find out whether it must be reversed. The others (where the binding lives, a note over a new return type, snapshot storage) are reversible by the same edit and obvious on a first read of the code. ADR-0106's pin does not move: the run adds no import edge.

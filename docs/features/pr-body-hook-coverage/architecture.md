---
stage: architect
run: feature:pr-body-hook-coverage
date: 2026-11-09
ux: skipped — CLI hook only (a PreToolUse hook on Bash); no screens or flows.
assumptions:
  - "No live interview: the trade-offs below were settled from prd.md, idea.md, the hook's code and tests, and one read-only probe of the Owner's session transcripts, taking the recommended option each time. The three decisions that could have gone another way are named in the hand-off message for the Owner to overrule."
  - "The probe (not the Verify measurement) re-extracted every unique Bash command containing `gh pr create` from ~/.claude/projects, main and subagent transcripts: 1817 commands, of which the unchanged hook judges 158, the same count as #1633. It then applied the rules below through the real tokenizer (`_mask_heredocs`, `_Unrun`, `_tokens`); its survival funnel is in Decisions. It found 548 not-first readers whose file a `cat > F <<D` earlier in the command wrote, against #1633's 681 for the wider shape; that gap is not explained here, and the PRD's rule that Verify re-derives the ceiling on its own snapshot stands."
  - "Revised 2026-11-09 after review of f64e89d (12 findings, mostly false-block safety). The Owner confirmed the three trade-offs as drafted (identical spelling, inert allowlist, binding inside pr_body_preflight.py). The rules were tightened to fail closed on invalidation; the cost is recorded, not hidden."
  - "Recommended default taken: the binding judges the heredoc text with no filesystem read, so it needs no cwd and works for a relative path with no cwd in the payload."
  - "Recommended default taken: the binding applies to `--body-file`/`-F` only, as the PRD words it. `--body \"$(cat F)\"` after a same-call heredoc keeps today's note."
  - "Open question 3 (the corpus snapshot) is a Verify decision; this document records a recommendation and hands it off. Nothing here fixes it."
---

# Architecture: Judge the same-call heredoc body

## Approach

Inside the one parse the hook already does, record each statement-level heredoc's text instead of discarding it, keep each simple command's redirections and the operator that joined it, and, when a `gh pr create --body-file F` is not the compound's first command, look F up in a **ledger of heredoc-written files** built by one forward walk over the earlier simple commands. A file is *bound* to its heredoc text when exactly `cat > F <<D` wrote it, unconditionally, and nothing in between may have changed what F names or holds. A bound F is judged through `gates.pr_body_problems` exactly as a body file read from disk is today; every other outcome raises `_Unreadable` with a reason, which is the hook's existing "not checked" note and exit 0. The binding reads no file, so it is pure and adds no I/O, timeout or side effect of its own.

The second shape considered was to actually run the heredoc part of the command in a sandbox at hook time and read back the file a real shell wrote. It would be exactly the oracle the PRD uses at Verify, but a hook that executes shell text has side effects and a start-up cost on every `gh pr create`, and it makes the hook's own safety depend on the sandbox. It stays a Verify-time oracle only. The third shape was a standalone `heredoc_binding.py` module; see Decisions.

## Components

### Heredoc capture (`_Unrun`, extended)

- Responsibility: today it cuts every heredoc body and comment so neither is tokenized as a command, and throws the bodies away. It now also records, per statement-level heredoc, `(text, literal, terminated)` and rewrites that heredoc's operator-plus-delimiter into `<<` followed by an indexed placeholder word (the existing `PLACEHOLDER` convention: `__pr_body_preflight_heredoc_<N>__`, `N` counting heredocs `_Unrun` queues, in queue order). `text` is the bytes a shell writes (each body line plus a newline; leading tabs stripped for `<<-`). `literal` is true when any part of the delimiter word was quoted or backslashed, or when the body holds no `$`, backtick or backslash (the rule `_heredoc_at` applies to `$(cat <<D`). `<<<` is a here-string, not a heredoc: it queues nothing and gets no index.
- Unmasking: `_mask_heredocs` runs first on the raw string and rewrites any `$(cat <<'B' … B)` it finds, including one that sits inside a statement-level heredoc body (a PR body that documents this very hook). The capture therefore restores each placeholder it finds in a captured body to the original span, which `_mask_heredocs` now returns as `(placeholder, original)` pairs. The file text is then the text the shell would write. This settles review finding 8 without changing what the tokenizer sees.
- Collaborators: `_tokens`, `_mask_heredocs`, the binding. The `$(cat <<'D' … )` path keeps its own placeholders and is unchanged.

### Command splitter (`_simple_commands`, extended)

- Responsibility: today it returns word lists and drops each redirection with its target, and drops a command with no words. It now returns one `Simple` per command, including a redirect-only command such as `> /tmp/b.md`: `words`, `redirects` (an ordered list of `(operator, target)`, where a heredoc redirection's target is the placeholder word, from which the index is read, never counted) and `joiner` (the whole shlex punctuation run that precedes it, e.g. `&&`, `&&\n`, `;\n`, `&\n`, `\n`; see Data model). `&>` and `&>>` are redirections. A `<(` or `>(` run anywhere is recorded as a redirection of kind `procsub`.
- `first` and `position` are computed over the `Simple` records that have words, so a leading `> log` does not make a first-command body file "not first" (review finding 10): today's behaviour is preserved, and the word-less record exists only for the binding walk, where a truncation of F is a redirect to a file.
- Collaborators: `_verdicts`, the binding. `_working_directory`, `_gh_repo` and `_create_args` read `words` of records with words and are otherwise unchanged.

### Heredoc binding (`_bound_body`, new, in `pr_body_preflight.py`)

- Responsibility: the one owner of "which heredoc wrote the file this `gh pr create` will read, and is that still true". It owns the writer shape, the spelling rule for F, the chain rule, the invalidation rule and the inert list. Nothing else in the hook knows those rules. It binds on identical spelling and invalidates on anything that might touch a file, which is the fail-closed direction in both halves.
- Collaborators: the splitter's records, the capture's heredoc list, and `_body`, its only caller. Source dependencies point toward policy: the binding imports nothing; `gates.pr_body_problems` still sees only a string.

### Body source (`_body` / `_read_body_file`, changed)

- Responsibility: unchanged in kind: pick the one body source of a `gh pr create` and return its text or raise `_Unreadable`. For a `file` source that is not the compound's first command it now asks the binding first. If the binding finds no writer for that spelling, the old reason (`a body file is read only from the first command`) is raised unchanged. A `<(` or `>(` anywhere in the reader's own command raises `_Unreadable` before the binding is consulted (review finding 2: the splitter reads `-F <(cat a c)` as the file `a`).
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

- `Heredoc`: `text: str` (the bytes a shell writes, unmasked), `literal: bool`, `terminated: bool`, indexed by the placeholder number `_Unrun` assigned.
- `Simple`: `words: list[str]`, `redirects: list[(op, target)]`, `joiner: str`.
- `Ledger`: a mapping from F's *spelling* (the exact token) to `Live(text, writer_index)` or `Dead(reason)`, built by one forward walk over the `Simple` records up to the reader and consulted once.

Access patterns, from the PRD: (1) at one `gh pr create`, "what text does this spelling stand for here?" (one lookup); (2) for each earlier simple command, "may this change what the spelling names or holds?" (one pass, linear in the compound). Consistency: none beyond a single process; the walk is a pure function of the command string, with no clock, disk or environment.

**The joiner.** shlex with `punctuation_chars` returns a run of punctuation characters as one token (`&&`, `&&\n`, `;\n`, `&\n`, `\n)\n`, `&>`). The joiner is that whole token. A joiner *separates* (and is not a redirection) unless it starts a redirection: `<`, `>`, `&>`, `&>>` and their targets are redirects. Over the run: `|` (so `||` too), `(`, `)`, or an `&` that is not part of an `&&` pair makes the run **hostile**; the rest (`;`, `&&`, newline, in any combination such as `;\n` or `&&\n`) is **sequential**. A `&&` pair is the sequential-and kind; anything else containing `&` (`&`, `&\n`) is hostile, so a background writer never binds. This is defined over the real runs, not over a membership list.

**The writer shape.** A simple command is a writer of F when its words are exactly `cat`, and its redirects are exactly one `>` (target F) and one heredoc (placeholder index), in either order: `cat > F <<D` or `cat <<D > F`. `>>`, `>|`, `&>`, a file-descriptor prefix, `tee`, `cp`, any other verb, a second redirection of any kind and a heredoc with `terminated` false are not writers. A later writer of the same spelling replaces an earlier one. The writer's own record decides the pairing: its heredoc is the index in its own redirect target, so a `<<` that sits in a `"$( … )"` word (which `_Unrun` queues but shlex keeps inside one word) or in `X=$(sed q <<A …)` (a command whose words are not `cat`) never pairs with a reader.

**The spelling rule.** F is a spelling the hook can compare when:

- it holds no backtick, no `$(`, no glob character (`*?[]`), no brace and no leading `~`;
- every `$` in it begins `$NAME` or `${NAME}`, with `NAME` of the form `[A-Za-z_][A-Za-z0-9_]*` and not one of the names a shell changes without an assignment: `RANDOM`, `SRANDOM`, `SECONDS`, `EPOCHSECONDS`, `EPOCHREALTIME`, `LINENO`, `BASHPID`, `PWD`, `OLDPWD`, `_`, or any name beginning `BASH`. `$$`, `$!`, `$?`, `$-` and positional parameters are not `NAME` forms and so are rejected.

F is **absolute** only when it starts with a literal `/`. Anything else, including `$S/b.md`, `${PWD}/b.md` and `./b.md`, is treated as relative to the working directory: a `cd`, `pushd` or `popd` between writer and reader unbinds it. Two words bind when their spelling is identical. The hook never resolves `$NAME` to a value: the same token in the same shell state names the same file whatever its value, including unset.

**Invalidation is fail-closed and never compares spellings.** Binding may rely on identical spelling because a mismatch there only falls back to a note. Invalidation may not, because a missed second spelling (`./b.md` for `b.md`, a `$BODY` alias, an appended `>> "$BODY"`) keeps a stale binding alive. So the ledger entry for F dies at the first command between the writer (exclusive) and the reader (inclusive of the reader's own redirects) that:

1. carries any redirect whose operator writes (`>`, `>>`, `>|`, `&>`, `&>>`, `<>`) unless the target is `/dev/null`, `/dev/stderr` or a file-descriptor duplication (`>&N`, `2>&1`); this covers a redirect-only truncation and every spelling of F, with no comparison;
2. holds a `<(` or `>(` anywhere (a process substitution can read or write any file);
3. sits behind a hostile joiner (a pipeline, a subshell, a background job, `||`), or is itself a shell keyword (`if then else elif fi for while until do done case esac function`, `{`, `}`, `!`) or an assignment, `export` or `unset` of a variable F's spelling names;
4. is off the inert list below, or is on it with an argument that writes: an argument that is `-v` for `printf`, or holds `${…=`, `${…:=` or `$((…=`, which assign.

**The chain rule.** A writer binds only if its execution is implied by the reader's. The writer's own joiner must be the start, `;` or a newline (a sequential run with no `&&`), or every joiner from the writer to the reader must be a sequential run made of `&&` pairs. In both cases no joiner from the writer through the reader is hostile. A writer after `test -d /x && cat > F <<D … D` and then a newline before the reader does not bind: if the test fails the writer is skipped while gh still runs. Joiners *before* the writer's own do not matter when the writer's own joiner is the start, `;` or a newline, because that command runs whatever the earlier ones did. A hostile run strictly before the writer, with a `;` or newline joiner for the writer, is therefore harmless.

**What may sit between writer and reader (open question 2).** The binding survives an intervening simple command only if it is on this inert list, and it dies to any command not on it.

| Inert | Notes |
|---|---|
| a standalone `NAME=value` or `export NAME=value` | dies when NAME is a variable F's spelling names, or the value holds `$(` or a backtick |
| `cd`, `pushd`, `popd` | dies for a relative F |
| `echo`, `printf` (without `-v`), `true`, `:`, `sleep` | |
| `cat`, `grep`, `egrep`, `fgrep`, `head`, `tail`, `wc`, `ls`, `test`, `[`, `diff`, `cmp`, `stat` | read-only verbs |
| `git status`, `git diff`, `git log`, `git rev-parse`, `git branch --show-current`, `git config --get` | none with `--output…`, `-f`, `--file` or any argument that spells F; `git add`, `commit`, `push`, `fetch` and every other subcommand are off the list: a commit runs hooks, which are arbitrary code, and `fetch` and `push` run them too |
| `gh pr view`, `pr list`, `pr status`, `pr checks`, `pr diff`, `issue view`, `issue list` | and `gh api` with no `--output`, `-X`, `--method`, `-f`, `-F`, `--field`, `--raw-field` or `--input`; every other `gh` verb is off the list (extensions and `--shell` aliases run any program; `pr checkout`, `repo sync`, `repo clone`, `gist clone`, `pr merge --delete-branch` write working-tree files) |

`rm`, `mv`, `cp`, `tee`, `sed`, `truncate`, `python3`, `git commit` and every other verb are off the list. The PRD's `>`, `>>`, `rm`, `mv`, `tee` are all covered, and so is every verb nobody thought to name. Commands that follow the reader never matter: a cleanup after `gh pr create` does not unbind.

## Interfaces & contracts

### `preflight(payload_text, environ=None) -> (exit_code, stderr_lines)` (unchanged contract)

- Input: the PreToolUse payload. It reads `tool_input.command` and `cwd`, as today.
- Output: exit 2 with B's strings from `gates.pr_body_problems(text)` then the pointer line, when the hook read a body and B fails it; exit 0, silent, when it read a body B accepts; exit 0 with one `pr-body-preflight: not checked — <reason>` line per unreadable `gh pr create`.
- Failure modes: unchanged. Every exception after the payload parses is caught and becomes exit 0 with a note, so no exception escapes. Exit 2 comes only from a body the hook read exactly and B judged failing. Retry is safe: the hook has no side effects and the binding reads no file. Cost is one forward walk over the compound's simple commands, linear. The binding itself does no I/O and imports nothing; a newly bound body does reach `_check_target`, which reads the cwd checkout's git config and calls `is_dir()` after a `cd` (see Accepted behaviour changes).

### `_bound_body(commands, heredocs, position, spelling) -> str`

- Input: the splitter's `Simple` records for the whole compound, the capture's heredoc list, the index of the `gh pr create` among records and the exact `--body-file` / `-F` value.
- Output: the file text a real shell leaves at that spelling when the compound runs up to `position`: the writer's heredoc text.
- Failure modes: raises `_Unreadable(reason)`. This is the open-question-1 answer: a binding the hook cannot establish is reported through the channel the hook already has, as a note, never as exit 2, and the caller needs no new case. The reasons are:

| Situation | Reason in the note |
|---|---|
| no writer of that spelling anywhere earlier (a different file, a file from an earlier call) | `a body file is read only from the first command` (today's text) |
| writer found, heredoc body holds `$`, a backtick or a backslash under an unquoted delimiter | `an unquoted heredoc body holds $, a backtick or a backslash` (today's text) |
| writer found, delimiter line never closes | `the heredoc that writes <F> has no closing delimiter` |
| writer found, chain rule fails | `the heredoc that writes <F> is not certain to run before gh pr create` |
| F spells an expansion the hook cannot compare | `<F> names a file through an expansion the hook cannot compare` |
| an invalidating command between them (rule 1 to 4) | `<F> may be rewritten or removed by <verb or redirect> between the heredoc and gh pr create` |
| a relative F and a directory change between them | `a cd between the heredoc and gh pr create may change what <F> names` |
| `<(` or `>(` in the reader | `a process substitution in gh pr create hides the body file` |

The first row is why "a `--body-file` that names a different file" needs no row of its own: a reader whose spelling no writer wrote is indistinguishable from today's not-first case and keeps today's note.

### The Verify replay and the false-block oracle (hand-off, with a recommendation)

- Input: one frozen file of unique `gh pr create` command strings; the pre-change hook (the merge-base commit's `pr_body_preflight.py`) and the changed hook.
- Output: for each hook, the count of commands exiting 2 or exiting 0 silently on a body it read, over the snapshot size; for each command judged through the binding, a verdict from `gates.pr_body_problems` on a reference body; and the survival funnel (see Decisions) beside the ceiling, so a miss of the 40% target names the rule that cost it.
- The reference body never comes from executing the Owner's command. Historical commands write absolute paths into real checkouts and run `rm`, `cp`, `python3` and `npm`, so running even their prefixes would overwrite real files. Instead the oracle extracts, by regex over the raw command text and independently of the hook's parser, only the writer's source span: the line holding `<<D`, its body and its delimiter line. It rewrites that line's `> F` target to a scratch file and runs that span, alone, under `sandbox-exec` with network denied, writes denied outside the scratch directory, a scratch `HOME` and an empty environment. Variables in the span's body are unset, so an unquoted body with `$` is out of the criterion anyway. The span is paired with the hook's reader by the one heredoc whose redirect the hook reports as F's writer; a command whose text yields more than one candidate span, or none, is reported as *unpaired*, not as agreement.
- Failure modes: a refusal B would not give fails the run (PRD criterion 4). Known blind spot, recorded here and not papered over: this oracle checks the heredoc text, the writer shape and the pairing, not the commands between writer and reader, because it never runs them. A false block caused by the between-commands rule cannot show at Verify. The compensation is that Verify lists every bound command with at least one command between writer and reader and the Owner reads a sample by hand, and the inert list is the only thing the rule trusts.

## Stack & dependencies

- Python 3 standard library only, unchanged (`stdlib-only`): the binding uses `re` and nothing else. No new import edge, so ADR-0106's dual-membership pin and `tests/test_dual_membership.py` are untouched.
- The hook stays root-only and in one file; it still imports `gates` lazily, after the pre-filter.

## Requirement trace

| PRD item | Where |
|---|---|
| Demo payload exits 2 with B's two strings then the pointer | binding returns the heredoc text; `_body` hands it to `gates.pr_body_problems` |
| Same payload with a passing body exits 0 and prints nothing | the same path; a body B accepts yields no lines |
| Judged share ≥ 25% on one frozen snapshot, ceiling re-derived | spelling-identity rule (so `$S/x` paths bind); replay, snapshot and the survival funnel are Verify's; the probe's risk to this criterion is stated under Decisions |
| Exit 2 iff B fails the file a real shell writes | writer shape, literal rule and the chain and inert-list rules exist for this; sandbox oracle is Verify's |
| Unestablishable binding passes with a note, no exception escapes | `_Unreadable` reasons table above; `preflight()`'s catch-all, unchanged |
| Fixtures: each shape plus quoted, unquoted, `<<-`, leading `cd` | `TestSameCallHeredoc` |
| One owner of B's patterns | the binding holds no B regex; `TestOneOwner` and `one_owner.py` still pass |
| `run_tests.py`, `lint.py`, `gates.py`, `gates.py --selftest` | no gate, mirror or manifest file changes; the kb page's `verified:` is refreshed |
| User stories 1 to 3 (refuse early; same for routines; no false block) | the refusal path; the same hook runs for unattended runs; the fail-closed invalidation, chain rule and inert list |
| User story 4 (frozen corpus before and after) | the replay hand-off |

## Test strategy

Fixtures are full payloads through `preflight()`, in `TestSameCallHeredoc`. Each pairs a refused body (exit 2, lines equal to `gates.pr_body_problems(body) + [POINTER]`) with a passing body (exit 0, `[]`), unless it is a note case (exit 0, one `not checked` line). Cases:

- the shapes the PRD names: the demo payload; quoted delimiter; unquoted delimiter without expansion; unquoted with `$` (note); `<<-` with tab-indented lines; a leading `cd` to the repository; the redirect before and after the heredoc (`cat <<D > F`); a `$S/b.md` path after `S=<dir>`; a `${S}` spelling; a different file (today's note); `>>` (note); a cleanup `rm F` after `gh pr create` (still judged); a missing closing delimiter (note); two `gh pr create` in one command, each bound to its own writer;
- chain rule: a writer after `test -d /x &&` with a newline before the reader (note); a writer after `cd D &&` then `&&` to the reader (judged); a background writer `cat > F <<D &` (note); a pipeline, a subshell and an `if` between (note); a hostile run before a `;`-joined writer (judged); `&&\n` and `;\n` joiners (judged as sequential);
- invalidation: each of `sed -i`, `mv`, `rm`, `tee`, `cp`, `python3`, `echo … >> "$BODY"`, `> F` (redirect-only), `./F` for `F`, `>| F` and `&> F` between (each a note); `2>&1`, `> /dev/null` and `>&2` between (still judged); `printf -v S`, `: ${S:=x}` and `$((S=1))` between when F names `$S` (note); `git commit`, `git push`, `gh pr checkout`, `git diff --output=F` between (note); `git status` and `gh pr view` between (judged);
- spelling: an absolute path (judged), `$S/b.md` with a `cd` between (note), `$RANDOM`, `$PWD`, `$(mktemp)`, a glob and `~` (note);
- reader: `-F <(cat a c)` (note, also as the first command), `-F` with a same-spelling reader whose heredoc sits inside `"$( … )"` or `X=$(sed q <<A …)` (note, no pairing), a here-string `<<<` (never a writer);
- masking: a PR body that itself holds a `$(cat <<'B' … B)` snippet, judged on the file text, not the placeholder;
- first-command parity: `> log` then `gh pr create -F x.md` is judged from disk as today.

Every test that passes today is unchanged and still passes, including `test_a_body_file_after_another_command_fails_open`, because a reader with no writer keeps today's note.

## Accepted behaviour changes

Compared by running the old rule (a body file is read only from the compound's first word-bearing simple command; a `<(` is read as a redirection that drops the next word) and the new rule over the inputs where they differ. Exit codes differ only in the first row; the others change stderr.

| Input class | Old | New |
|---|---|---|
| not-first `--body-file F`, bound by a `cat > F <<D` that passes every rule | note, exit 0, unjudged | judged: exit 2 if B fails the heredoc text, exit 0 silent if B accepts it |
| not-first `--body-file F`, a writer exists but a rule fails | `a body file is read only from the first command` | the reason from the table above (stderr changes; exit 0 as before) |
| as the first row, bound, but the compound `cd`s the checkout out of this repository or to a place the hook cannot place | the first-command note | the `_check_target` reason (`a cd before gh pr create leaves this repository` or `… the hook cannot place`); exit 0 as before |
| `-F <(…)` or `-F >(…)`, as the first command or not | first: the first word after `<(` was read from disk as the body and judged, a refusal B might not give; not-first: the first-command note | `a process substitution in gh pr create hides the body file`, exit 0 (a first-command case that was a latent false block is now a note) |
| a leading redirect-only command (`> log`) | not a command; `first` unaffected | a record for the binding walk only; `first` and `position` are computed over records with words, so the result is unchanged |
| no writer of F in the compound; first-command file; inline `--body`; `$(cat F)`; every other fail-open | as today | identical output, since the binding runs only on the not-first path and falls back to today's reason when it finds no writer |

New I/O, stated once: the binding reads no file. A newly bound body is judged only after `_check_target` passes, and `_check_target` reads the cwd checkout's `.git/config` (following a worktree's `gitdir` and `commondir`) and calls `is_dir()` for each `cd` argument. Those reads are the hook's existing ones, reached by more commands, and every failure there is already a note.

- Accepted limit: if the writer itself fails (an unwritable directory, a full disk), gh reads whatever the file held, not the heredoc. The hook still judges the heredoc text. A body B would accept on disk is refused only if the writer failed and a stale passing file was there; that needs two coincidences and the refusal asks only for a body fix.
- Accepted limit: `'$S/x'` (single-quoted, a file literally named `$S/x`) and `"$S/x"` tokenize alike. Both ends would have to be spelled differently for this to bind wrongly.
- Accepted limit: a command on the inert list is trusted to leave F alone unless its arguments or redirects write. The list names only commands whose arguments the rules read.

## Decisions & alternatives

- **The binding lives inside `pr_body_preflight.py`, as one new function fed by two extended records** over a new module (`heredoc_binding.py`): the rules need `_Unrun`'s heredoc bodies and the splitter's redirections, so a separate module would have to import both or be handed them, and exposes the parser's internals for one caller. Deleting it would not remove complexity from the hook, only move it. Answers open question 1. Standards: `stdlib-only`. Confirmed by the Owner.
- **A binding it cannot establish is an `_Unreadable` note** over a new return type (`Bound | Unbound(reason)`): the hook already routes every unreadable body this way, and a second channel would be a second case in `_verdicts` for no new fact.
- **F is matched by spelling identity, never resolved to a value** over a variable table (`S=<dir>` then `$S/b.md` expanded) and over binding literal paths only. The probe's funnel below shows a literal-only rule binds 222 of 1817 (judged share 20.9%) against spelling identity's 323 (26.5%). A table resolves values the hook cannot know (`$TMPDIR`, a value with `$(mktemp)`), and identical spelling in unchanged state names the same file without knowing them. Confirmed by the Owner.
- **Invalidation never compares spellings, and what may sit between writer and reader is an inert allowlist** over a deny-list of `>`, `>>`, `rm`, `mv`, `tee`, and over an invalidation keyed on F's spelling. Binding may rely on identical spelling (a mismatch there only falls back to a note); invalidation may not (a mismatch there keeps a stale binding: `./b.md` for `b.md`, a `$BODY` alias, `>> "$BODY"`). A deny-list passes every verb nobody listed (`sed -i`, `cp`, `python3`), and each is a refusal B would not give. Any file-writing redirect, any `<(`, any hostile joiner and any command off the list unbinds. Answers open question 2. Confirmed by the Owner.
- **The chain rule: the writer's own joiner is the start, `;` or a newline, or every joiner from writer to reader is `&&`; no joiner from writer to reader is hostile** over "every joiner from the compound's start to the reader is sequential". The second is wrong where `test -d /x && cat > F <<D … D` has a newline before the reader: the writer is skipped when the test fails and gh still reads the stale file. A hostile run before a `;`-joined writer is harmless, since that writer runs whatever came before. The cost is in the funnel: 102 writers in the probe sit after a `&&` with a newline before the reader (`cd "$D" && cat > F <<EOF … EOF`, newline, `gh pr create`).
- **The path is judged with no disk read and no cwd** over reading the file the heredoc just wrote: the file does not exist yet at hook time, which is the whole problem.
- **A heredoc's index is carried by a placeholder word in the token stream, and bodies are unmasked on capture** over counting `<<` operators in two places and over skipping masking inside heredoc bodies. Counts diverge on `"$( … <<A )"`, `X=$(… <<A)` and `<<<`; a placeholder in the target position cannot.
- **The replay snapshot is a local, uncommitted file and only its SHA-256 and count are recorded in `verification.md`** over committing the corpus: the commands carry PR bodies from the Owner's private repositories. Frozen means one sorted, de-duplicated JSONL file written once, at the start of Verify, outside the repository (the Owner picks the path); both the baseline and the changed hook run over it, and `verification.md` records the extraction command, the count, the SHA-256 and each measured number so a rerun on the same file reproduces them. The replay harness is a throwaway script, not a repository tool. Answers open question 3 as a recommendation; the Owner confirms at Verify.
- **`--body "$(cat F)"` after a same-call writer keeps today's note** over binding it too: the PRD names `--body-file`, and it is a separate spelling that the replay did not count.

### The 25% criterion and the survival funnel (a rough probe, not the Verify measurement)

The probe ran the tightened rules through the real tokenizer over the 1817 re-extracted commands. Of 1064 not-first body-file readers, 548 name a file that a `cat >`-style writer wrote earlier in the same command. Survival:

| Stage | Lost | Left |
|---|---|---|
| writer names F | | 548 |
| spelling rule | 4 | 544 |
| writer shape (`printf`, `sed`, `{ … } > F` and similar are not heredoc writers) | 58 | 486 |
| unquoted heredoc holding `$`, a backtick or a backslash | 22 | 464 |
| chain rule: a writer behind `&&` with a newline before the reader | 102 | 362 |
| chain rule: a `|`, `(`, `)` or lone `&` between | 26 | 336 |
| between-commands rule (off the inert list: `python3` 11, `gh` 2) | 13 | 323 |

So **323 bind**: a judged share of (158 + 323) / 1817 = 26.5%. Two further figures bound the criterion: binding every writer with no rule at all gives (158 + 548) / 1817 = 38.9%, and the writer-behind-`&&` rule alone costs 102 commands, 5.6 points. A relaxation, not adopted because the Owner asked for the stricter rule, lets a writer behind `&&` bind when everything before it in that `&&` run is `cd`, `pushd`, `export` or a plain assignment: it binds 410 (31.3%). **On this probe no rule set reaches 40%, the target before the Owner's decision**, and the gap to #1633's ceiling (839) is the 681 against 548 difference, which the probe cannot explain. This is not a design failure to hide: the PRD already requires Verify to re-derive the reachable ceiling on its own snapshot and report it beside the 25% result. Recommended Verify report: the funnel above, row by row, on the frozen snapshot, beside the ceiling and the share, so a miss names its cause; if the re-derived share misses 25%, the Owner decides with that table in hand whether to take the relaxation or revisit the target.

**Decision (Owner, 2026-11-09):** the target is lowered from 40% to 25% and every safety rule above is kept. Reason: the safe design's probe share is about 26.5%, and #1633's 681 same-call count was not reproduced (the probe found 548). The PRD's criterion is amended to match. idea.md's 40% ("Success in one sentence") is superseded; idea.md is a historical artifact and is left unedited.

## ADRs

none — no decision met the ADR bar. The closest, spelling identity with fail-closed invalidation and an inert allowlist (the false-block policy), fails the first leg: it is private to one hook function with no stored data and no public interface, so reversing it is a one-function edit, and the Verify replay is built to find out whether it must be reversed. The others (where the binding lives, a note over a new return type, the placeholder index, snapshot storage) are reversible by the same edit and obvious on a first read of the code. ADR-0106's pin does not move: the run adds no import edge.

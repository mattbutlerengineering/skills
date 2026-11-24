# Worker Bash shapes

The one owner of the Bash shapes a worktree-isolated worker may use
(#2319). `implement-queue` (its worker brief and its work-order brief)
and `autorun` copy the block below verbatim into the prompt of every
worker they dispatch with `isolation: "worktree"`, and `conduct` names
its own variant below. Each of them cites this file; none restates the
block.

Why: the harness refuses a worktree-isolated worker's command it cannot
prove stays inside the worktree. A harvest of 505 transcripts over 14
days in one consumer repo counted 169 such refusals: commands too
complex to check (heredocs, compounds), git aimed at a folder or
redirected elsewhere, a string run through a shell, and a change of
directory. Every refusal costs the worker a turn and a retry.

## The block to copy

> **Bash shapes.** This worker runs worktree-isolated, and the harness
> refuses any command it cannot prove stays inside the worktree.
> - One plain command per call: no heredoc, no `&&`, `||`, `;` or `|`
>   compound, no `$(...)` or backticks, no `bash -c` or `eval`.
> - Never `cd`. Name every file by its absolute path.
> - Write file content through the Write or Edit tool, never through
>   the shell (`echo >`, `cat >`, `tee`, `sed -i`).
> - Run git as `git -C <absolute worktree path> <subcommand>`.
> - Run gh with `--repo <owner>/<repo>` on every call.
> - Logic with more than one step goes in a script written to the
>   scratchpad directory and run as one plain command
>   (`python3 <absolute script path>`).
> - A refused command is reshaped to these rules, never retried as it
>   was.

## conduct's variant

`conduct`'s Workers are not dispatched with `isolation: "worktree"`:
each is a headless run whose working directory is its item worktree and
whose Bash is limited by `--allowedTools` patterns such as `git add *`.
Its brief, which `conductor_run.compose_brief` writes, carries a
`## Bash shapes` section with the same one-command, no-`cd`,
Write-or-Edit and script rules, and two differences the allowlist
forces: git runs in its plain allowed form from that working directory,
never `git -C`, which the patterns do not match; and there is no gh
rule, since a Worker never runs gh.

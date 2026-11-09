---
stage: prd
run: feature:pr-body-hook-coverage
date: 2026-11-09
ux: not-applicable
ux-reason: "CLI hook only (a PreToolUse hook on Bash); no screens or flows."
assumptions:
  - "Interview held live with the Owner: the false-block check (fixtures in tests plus the replay at Verify) and the scope exclusions (all five) were the Owner's picks. Actors, user stories and the other success criteria are drafted from idea.md and issue #1633 and were not separately confirmed."
  - "The Owner's first scope answer was an empty selection; a second question settled it as 'Exclude all five'."
  - "The 1805-command replay corpus grows with every session, so the baseline (158 judged, 8.8%) and the new share are measured on one frozen snapshot taken at the start of Verify, not on the live transcripts."
---

# PRD: Judge the same-call heredoc body

## Problem statement

An agent opens a pull request in a single Bash call that writes the body to a file and runs `gh pr create --body-file` on it: `cat > F <<'EOF' ... EOF`, then `gh pr create --body-file F`. The PR-body hook reads a body file only from the first command, so at hook time the file is absent or stale and the hook passes the command without judging it. Detector B then fails the PR in CI, after it is open. On a replay of 1805 historical `gh pr create` commands the hook judged 158 (8.8%); 681 (38%) were this one shape (issue #1633).

## Solution

When a `gh pr create --body-file F` follows, in the same Bash command, a heredoc that writes F, the hook judges that heredoc's text as the body, through detector B's one owner, and refuses a body B would fail with exit 2 and B's own strings. A binding the hook cannot establish still passes with a "not checked" note: the hook stays fail-open.

## Actors

- **Pipeline Worker** — an autorun stage subagent or a conduct Worker that opens a PR from one Bash call.
- **Scheduled routine** — an unattended cloud routine (merge train, hourly improvement) that opens a PR with no human watching.
- **Owner session** — the Owner working interactively in this repo.

## User stories

1. As a Pipeline Worker, I want a bad body written by heredoc to be refused before the PR exists, so that I fix it in the same turn instead of after a red B check.
2. As a Scheduled routine, I want the same refusal, so that an unattended run does not open a PR that fails detector B.
3. As an Owner session, I want a body that B accepts never to be refused, so that the hook costs me no false block.
4. As the Owner, I want the judged share measured on the same replay corpus before and after, so that I can see whether the change moved coverage.

## Success criteria

- [ ] The demo runs as written. One Bash payload that writes a body lacking both required lines and opens the PR from it:

      ```
      cat > /tmp/b.md <<'EOF'
      just a description
      EOF
      gh pr create --title t --body-file /tmp/b.md
      ```

      exits 2, with stderr carrying detector B's own problem strings for the missing work-order line and the missing closing line, then the hook's pointer line.
- [ ] The same payload with a body that carries a `No work order:` line and a `Closes #N` line exits 0 and prints nothing on stderr.
- [ ] On one frozen snapshot of the replay corpus (every unique Bash command containing `gh pr create` in the Owner's session transcripts, taken at the start of Verify), the judged share is at least 40%, against a baseline of 158 of 1805 (8.8%) measured by #1633. Judged means the hook exited 2 or exited 0 silently on a body it read.
- [ ] On that snapshot, for every command the new binding judges, the hook exits 2 if and only if `gates.pr_body_problems` of the same body text is non-empty. A refusal B would not give fails the run.
- [ ] A binding the hook cannot establish passes with a "not checked" note and exit 0: a heredoc with shell expansion in its text, a file rewritten or removed by a later command in the same compound, and a `--body-file` that names a different file than the heredoc wrote. No exception escapes `preflight()`.
- [ ] Fixture tests in `tests/test_pr_body_preflight.py` cover each shape above plus a quoted delimiter, an unquoted delimiter without expansion, `<<-`, and a compound command with a leading `cd`, and every test that passed before still passes.
- [ ] The check's patterns still have one owner: the hook calls `gates.pr_body_problems` and carries no copy of detector B's regexes (the existing one-owner test still passes).
- [ ] `python3 run_tests.py`, `python3 lint.py`, `python3 gates.py` and `python3 gates.py --selftest` all pass.

## Out of scope

- Body files written in an earlier Bash call: about 320 of the unjudged commands name a file that is gone by hook time.
- Bodies whose text holds `$` or a backtick the hook cannot expand (265 commands).
- Bodies set by `gh pr edit` or a `gh api` PATCH, and PRs aimed at other repositories.
- Logging each refusal the hook makes; whether this hook may keep state is a separate decision.
- Judging PR bodies at the forge for any tool (the Moonshot, saved as a seed).

## Open questions

- Where does the heredoc-to-file binding live, and how does it report a binding it cannot establish? — Architect.
- What exactly counts as "rewritten or removed by a later command in the same compound": `>`, `>>`, `rm`, `mv`, `tee`? — Architect, from the replay shapes.
- How is the corpus snapshot frozen and stored so the baseline and the new share are comparable? — Verify, with the Owner.

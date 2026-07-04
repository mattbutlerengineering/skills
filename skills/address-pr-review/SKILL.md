---
name: address-pr-review
description: Use after you've authored a pull request and reviewer feedback needs acting on — fixing what review comments ask, pushing the changes, replying to and resolving every thread, and merging the base branch (usually main) into yours when behind or conflicting. This works the feedback on an existing PR; it is not a quality review of the run's changes (that's review) and not passive watching of a PR's checks.
---

# Address PR Review

Work the feedback on a pull request you authored: gather its full state,
address each actionable comment in code, push, close the loop on every
thread, and get the branch mergeable again. Active by design — this skill
fixes and replies; it never just watches.

## Process

1. **Identify the PR.** The open PR for the current branch, or the one the
   user names. Use whatever PR tooling the harness provides (for GitHub,
   the `gh` CLI). If no PR exists, say so and stop — authoring one is not
   this skill's job.

2. **Gather the PR's full state** before changing anything:
   - every review thread and comment, noting which are unresolved;
   - CI status per check;
   - mergeability against the base branch (behind? conflicting?).

3. **Triage each unresolved thread** into one of:
   - **actionable** — the code should change; note what and where;
   - **decline with rationale** — the ask conflicts with the change's
     intent, the repo's conventions, or a recorded decision (cite it);
   - **question** — answer it; no code change.

4. **Address the actionable comments in code.** Group related asks into
   coherent commits. Run the repo's own verification commands (tests,
   lint — discover them from the repo, don't assume a stack) before
   pushing, and push only when they pass. If verification is red, fix it
   or surface the failure — never push a red build onto a PR under review.
   Push to the PR branch; never force-push over history a reviewer has
   already read.

5. **Reply to every unresolved thread, then resolve it.** Each reply states
   what changed (with the commit that changed it) or why no change was
   needed. Resolve the thread only after replying — a resolved thread with
   no answer reads as a dismissal. Leave threads you genuinely cannot act
   on unresolved, with a reply saying what's blocking.

6. **Reconcile with the base branch** if the PR is behind or conflicting:
   merge the base branch into the PR branch, resolve conflicts preserving
   both the PR's intent and what landed on the base, re-run verification,
   and push.

7. **Report.** Summarize per thread: fixed (commit), declined (reason), or
   blocked. Note CI status after the final push. Merging the PR stays with
   the user unless they've said otherwise.

## Rules

- Never force-push to rewrite commits reviewers have seen.
- Never resolve a thread without a reply on the record.
- Declining a comment is legitimate; ignoring one is not — every thread
  gets an answer.
- Verification runs before every push, not just the last one — and a red
  result blocks the push; fix or surface first.

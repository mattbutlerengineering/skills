---
stage: operate
run: feature:pr-body-hook-coverage
date: 2026-11-09
users-observed: 0
signal-source: "A scan of 4900 session transcripts of the Owner's account (every main and subagent .jsonl under the Claude Code projects directory for this machine's user) for Bash tool calls containing `gh pr create` after 2026-11-09T18:53Z, the first milestone merge (2c8b88a). The newest event in any transcript is 2026-11-09T05:10Z, so 0 sessions, 0 `gh pr create` calls and 0 hook decisions fall after the merge. The hook still logs nothing, so nothing else counts it."
---

# Retro: Judge the same-call heredoc body

## Read this first: hours, not a settled outcome

The four milestones merged between 2026-11-09 18:53Z and 20:05Z, the ship
record is #1681, and this retro was asked for the same evening. It reflects
hours of use by one account, not a settled outcome. The Owner asked to run it
now, so the stage ran; the soft gate's "let it breathe" offer was made and
declined. What would change it: transcripts dated after the merge that hold
`gh pr create` calls (the scan method is in `signal-source`, and re-running it
in a week gives the real count), a refusal log (the open seed "Log each
refusal the PR-body hook makes" is the only way to count blocks without
transcripts), and a replay on another day or machine, since the 25% margin is
24 commands and depends on the disk.

## Population

Counted by the scan in `signal-source`, counts only:

| Measure | Count |
|---|---|
| Transcripts scanned | 4900 |
| Sessions with a `gh pr create` Bash call after 2026-11-09T18:53Z | 0 |
| `gh pr create` calls after that time | 0 |
| Hook blocks (a PreToolUse error naming pr-body-preflight or "B: PR body") | 0 |
| Blocks followed by a corrected retry | 0 |
| Blocks whose retry kept the same body semantics (a suspected false block) | 0 |
| Blocks on a command that was not a real PR creation | 0 in the scan |

The newest transcript line on disk is about 13.7 hours older than the first
merge, so the sessions that ran with the hook live have not been written to
that directory (or are held elsewhere); the scan cannot see them. That is a
limit of the scan, not a finding that nobody used the hook. `users-observed` is
therefore 0 and every outcome is `unobserved`.

One observation exists outside the scan: during the launch-demo dry run
for this run, the hook is reported to have blocked a contrived quoted-string
command that was not a real PR creation. It is in no committed artifact and no
transcript the scan reached, so it is not counted, not classified beyond "a
block on a non-PR command", and not verified here. It is an anecdote (one
case), and it is the one place a false block may already have happened; the
seed below turns it into a fixture.

### Amendment 2026-11-11: re-scan over both transcript stores (#1694)

The population above and the frontmatter are the first scan's, left as
written. That scan read only the Claude Code projects directory, whose newest
event was 2026-11-09T05:10Z. This entry re-runs it over that directory and the
omp session store (`~/.omp/agent/sessions`), which holds this machine's omp
sessions. Counts and timestamps only; no command, body or session path text.

Method: every main and subagent `.jsonl` in both stores, all repositories (the
first scan was not filtered by repository either), events after
2026-11-09T18:53Z. A `gh pr create` call is a Bash tool call whose command
text contains that string (the first scan's rule, so it counts a mention as
well as a run). A hook block is, in the Claude store, a PreToolUse
`hook_blocking_error` record naming the preflight command; in the omp store, a
failing bash result that carries the hook's stderr strings. A corrected retry
is a blocked `gh pr create` followed in the same session by an unblocked one.
A session is the Claude `sessionId` or the omp session directory (subagent
files grouped under their parent). The two stores share no session id (0
overlap), so no session needed deduplicating.

| Measure | Claude store | omp store | Total |
|---|---|---|---|
| Transcripts scanned | 6617 | 828 | 7445 |
| Newest event | 2026-11-11T17:26Z | 2026-11-11T17:27Z | 2026-11-11T17:27Z |
| Sessions with a `gh pr create` Bash call | 0 | 30 | 30 |
| `gh pr create` Bash calls | 0 | 78 | 78 |
| Hook blocks | 0 | 0 | 0 |
| Blocks followed by a corrected retry | 0 | 0 | 0 |
| Blocks on a command that is not `gh pr create` | 0 | 0 | 0 |

What the numbers are and are not:

- Observed: the transcript counts, the newest timestamps, the 30 sessions and
  78 calls in the omp store, and 0 `gh pr create` Bash calls in the Claude
  store after the merge (3 other Claude lines mention the string inside an
  Agent prompt, not a Bash call, and are not counted).
- The omp store holds 4 failing bash results that quote the hook's strings (2 of
  them its exact exit-2 stderr). All 4 come from commands that name the
  preflight script themselves, which a worker ran by hand to probe it, so none
  is a hook decision; they are not counted as blocks.
- Inferred, not observed: that the hook does not run in omp sessions. The hook
  is a Claude Code PreToolUse command registered in `.claude/settings.json`.
  The omp hook docs describe only TypeScript/JavaScript factories found under
  `.omp/hooks/pre` and `.omp/hooks/post`, and neither the repository nor the
  user agent directory has such a directory; the docs never mention a
  `PreToolUse` command or `settings.json` hooks. A block would show in an omp
  transcript as a failing bash result carrying the stderr strings, so the store
  could record one, but none of its 78 calls shows a hook decision, and with no
  evidence the hook runs there, the omp 0 is not an observed 0 for the hook:
  it is the absence of a hook that was likely never live. The omp
  sessions are real `gh pr create` use, but not use of the hook.
- The Claude store is the only one where the hook should have run. Its 0 is
  an observed 0 for blocks and retries, over 0 calls: nobody ran a Bash
  `gh pr create` there after the merge, so it says nothing about false blocks.
- Still not seen: the hook logs nothing, so a block that left no transcript
  record, or a session whose transcript was never written, is invisible. The
  quoted-string anecdote above is still uncounted.

`users-observed` stays 0: no hook decision exists in either store after the
merge. The newest-event gap the first scan reported (13.7 hours before the
merge) is closed: both stores now reach 2026-11-11. The frontmatter is left
unchanged: the skill's form carries one population figure there, which is
unchanged at 0, and the dated body entry keeps the first scan's figure
readable beside this one.

## Outcomes vs. intent

### The demo is refused before the PR exists (PRD criteria 1 and 2)

- What happened: state, not use. A payload that writes a body lacking the
  work-order and closing lines by heredoc and runs `gh pr create --body-file`
  in the same call exits 2 with detector B's two strings and the pointer line,
  and its passing twin exits 0 silently, both through `preflight()` and through
  the hook command as `.claude/settings.json` registers it
  (`verification.md` criteria 1 and 2; `release.md` post-release checks). No
  live refusal has been observed.
- Signal strength: unobserved.

### The judged share rises on one frozen snapshot (PRD criterion 3; idea.md's one-sentence success)

- What happened: state of a pre-release replay, not use. On one frozen snapshot of 1817 commands the judged share went from 229 (12.60%)
  to 479 (26.36%), against the PRD's amended 25% target (455 commands needed,
  margin 24) and a reachable ceiling of 778 (42.82%). `idea.md`'s own
  sentence, at least 40% on a 1805-command corpus, is not met and was
  superseded on 2026-11-09 after the Architect stage (the design's safe
  ceiling was about 26.5%, and the 681 same-call count behind the 40% was not
  reproducible: 549 here, 548 in the probe). The margin depends on the disk:
  with no cwd in any payload the same snapshot gives 348 (19.15%), under the
  bar, because 57 bound commands are stopped by the target check and 873 rows
  name a directory that is gone. Live coverage is unmeasured.
- Signal strength: unobserved for live coverage; the replay is a one-snapshot
  measurement and is labelled as such, not a result for users.

### No refusal that detector B would not also give (PRD criterion 4; the Owner's named biggest risk)

- What happened: state. The false-block oracle paired 250 of 250 commands
  judged through the binding with the file a real shell wrote from the heredoc
  alone, 0 unpaired and 0 disagreements. It never ran the commands between
  writer and reader: only 8 of the 250 had one (5 `cd`, 3 `grep`), and the
  `git`, `gh`, `printf`, assignment and `export` branches of the inert list
  have no corpus command. No false block has been reported, and the scan saw no
  session to report one. One unverified report of a block on a non-PR command
  sits above.
- Signal strength: unobserved.

### Unattended routines stop going red on a bad same-call body (the PRD's problem statement)

- What happened: not measurable from here. Whether the hook is live in the
  cloud routines at all is the open seed on `CLAUDE_PROJECT_DIR` from the
  pr-body-preflight retro; nothing in this run settled it.
- Signal strength: unobserved.

## Open debt

The run's own debt. None of it is feedback and none of it counts toward the
population.

- #1655 — eight P3 precision gaps in architecture.md, from the third
  architecture review (Decompose absorbed them as the first item).
- #1661, #1664, #1667, #1670 — milestone 1 to 4 review follow-ups, all
  created before the run's last merge.
- #1677 — lean sweep: cut the between-writer-and-reader branches that lose no
  corpus command; deferred from Review (the major finding). Needs a fresh
  Verify replay before it lands.
- #1678 — five Review minors (findings 3 to 7) and the `deepen` handoff.
- #1679 — Architect amendment (findings 2 and 4), collecting #1664, #1667 and
  #1670.
- #1633 — the issue this run started from, created before the run; its
  figures are superseded by `verification.md`.
- #1682 — this Operate stage's own tracking issue.

## Run retrospective

Stages: Idea #1635, PRD #1643, Architect #1652, Decompose #1657, four
milestones (#1660, #1663, #1666, #1669), Verify #1674, Review #1676, Ship
#1681; every milestone had one or two reviews.

- Keep: the replay-before-claim habit. The Architect probe on a re-extracted
  corpus caught the over-reach in the 40% target before any code was written, and Verify's
  oracle (a real shell on the heredoc alone, paired 250 of 250) is a stronger
  test than any hand-picked fixture and is the reason the false-block risk can
  be called measured rather than argued. Keep the milestone reviews: each
  found real gaps (`2>&1` reversed, `exec` wrappers, steering names, trap
  forms) before they merged. Keep the independent final Review: its lean pass
  was the only thing that saw the 160 lines no corpus command uses.
- Change: set the number after the probe, not before it. The success sentence
  said 40% on an estimate from an issue whose figures were not reproducible
  (681 against 549), and the PRD was amended to 25% after Architect; the
  amendment was honest and cheap, but the idea's headline target never
  survived contact with a corpus. Put a spike that re-derives the ceiling
  before the Idea's success sentence is written. Also: review rounds of 7 to
  10 minutes each, four milestones, 1 to 2 reviews apiece and a flag list at
  every milestone (#1655, #1661, #1664, #1667, #1670) meant most of the wall
  time went to precision gaps in one 1098-line module; design the invalidation
  as the smaller rule set the lean cut proposes (#1677) rather than the
  fail-closed maximum and relaxing it.
- Stop: ticking a breakdown Accept line before a fixture pins its literal
  payload (the `2>&1` line was ticked while the code gave a note, #1667), and
  carrying design deltas only in breakdown Notes while architecture.md says
  otherwise.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| architecture.md names a `Ledger` and a `_bound_body(commands, heredocs, position, spelling)` signature the code never had; the deltas lived only in breakdown Notes | `review.md` §Minor: architecture.md describes a binding the code is not | mechanical | `gates.py` detector D (`_architecture_drift`, the `tree-claims` fence): extend it from file paths to named functions and classes, so a signature the architecture names that the tree lacks is a problem string. Today D checks only files, so nothing compared the architecture's names with the code |
| The 25% margin is 24 commands and moves with the disk: 19.15% with no cwd, 57 bound commands stopped by the target check, 873 rows naming a gone directory | `verification.md` §Summary and §Criterion 3 | judgement | `skills/verify/SKILL.md`: report any measured threshold with the state it depends on and the figure without that state, beside the margin. A deterministic check would need a hermetic checkout for the replay, which no existing check provides (seed below) |
| The idea's 40% target and #1633's 681 same-call figure were not reproducible (549 and 548 on re-extraction); the PRD was amended to 25% | `prd.md` assumptions (Owner decision 2026-11-09); `verification.md` §Not verified | judgement | `skills/idea/SKILL.md`: re-derive any count the success sentence rests on, with the measuring command named, before the sentence is written |
| About 160 lines of between-writer-and-reader and before-the-writer machinery have no user on the corpus; caught only by the Review lean pass | `review.md` §Major (#1677) | judgement | `skills/lean/SKILL.md`, run at each milestone in Implement; the cut-list tag `speculative` is the Review-stage form of it. No deterministic check knows which branch a corpus uses |
| Duplicated constants and reason strings in one module (the literal rule twice, two reasons twice, the name pattern five times) and two heredoc representations | `review.md` §Minor: parallel heredoc representations (#1678) | mechanical | `one_owner.py`, which finds values stated twice, but it runs in no hook, no CI job and not in `make check` (CLAUDE.md says so), and exits 1 today on 4 standing problems; it also cannot see duplicated logic. Finding: the repo's own one-owner check has no guardrail |
| Tests pin private structure at seven sites (`_Unrun`, `_mask_heredocs`, `_tokens`, a patched `_bound_body`), as the breakdown's Accept lines asked | `review.md` §Minor: tests pin private structure; `breakdown.md` Capture and Keep items | judgement | `skills/decompose/SKILL.md`: an Accept line names a payload through the public seam (`preflight()`), not a private function |
| A breakdown Accept line was ticked while the code contradicted it (`2>&1` judged; the reader-joiner regex looser than the chain rule) and was found by milestone review | `breakdown.md` Notes (Implement, Milestone 4, follow-ups from #1667 and #1661); #1661, #1667 | mechanical | `tests/test_pr_body_preflight.py`: one fixture per literal payload an Accept line names, written failing first. The notes record that some could not fail first, so the fixtures arrived with the follow-ups |
| A leading redirect-only command truncating the body file leaves the hook reading a stale passing file (an under-block) | `review.md` §Minor: the first-command path reads disk (#1679) | mechanical | `tests/test_pr_body_preflight.py`: the 40000-variant fuzz the reviewer ran, kept as a fixture over the binding's shapes, would hold shapes of this kind; it was throwaway |
| The not-first note blames "first command" when a same-call writer exists; the kb page does not say which writers bind | `review.md` §Minor: the not-first note; §Minor: the kb page (#1678) | judgement | `docs/kb/pr-body-contract.md`, with `kb.py lint` holding its stamp; the note text is pinned by one test that would carry the new wording |
| The first Verify snapshot dedupe kept transcript lines with no cwd, and the file was frozen twice | `verification.md` assumptions; `release.md` §Outcome | judgement | The hand-off's point 1 in `breakdown.md` Notes (each row carries its cwd): it names the field, not a check that rows without one are zero; caught by the worker before any measurement |
| The oracle's hand sample was set at 20 before anyone knew only 8 commands had a command between writer and reader | `verification.md` §Criterion 4; `breakdown.md` hand-off | judgement | `breakdown.md` hand-off wording: "20, or all that exist" |
| Architecture drift as a class: the design named signatures and a data structure; Implement built others; nothing compared them until the final Review read the code | `review.md` §Minor 1; `architecture.md` Interfaces | mechanical | Same carrier as the first row: `gates.py` D |
| The `one_owner.py` command runs under no hook and no CI job; four standing problems on main are outside any run | `verification.md` §Criterion 7; `CLAUDE.md` | mechanical | `Makefile` `check` target (what CI's validator runs), after the four problems are resolved |

## Idea seeds

- Extend gates detector D so a function or class named in a run's architecture.md that is absent from the tree is a problem string, not only a missing file (from: feature:pr-body-hook-coverage)
- Add `one_owner.py` to `make check` once its four standing problems are resolved or marked, so a duplicated fact fails CI instead of reading as an advisory (from: feature:pr-body-hook-coverage)
- Rerun the pr-body-hook-coverage replay on a clean checkout and on a different day against the frozen snapshot, and record how much of the 24-command margin the disk owns, before issue #1677 cuts any branch (from: feature:pr-body-hook-coverage)
- Add a rule to idea that a success sentence stating a measured share names the command that measured its baseline and ceiling on the same corpus, so a target is not lowered after Architect (from: feature:pr-body-hook-coverage)
- Re-run the Operate scan of Owner transcripts for the PR-body hook one week after 2026-11-09, count sessions, blocks, retries and any block on a command that is not a real PR creation, and record the counts in a follow-up retro (from: feature:pr-body-hook-coverage)
- Turn the launch-demo dry-run block on a contrived quoted-string command into a fixture, and decide whether the hook may judge a `gh pr create` that sits inside a quoted string at all (from: feature:pr-body-hook-coverage)
- Keep the reviewer's 40000-variant token-insertion fuzz of `pr_body_preflight.py` as a test, so the fail-open contract and the no-exception rule are held by a deterministic check (from: feature:pr-body-hook-coverage)

## Run complete

Closed 2026-11-09 on hours of use, population 0 observed. The seeds above are
the input to the next Idea-stage run; the first useful one is the re-scan in a
week, which turns every `unobserved` above into a count or confirms it still
has none.

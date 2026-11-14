---
stage: operate
run: feature:kb-from-knowledge-work-plugins
date: 2026-11-13
users-observed: 0
signal-source: "own scan on 2026-11-13, four days after the 2026-11-09 merge of #1609: every tool call in ~/.claude/projects and ~/.omp/agent/sessions touched since 2026-11-09 (this run's own building and verifying sessions excluded) searched for kb.py harvest, kb_harvest and --memory, plus git log of docs/kb, kb.py, kb_harvest.py and skills/knowledge-base on origin/main and the issues opened since the merge; no one ran harvest or wrote a new page field"
---

# Retro: Teach the knowledge base what it cannot see yet

## Outcomes vs. intent

Intent (`idea.md`, success in one sentence): `kb.py lint` flags an
external-fact page past its declared age, and harvest proposes the three
duplicated memories as NOOP/CONFLICT and a memory-only gotcha as an ADD
candidate, every new candidate still going through the human-promotes
rule. Population: 0. The scan, with what each source held:

- Claude Code and omp transcripts, two stores, every session file touched
  since 2026-11-09. `kb.py harvest` or `kb_harvest` appears in 138 request
  blobs, 130 CLAUDE.md instruction attachments (a consumer repo's stage-hook
  table naming `kb.py harvest` for its retros) and 41 messages. Not one is a
  tool call; the only tool call that names it is the query that ran this
  scan. `--memory` was never passed. The knowledge-base skill was never
  invoked as a skill in any store.
- `docs/kb/`: the only page declaring `checked-against`, `checked` and
  `max-age` is `main-unprotected.md`, which this run wrote. It is not due
  until 2026-12-08. The six later kb changes (#1632, #1672, and the hourly
  re-verify pull requests #1759, #1761, #1763, #1765, #1767) each change one
  `verified:` stamp or one page body by hand. None touches a new field, and
  none cites a harvest.
- Issues opened since the merge: none mentions harvest, memory candidates or
  the age check.

### `kb.py lint` flags an external-fact page past its declared age

- What happened: the feature is in main and untouched by use. The one
  declaring page is not past its age, so lint has flagged nothing for real.
  Offline fixture tests show the flag; no real page has reached it.
- Signal strength: unobserved

### `kb.py harvest --memory` lists the repo-scoped memory entries beside their duplicate pages

- What happened: no one has run it. `verification.md` PRD 32 steps 3 and 4
  (the real memory directory, a model session proposing NOOP, CONFLICT and
  ADD) were NOT RUN and still are. The state is: shipped, tested on
  fixtures, never run on real memory.
- Signal strength: unobserved

### Harvest lists human corrections and answered questions (`human_turns`)

- What happened: no one has run it, so PRD 13 (the precision of the kind,
  a hand count over real interactive transcripts) has no count and the
  default-on assumption in `architecture.md` is untested.
- Signal strength: unobserved

### The lessons the run named as memory-only reach the knowledge base

- What happened: two of the four gotchas the idea named as memory-only
  (`gh pr edit` failing where the REST route works, and a closing keyword
  binding only the first issue) reached `docs/kb/pr-body-contract.md` in
  #1632 two hours after the merge. The pull request records them as
  "found fixing a red B on #1629": a person met the traps live and wrote
  them, not harvest or memory. The need the run bet on is real; the shipped
  path was not the one used.
- Signal strength: anecdote (one pair of traps, one session; it says the
  need exists, not that the feature met it)

### Other signals checked, not counted

- A consumer repo's retros of 2026-10-22 record real harvest runs (623
  transcripts, 51 arcs). They predate the merge and ran the old two-kind
  harvest, so they count for neither this release nor its new kinds. They do
  show a standing operate hook that would carry the new kinds when its next
  retro runs.
- The hourly re-verify pull requests keep the kb alive by the old staleness
  check (`verified:` against the cited sources), which this run did not
  change.

## Open debt

The run filed no issue of its own. Its debt lives in two artifacts and
counts toward nothing:

- `verification.md` PRD 13: precision of the `human_turns` kind, owed to the
  Owner on real transcripts (Verify carry-forward).
- `verification.md` PRD 32 steps 3 and 4: the demo against the real memory
  directory, owed to the Owner (Verify carry-forward).
- `review.md` §Findings, two deferred minors: `CORRECTION` matches replies
  that are not pushback ("No problem, carry on"), and a human turn whose
  first item is a harness tag is skipped whole (Review deferrals).
- Issues #1614 and #1617 were opened after the merge but are the release
  record and this retro's own reminder, not feedback.

## Run retrospective

- Keep: the Review stage's break-it probes. Fixture-driven attacks on the
  user-scope exclusion, symlinks and absurd `max-age` found three majors
  that no earlier test pinned, and mutation of the exclusion block proved
  the tests were not vacuous. Also keep the brief's "fixtures only, never
  the real memory" rule: it kept a privacy-sensitive feature safe to
  build.
- Change: two success criteria could only be satisfied by a human on a real
  machine (PRD 13, PRD 32), and four days on neither has run, so the run
  closes with its headline demo unrun. Name the person and the date for such
  a criterion at PRD time, or move it out of the success criteria. Release
  authorization none meant nothing carried them past the merge.
- Change: ship without a way to see use. Harvest prints to stdout and writes
  nothing, by design, so even when someone runs it the repo keeps no trace.
  A retro four days later can only report that it found none.
- Stop: widening a feature run to eight items when evidence came for two
  (observed here) and one anecdote. The Owner's ruling kept all eight and
  that was their call; the count above is the cost, because five items
  (class pages, symptom summaries, setup question, wrong/right pair,
  verified-against) have no signal of any kind to read yet.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| `kb.py lint` crashed with a traceback on an absurd `max-age` instead of a problem string | `review.md` §Findings, third Major | mechanical | `tests/cli_contract.py`: pin that a root tool never exits with a traceback on a malformed field, with one malformed-field fixture per tool |
| Harness-injected text and symlinked memory entries reached harvest output; found by a reviewer's hand-built fixtures, not by tests | `review.md` §Findings, first and second Major | mechanical | a fixture-matrix test in `tests/test_kb_harvest.py` over the shapes the review probed (symlink, flow mapping, injected tag), so the next harvest kind starts with them |
| Two criteria needed a human and a real machine; no stage owned them after merge | `verification.md` §Not verified, PRD 13 and PRD 32 | mechanical | a gates detector that fails a `verification.md` whose NOT RUN line names no owner and no date, extending the existing detectors over artifacts |
| Nothing records that harvest or the age check was used, so Operate has no measure | this retro, §Outcomes vs. intent | judgement | the operate hook in a consumer's CLAUDE.md, which already asks retros for a "Gotcha harvest" line; extend the line to count candidates proposed and promoted |
| `kb.py lint` runs in no CI job or hook, so the age check the run shipped flags nothing unless someone runs it by hand | `review.md` §Scope, date-dependent lint in CI; the 2026-10-16 backlog seed on `kb.py lint` in `make check` | mechanical | the `check` job in `.github/workflows/validator.yml` or `make check`, after the existing shallow-checkout problem is solved (a depth-1 checkout makes lint report every page "not a commit") |

## Idea seeds

- Run `python3 kb.py harvest --memory` over the real memory directory and hand-label each `human_turns` candidate, then record both counts as an addendum to verification.md, since PRD 13 and PRD 32 were never run (from: feature:kb-from-knowledge-work-plugins)
- Re-check docs/kb/main-unprotected.md on or after 2026-12-09: confirm lint flags it past its 30d age, and that the two declared commands were re-run and `checked:` moved, then record whether anyone acted on the flag (from: feature:kb-from-knowledge-work-plugins)
- Have `kb.py harvest` append one line per run (date, kinds, counts) to a file outside docs/kb, so the next retro can count real use instead of searching transcripts (from: feature:kb-from-knowledge-work-plugins)
- Add a `Gotcha harvest` count line (candidates proposed, promoted) to the operate retro template so each retro that runs harvest records its yield (from: feature:kb-from-knowledge-work-plugins)
- Fix the CORRECTION pattern so "No problem" and "Never mind" are not pushback, and let a turn that opens with a harness tag keep its typed words, once PRD 13's hand count exists to judge it (from: feature:kb-from-knowledge-work-plugins)
- Add a gates check that a NOT RUN line in verification.md names an owner and a date, so a criterion for a human is never left to a later stage by default (from: feature:kb-from-knowledge-work-plugins)
- Re-run this Operate scan on 2026-12-13 across both session stores and the next consumer retros, counting harvest runs, `--memory` runs, pages declaring `max-age` and class, symptom-first or wrong/right pages, and record the counts in a follow-up retro (from: feature:kb-from-knowledge-work-plugins)

## Run complete

Closed 2026-11-13. users-observed is 0: the shipped feature has not been
run by anyone in the four days since the merge, and no outcome above reads as
landing, adopted or used. Seeds above are the input to the next Idea-stage
run.

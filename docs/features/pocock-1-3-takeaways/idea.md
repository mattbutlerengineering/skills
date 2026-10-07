---
stage: idea
run: feature:pocock-1-3-takeaways
date: 2026-10-06
assumptions:
  - "Idea-stage inputs came from the orchestrator's autorun brief (its 'Idea-stage inputs' section is marked as the orchestrator's reading), not a live interview; the user's own words were one sentence: 'matt pocock 1.3 was released see what we can take and learn from this'."
  - "The optional last30days corroboration was not run: the skill says never run it unasked, and the brief does not ask for it, so the brief alone is the complete interview result."
---

# Idea: Pocock 1.3 takeaways

## Problem

A maintainer of this skills repo reads a peer skills repo's release and has
no cheap way to know which of its lessons already apply here. The one lesson
that does apply right now is a silent loader incompatibility: six of our
skill descriptions are invalid under a strict YAML parser, and nothing in
this repo checks for it. The harnesses we run on are permissive, so the
defect is invisible until a stricter loader drops the skills without a
word.

## Who has it

The repo owner, alone. They cope by reading release notes by hand and asking
an agent to compare the peer repo against this one. One such comparison
produced this run; the comparison itself is the cost being paid today.

## Why now

mattpocock/skills v1.3.0 and v1.3.1 shipped on 2026-10-04, two days ago. The
YAML defect its patch notes name is live in six skills here today, and the
release also carries four judgement-call practices (merge-danger in PR
bodies, environment retrospectives, tool-naming hand-offs, two small
worker and glossary conventions) that are cheapest to weigh while the
source material is fresh and already downloaded.

## Evidence

- **Hard count.** Six of the twenty-five `skills/*/SKILL.md` descriptions
  contain an unquoted colon-space: audit, automate, deepen, doctor,
  pipeline-board, work-queue. Re-counted 2026-10-06 by a read-only script
  over this worktree; the count and the names match the brief. None
  contains an unquoted space-hash.
- **Anecdote, one peer repo.** Pocock's patch notes (his #911) report the
  same defect in six of his skills, which `skills.sh` then skipped. One
  repo, one incident; it shows the failure mode is real, not how common
  it is.
- **Anecdote, one peer repo.** Pocock's most-reported problem (his #878,
  #880) was a skill naming another skill in prose and the second skill not
  loading. Our `next` router hands off in prose. We have no report of our
  own that it fails; this is his evidence, not ours.
- **Anecdote, this session.** A detached-HEAD incident during this run's
  own orchestration is the kind his worker base-check rule prevents. One
  occurrence.
- The other borrowings (PR-body merge-danger call, environment retro,
  glossary filename) rest on judgement, not measurement, and are labelled
  as such.

## Solution hunch

Five small edits to existing skill and protocol text plus one lint rule;
nothing new is built. Reword the six descriptions, then pin the rule in
`protocol.py`'s `skill_frontmatter_problems` (the seam owner, ADR-0052) so
it cannot recur. Add a pull-request-body section to the protocol that the
work-queue brief, ship, and the improvement routine point at. Give Operate
an environment-retrospective step whose output `automate` reads as friction
evidence. Decide, after checking omp (ADR-0027), whether hand-offs should
name the tool. Read `GLOSSARY.md` beside `CONTEXT.md`, and give work-queue
workers the base-and-tip rules. Three of Pocock's changes were read out as
not recommended now: deleting skills the model handles unaided, marking
skills user-invoked only, and the em-dash purge.

## Success in one sentence

A strict YAML loader sees every skill, and the four other lessons are each
either adopted in the skill text or rejected with a recorded reason.

## Unknowns & risks

- omp may have no model-callable skill tool, which kills the tool-naming
  borrowing outright; that is why it starts with a check rather than an
  edit.
- Rewording six descriptions changes routing-eval trigger text. The routing
  eval costs money and will not be re-run in this run, so a routing
  regression would surface later, not here.
- `factory/manifest.json` is also touched by three other unmerged branches;
  whichever lands later regenerates it, and a stale manifest fails
  detector E.
- The brief's claim that Claude Code and omp both parse the current
  descriptions permissively is the orchestrator's reading, not something
  verified in this stage.

## Work already in flight

The protocol's guard ran. The brief records that eleven open pull requests
(#585, #589, #595, #596, #597, #598, #600, #602, #604, #606, #608) were read
by title and branch on 2026-10-06 and none does this work; #598 touches the
decompose skill and #602 touches `work_queue.py`, neither overlapping. A
read-only re-listing during this stage returned the same eleven. Outcome:
nothing matches. This run starts from the user's message, not a backlog
seed; `docs/backlog.md` line 6 is adjacent and stays out of scope.

Next stage: PRD, via the `prd` skill or the router.

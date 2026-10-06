---
stage: prd
run: feature:pocock-1-3-takeaways
date: 2026-10-06
id: PRD-0007
ux: not-applicable
ux-reason: no UI surface; deliverables are skill and protocol text plus a lint rule
assumptions:
  - "Interview answers came from the autorun brief and idea.md, not a live interview; every section below traces to the brief's 'What and why', 'Scope' and 'Success criteria' sections or to idea.md."
  - "The brief names one person (the repo owner) and no actor roles; the Actors section splits that person and the agents the borrowings serve into four roles (maintainer, merge reviewer, worker, stage agent) because the stories read differently per role. Taken without user input."
  - "Typed id PRD-0007 assigned as the next free id (highest existing is PRD-0006; no local or remote ref declares 0007), and coverage waivers added under the context sections following PRD-0006's pattern, so the breakdown cites Success criteria alone (ADR-0004, ADR-0072). The brief is silent on both."
---

# PRD: Pocock 1.3 takeaways

## Problem statement

<!-- coverage-waiver: context for the requirements below, not a deliverable; the Success criteria carry the work every breakdown row cites -->

A maintainer reads a peer skills repo's release and has no cheap way to know
which of its lessons already apply here. One does, today: six of this repo's
twenty-five `skills/*/SKILL.md` descriptions (audit, automate, deepen,
doctor, pipeline-board, work-queue) contain an unquoted colon-space and are
invalid under a strict YAML loader. Claude Code and omp parse permissively
and nothing in `lint.py` checks for it, so a stricter loader would drop the
six skills without a word, as `skills.sh` did to six of Pocock's. Four
further lessons from the same release (merge-danger in pull request bodies,
an environment retrospective, tool-naming hand-offs, two small worker and
glossary conventions) are judgement calls cheapest to weigh while the source
is fresh.

## Solution

<!-- coverage-waiver: narrates the same five borrowings the Success criteria check one by one; the breakdown rows cite those criteria, not this summary -->

Five small edits to existing skill and protocol text plus one lint rule;
nothing new is built. The six descriptions are reworded without changing
their trigger phrases and the rule is pinned where frontmatter facts already
live. The protocol gains one owning section on what a pull request body says
about its merge; the three places that write bodies point at it. Operate
asks what in the environment would have caught each mistake, and `automate`
reads the answer as friction evidence. The tool-naming hand-off is adopted
or rejected after a check against both harnesses, decision recorded either
way. Three skills read a target repo's glossary under either filename, and
work-queue workers get the base-and-tip rules.

## Actors

<!-- coverage-waiver: names who is involved; no actor is itself something to build -->

- **Maintainer** — the repo owner; edits skill and protocol text, reads
  peer releases, keeps `make check` green.
- **Merge reviewer** — the human at gate 2 (ADR-0033) who reads a pull
  request body and decides to squash-merge; today the same person as the
  maintainer, but reading rather than writing.
- **Worker** — the agent `work-queue` dispatches into its own worktree for
  one work order; it opens the pull request the merge reviewer reads.
- **Stage agent** — the agent running a stage or utility skill (`operate`,
  `next`, `audit`, `deepen`, `automate`) in this repo or a target repo.

## User stories

<!-- coverage-waiver: each story is realized through the Success criteria the breakdown rows cite, not built as separate work -->

1. As a **maintainer**, I want every skill description to be valid strict
   YAML and a lint rule to reject one that is not, so that a stricter loader
   cannot silently drop skills and the defect cannot come back.
2. As a **merge reviewer**, I want each pull request body to show the
   change, its before-and-after evidence, and a merge-danger call (one-way
   or two-way door, blast radius), so that the gate-2 decision rests on
   stated risk rather than on reading the diff cold.
3. As a **worker**, I want the pull-request-body shape stated once in the
   protocol and pointed at from my brief, so that I write the body the
   reviewer expects without a second copy of the rule to drift.
4. As a **stage agent** running Operate, I want the retro to ask, for each
   mistake of the run, what in the environment would have caught it and
   whether that is a mechanical check or a judgement rule, so that the
   finding lands as friction evidence `automate` can price.
5. As a **stage agent** running `next`, I want the hand-off wording decided
   against both harnesses and the decision recorded, so that the hand-off
   fires the same way on Claude Code and omp, or the reason it stays prose
   is written down.
6. As a **stage agent** running audit, deepen or automate on a target repo,
   I want its vocabulary read from `GLOSSARY.md` as well as `CONTEXT.md`,
   so that a repo on the newer convention is not read as having none.
7. As a **worker**, I want my brief to tell me to confirm my branch base is
   the default-branch tip before writing and to merge or rebase that tip
   before declaring done, so that I never build on a detached or stale base.

## Success criteria

- [ ] **Strict-YAML descriptions.** No `skills/*/SKILL.md` description
  contains an unquoted `: ` or ` #`, each stays within 1024 characters, and
  every trigger phrase of the six reworded descriptions survives (check: a
  read-only script over the twenty-five files; `git diff` of the six lines
  read side by side). `python3 lint.py` reports a problem for a fixture
  skill whose unquoted description carries `: ` or ` #`, none for a clean
  one, and a test asserts the exact problem string through the public
  interface and fails before the rule exists (check: run the new test
  against the pre-rule commit, then the post-rule commit).
- [ ] **Pull request body.** `docs/pipeline-protocol.md` has a section on
  the pull request body covering the smallest visual that shows the change,
  before-and-after evidence, and a merge-danger call naming the door and
  the blast radius, crediting mattpocock/skills `pr` and Dex Horthy's
  `show-me`; the work-queue worker brief (step 4), ship's rollback plan
  (pre-flight step 3 and `TEMPLATE.md`), and the improvement routine's PR
  skeleton each point at that section rather than restating it (check:
  grep each file for the section's name; the skeleton's first two lines are
  unchanged).
- [ ] **Environment retrospective.** Operate has a step after "Retrospect on
  the run itself" that names, per mistake, the check or rule that would have
  caught it and classifies it mechanical or judgement; `skills/operate/
  TEMPLATE.md` has an `## Environment` section (mistake, evidence, class,
  proposed carrier); `automate`'s surface table lists the Environment
  sections of `docs/**/retro.md`; Operate's `description:` line is
  byte-identical to before (check: grep, and `git diff` on that line).
- [ ] **Hand-off decision.** The protocol's Harness neutrality section
  records an adopt-or-reject decision on tool-naming hand-offs with its
  reason, and `next` step 5 is worded to match (check: read both; the
  decision names what was checked in omp).
- [ ] **Small borrowings.** `audit`, `deepen` and `automate` `SKILL.md` each
  name `GLOSSARY.md` beside `CONTEXT.md`; the work-queue worker brief
  carries both the base-check and the tip-merge rule (check: grep).
- [ ] **Battery and packaging.** On Python 3.12 and 3.14, `python3 -m
  unittest discover tests` prints `OK`, `python3 lint.py` prints `lint: 0
  problem(s)`, and `python3 gates.py && python3 gates.py --selftest` prints
  `gates: 0 problem(s)` and `selftest: ok`; `factory/manifest.json` is
  regenerated after the seam edit; `.claude-plugin/plugin.json` carries a
  bumped version; nothing under `evals/` changes and `LEDGER.md` is
  untouched (check: `git diff --stat main -- evals/ LEDGER.md` is empty).

## Out of scope

<!-- coverage-waiver: exclusions: by definition nothing here is decomposed into work -->

- **New skills** — no `pr` or `retro` skill of our own; every borrowing
  lands in existing skill or protocol text.
- **The three Pocock changes read out as noted, not recommended now** —
  deleting skills the model handles unaided, marking skills user-invoked
  only, and the em-dash purge.
- **Paid evals and maturity** — running `trigger_eval.py` or
  `charter_replay.py`, any edit under `evals/`, any LEDGER maturity change.
  The routing-eval exposure from rewording six descriptions is accepted and
  surfaces at the next on-demand run, not here.
- **Adjacent branches and trackers** — the lean/polish branch, the
  guarded-read branch, GitHub issues or pull requests, the `bd` tracker.
- **`docs/backlog.md` line 6** — whether the 1024 limit is chars or bytes
  touches the same check as the YAML rule and stays separate.

## Open questions

<!-- coverage-waiver: questions settled downstream by Architect, Implement or Ship, not requirements of this run -->

- Does omp expose a model-callable skill tool, so "call the skill tool with
  X" is neutral across both harnesses? — omp's `docs/skills.md`
  model-invoked section, read at Architect; decides whether borrowing 4 is
  adopted or rejected (ADR-0027).
- Does the lint rule also reject a *quoted* description, keeping the
  frontmatter reader a plain `key: value` splitter? — recommended yes, so
  every description stays a bare scalar; the brief leaves it to Implement.
- Plugin version 0.3.0 or 0.3.1? — depends on whether the lean/polish
  branch lands first; Ship records which.
- Who regenerates `factory/manifest.json` when this and the three other
  branches that touch it land in some order? — whichever lands last; the
  merge reviewer at gate 2 watches detector E.

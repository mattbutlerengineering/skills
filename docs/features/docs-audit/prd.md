---
stage: prd
run: feature:docs-audit
date: 2026-10-10
id: PRD-0010
ux: not-applicable
ux-reason: static documentation; no flows or screens
assumptions:
  - "Interview answers came from the autorun brief and idea.md, not a live interview; every section below traces to the brief's Feature, Scale, Scope (IN/OUT/DECIDED), User-facing surface or Release authorization sections, or to idea.md's Problem, Who has it, Evidence, Success and Unknowns sections."
  - "Typed id PRD-0010 assigned as the next free id: the highest id on main and this branch is PRD-0008, but the unmerged local branch feat/launch-demo already declares the id after PRD-0008 in docs/features/launch-demo/prd.md, and no local or remote ref declares PRD-0010. Coverage waivers added under the context sections following PRD-0008's pattern, so the breakdown cites Success criteria alone (ADR-0004, ADR-0072). The brief is silent on both."
  - "'Nothing stale remains' is made checkable by defining stale operationally: a passage is stale when it describes something the tree no longer has or no longer does (a removed file, a renamed module or checker, a retired command, a superseded ADR presented as standing, a roster or count that no longer matches). Whether a still-true passage is useful is not judged by any criterion; idea.md names that judgement as the way the audit dies. Taken without user input, under the skill's rule that every criterion must be checkable."
  - "Scope diffs are taken against feat/grok-harness, the branch this run is stacked on (brief, Scale), so #618's own edits to README, CONTEXT, docs/setup.md and docs/pipeline-protocol.md are not counted as this run's edits. Taken without user input."
  - "idea.md names the owner, a new contributor and agents that auto-load CLAUDE.md / AGENTS.md as the people with the problem; the Actors section uses those three. Taken without user input."
---

# PRD: audit the living docs until they are true, current, and organized

## Problem statement

<!-- coverage-waiver: context for the requirements below, not a deliverable; the Success criteria carry the work every breakdown row cites -->

A reader opens one of this repo's living reference docs to learn how
something works — a command to run, which module owns a fact, what a
checker is called, which skills exist, whether an ADR still stands — and
cannot trust the answer. The docs have drifted while 76 ADRs and roughly
60 fix runs landed, and nobody has ever read them as a set, so every
answer is cross-checked against the code: the doc meant to save the trip
costs the trip plus the reading. Evidence is anecdote only and labelled
so: the owner filed GitHub issue #616 on 2026-10-10 asking for stale
documentation removed, inaccurate documentation fixed, and the set
organized. No specific false claim has been cited or counted yet; that
absence is recorded as absence. This run's own findings become the hard
evidence.

## Solution

<!-- coverage-waiver: narrates the same deliverables the Success criteria check one by one; the breakdown rows cite those criteria, not this summary -->

When this ships, the thirteen living reference docs (listed under Success
criteria) say only what the tree bears out. Every claim in them that the
code can falsify — paths, commands, module names, counts, checker names,
ADR statuses, skill rosters — has been checked against the tree, with the
check recorded; what was false is corrected, what was stale is removed,
and passages that said the same thing in two docs now live in one owner
with a link from the other. Each doc has one stated job. The
reorganization is in place: no doc file is moved, renamed or deleted.
Where the truth would require changing a contract (`docs/pipeline-protocol.md`
is normative for the skills) or an out-of-scope file (an ADR body, a run
artifact), the finding is reported as a follow-up instead of edited. How
the inventory is taken and where it is recorded are the architect's calls.

## Actors

<!-- coverage-waiver: names who is involved; no actor is itself something to build -->

- **Owner** — the repo maintainer; re-reads the docs to remember what was
  decided, and merges (ADR-0033 gate 3).
- **New contributor** — someone arriving at the public repository with no
  prior knowledge, for whom the docs are the way in.
- **Loading agent** — an agent that auto-loads `CLAUDE.md` / `AGENTS.md`
  and acts on what the docs say without the instinct to doubt them.

## User stories

<!-- coverage-waiver: each story is realized through the Success criteria the breakdown rows cite, not built as separate work -->

1. As the **owner**, I want every checkable claim in the living docs to be
   true of the tree, so that I can re-read a doc to remember what was
   decided without re-deriving it from the code.
2. As the **owner**, I want each fix to carry the check that justified it,
   so that I can review the diff without redoing the audit.
3. As a **new contributor**, I want each doc to have one clear job and to
   link to the doc that owns a fact rather than restating it, so that I
   know which doc to open and never meet two versions of the same answer.
4. As a **new contributor**, I want nothing in the docs to describe a file,
   command, checker or decision that no longer exists, so that following
   the docs never leads me to something that is not there.
5. As a **loading agent**, I want `CLAUDE.md` and `AGENTS.md` to name only
   commands, modules and conventions that exist today, so that acting on
   them does not produce wrong work.
6. As the **owner**, I want any correction that would change what a skill
   must do reported rather than made, so that no behaviour change reaches
   `main` disguised as a doc edit.

## Success criteria

The in-scope set is exactly these thirteen files: `README.md`,
`CONTEXT.md`, `LEDGER.md`, `AGENTS.md`, `CLAUDE.md`, `docs/setup.md`,
`docs/pipeline-protocol.md`, `docs/output-evals.md`,
`docs/factory/doc-gardener-routine.md`,
`docs/factory/improvement-routine.md`,
`docs/factory/queue-groomer-routine.md`,
`docs/factory/retro-reflect-routine.md`, `evals/README.md`. "The base"
below means `feat/grok-harness`, the branch this run is stacked on (or
`main`, if #618 has merged and the branch was retargeted).

- [ ] **Claim inventory covers the set.** A run artifact under
  `docs/features/docs-audit/` records, for each of the thirteen files,
  every checkable claim found in it (path, command, module, function or
  checker name, count, ADR status, skill roster), each with the check run
  against the tree (the command, grep or file read), its result, and a
  verdict of true, false or stale (stale as defined in this PRD's
  assumptions). Check: all thirteen paths appear in the record; no entry
  lacks a check or a verdict; no entry's evidence is "from memory".
- [ ] **Every false or stale claim is resolved.** Each entry with a false
  or stale verdict has exactly one disposition: corrected in the diff,
  removed in the diff, or reported as a follow-up (for an out-of-scope
  file or a protocol behaviour change) with the reason. Check: walk the
  record's false/stale entries against `git diff <base>...HEAD`; none is
  left without a disposition, and every "corrected"/"removed" entry
  points at a hunk that exists.
- [ ] **The corrected docs pass their own checks.** Every check recorded
  in the inventory is re-run at Verify against the final tree, and every
  claim still present in the thirteen files passes it. Check:
  `verification.md` records the re-run and a count of claims re-checked,
  with zero failures; a failure is a failed criterion, never a reworded
  claim.
- [ ] **One job per doc.** The record states each of the thirteen files'
  job in one line, and no two lines state the same job. Every passage
  found duplicated across two in-scope docs is either collapsed to one
  owner with a relative link from the other, or kept and recorded as
  deliberate with the reader it serves (for example `CLAUDE.md`
  summarizing for agents). Check: thirteen job lines, pairwise distinct;
  every duplicate has a disposition; every "collapsed" disposition's link
  appears in the diff.
- [ ] **Links resolve.** Every relative Markdown link in the thirteen
  files points at a path that exists in the tree. Check: a stdlib-only
  scan of the thirteen files at Verify reports zero missing targets.
- [ ] **Protocol stays a contract.** Every hunk in
  `docs/pipeline-protocol.md` has an inventory entry showing the code or
  `SKILL.md` already behaves as the new text says; any finding that would
  change what a skill must do appears only as a reported follow-up, never
  as an edit. Check: read each protocol hunk against its entry.
- [ ] **In place, in scope.** `git diff --name-status <base>...HEAD`
  lists only `M` lines for in-scope files plus files under
  `docs/features/docs-audit/` (plus `factory/manifest.json` and its
  mirrored payload only if an edited file is in `factory_init.MIRRORS`;
  none of the thirteen is today) — no `A`, `D` or `R` outside the run directory. `git diff --stat
  <base>...HEAD -- docs/adr docs/fixes docs/backlog.md skills
  factory/templates 'evals' ':!evals/README.md' 'docs/features'
  ':!docs/features/docs-audit'` is empty.
- [ ] **Battery.** `python3 -m unittest discover tests` prints `OK`,
  `python3 lint.py` prints `lint: 0 problem(s)` (so the README/CONTEXT
  prose pins such as `check_readme_skills`, `check_readme_no_orphans` and
  `check_readme_figure` still hold), and `python3 gates.py && python3
  gates.py --selftest` prints `gates: 0 problem(s)` and `selftest: ok`.
  Any new or changed check is Python standard library only.

## Out of scope

<!-- coverage-waiver: exclusions: by definition nothing here is decomposed into work -->

- **ADR bodies under `docs/adr/`** — supersede, never rewrite; a docs/adr
  PR is a human gate-2 merge (ADR-0036). A stale ADR claim found in
  passing is a reported follow-up.
- **Run artifacts** under `docs/features/**` and `docs/fixes/**` (other
  than this run's own), and `docs/backlog.md` — historical records and an
  append-only inbox.
- **`skills/**/SKILL.md`** and anything under `factory/templates/**` —
  product behaviour, eval-covered and checksum-pinned.
- **Eval definitions and `evals/results/`** — append-only under eval
  honesty; only `evals/README.md` is in scope.
- **File moves, renames, or deleting a whole doc file** — reorganization
  is reordering sections, merging duplicates into one owner, and adding
  cross-links, in place.
- **Changing what a skill must do** through `docs/pipeline-protocol.md`,
  and re-litigating ADR-0076's Grok wording.
- **Judging whether a true passage is useful** — only falsifiable claims
  are audited; prose taste is not a criterion.
- **Tracker work** beyond `Closes #616` in the pull request body: no beads
  writes, no new GitHub issues.

## Open questions

<!-- coverage-waiver: questions settled downstream by Architect, Verify or the owner at merge, not requirements of this run -->

- How the claim inventory is taken (by hand, by a scratch script, or by a
  committed check) and in which run artifact it is recorded? —
  Architect; any committed check is stdlib only.
- Should any of the inventory's checks graduate into a permanent lint or
  gate so the docs cannot drift again? — Architect proposes; adding one
  is in scope only if it stays stdlib and touches no out-of-scope path,
  otherwise it becomes a backlog seed.
- Where is a reported follow-up recorded — which run artifact holds it,
  and does Operate's retro turn any into `docs/backlog.md` seeds? —
  Architect for the artifact; Operate for seeds. This run's diff never
  touches `docs/backlog.md` and opens no new issues.
- If #618 changes before it merges, does the audit re-run on the moved
  base? — Owner at merge; Verify records the base commit it checked.

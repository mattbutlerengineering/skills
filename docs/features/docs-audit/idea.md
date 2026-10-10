---
stage: idea
run: feature:docs-audit
date: 2026-10-10
origin: "GitHub issue #616 ('Audit documentation', filed 2026-10-10 by the owner; body: 'Audit documentation / Remove stale documentation / Fix inaccurate documentation / Organize documentation'). Not a docs/backlog.md seed, so no backlog line is claimed. Idea-stage answers come from the owner-confirmed autorun brief (autorun-brief.md in this directory), collected one question at a time; no live interview was held in this stage."
assumptions:
  - "The optional last30days corroboration was not run: the idea skill says never run it unasked, and the brief does not ask for it, so the brief alone is the complete interview result."
---

# Idea: audit the living docs until they are true, current, and organized

## Problem

I open a reference doc in this repo to find out how something works — a
command to run, which module owns a fact, what a checker is called, which
skills exist, whether an ADR still stands — and I cannot trust the answer.
The living docs have drifted as 76 ADRs and roughly 60 fix runs landed, and
nobody has ever read them as a set. So every answer has to be cross-checked
against the code, and the doc that was meant to save me that trip costs me
the trip plus the reading.

## Who has it

- **The owner**, who re-reads the docs to remember what was decided.
- **A new contributor**, now that the repository is public and the docs
  are the way in.
- **Agents that auto-load `CLAUDE.md` / `AGENTS.md`**, which act on what
  the docs say without the instinct to doubt them.

Today they all cope the same way: trust the ADRs and the code over the
docs, and treat the docs as a hint to be verified.

## Why now

PRD-0008 just shipped a README skill map, so the front page has had a
deliberate pass while the rest of the living docs never have. The docs
have never had a whole-set audit, and the volume of decisions and fixes
that landed since they were written keeps growing.

## Evidence

Anecdote only. The owner filed #616 on 2026-10-10 asking for stale
documentation to be removed, inaccurate documentation fixed, and the set
organized. No specific false claim is cited in the issue or the brief, and
none has been counted yet; that absence is recorded as absence, not as
evidence either way. The audit's own findings — each claim checked against
the tree, with the check recorded — become the hard evidence.

## Solution hunch

Inventory every claim the living docs make that the code can falsify —
paths, commands, module names, counts, checker names, ADR statuses, skill
rosters — check each against the tree, fix or remove what is false or
stale, and dedupe passages that say the same thing in two docs down to one
owner plus a link. In scope are the living reference docs only (root
`README.md`, `CONTEXT.md`, `LEDGER.md`, `AGENTS.md`, `CLAUDE.md`;
`docs/setup.md`, `docs/pipeline-protocol.md`, `docs/output-evals.md`;
`docs/factory/*.md`; `evals/README.md`), audited as they read on this
branch, which is stacked on the Grok-harness PR (#618). Reorganization
stays in place: no file moves, renames, or whole-file deletions. ADR
bodies, run artifacts, the backlog, `SKILL.md` files, factory templates,
and eval definitions/results are out of scope. How the inventory is taken
and recorded is for later stages.

## Success in one sentence

Every checkable claim in the living docs is true of the code today,
nothing stale remains, and each doc has one clear job.

## Unknowns & risks

- **"Stale" is a judgement call on prose.** A factual claim can be
  checked; whether a passage is still useful cannot, and the audit can
  die arguing about it.
- **Silent contract change.** `docs/pipeline-protocol.md` is normative for
  the skills; a "fix" that changes what a skill must do is a behaviour
  change smuggled in as an edit. Such corrections are reported, not made.
- **Deliberate duplication.** Some repeated passages are on purpose (e.g.
  `CLAUDE.md` summarizing for agents); collapsing them could cost the
  reader they were written for.
- **Lint pins on prose.** Checks that pin exact README / CONTEXT text will
  break when prose moves, so a reorganization can turn CI red.
- **Scope creep** into ADRs or run artifacts once a stale claim is found
  there; those become reported follow-ups, never edits.
- **Stacked base.** The branch sits on #618, which edits four in-scope
  docs; if #618 changes before merging, the audit's base moves under it.

## Work already in flight

The protocol's guard ran on 2026-10-10. `gh pr list --state open` returned
one pull request, #618 (`feat/grok-harness`, Grok as a supported harness,
ADR-0076) — the base this branch is stacked on, not a duplicate of this
work. A scan of local and remote branch names for `doc` / `audit` found
only earlier per-run documentation branches, none a whole-set docs audit.
Outcome: nothing matches. This run is seeded from GitHub issue #616, not a
backlog seed, so `docs/backlog.md` is untouched.

Next stage: PRD, via the `prd` skill or the router.

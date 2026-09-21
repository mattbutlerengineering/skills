---
stage: architect
run: maintenance:run-discovery-ignores-open-prs
date: 2026-08-25
ux: skipped — no user-facing surface; pipeline protocol and skill text
assumptions:
  - "D4's mechanical pin is read as inside the brief's prohibition on new CI gates rather than outside it, and taken anyway with the distinction stated: the brief forbids a gate that fails on EXTERNAL state — open PRs, which no checkout controls and which change under a build that has already started. A recital pin reads two files in the tree and is deterministic offline. Recorded here rather than quietly reinterpreted, because the brief is this run's only interview."
  - "The rule is written as applying wherever a project HAS a review surface, not as an optional section like the tracker mirror. A project with no review surface satisfies it vacuously — there is nothing to list — and making it opt-in would mean the one repo that needs it most could turn it off by saying nothing."
---

# Architecture: ask before starting, not after building

## Approach

The pipeline already holds this rule. `skills/work-queue/SKILL.md`
preflight says, in the skill that starts *many* work orders at once:

> Open PRs come before new work. An unfinished PR is closer to value than
> a fresh work order, and merging it first is what keeps the batch's
> branches from stacking conflicts.

It is absent from the two skills that start *one* run, and absent from
the protocol. So this is not a new rule to invent — it is a rule with one
owner and three places that need it, which is the shape this repo
recognises: state it once where facts live, recite it where agents read.

The design is therefore **protocol first, skills recite, one mechanical
pin so the recital cannot quietly rot**. No new tool, no new skill, no new
external call in any skill body. The check's *shape* is protocol; the
concrete command that performs it is packaging, exactly as the tracker
intake marker already splits (`the concrete marker — a tracker label — and
the tracker CLI live in packaging`).

It is a **guard, not a door**. The protocol's hard bound — "the mirror is
one-way out: nothing in the tracker starts a run" — is untouched, because
this rule can only ever *stop* a run from starting. Nothing here polls,
nothing here seeds, and orientation inside an active run reads run
artifacts alone as it always has.

## Components

### `docs/pipeline-protocol.md` — the rule's one owner

- Responsibility: state, once, that run discovery sees the working tree
  and that work already finished elsewhere lives on a branch behind an
  open change proposal; and that the moment a run *starts* is where that
  is checked.
- Placement: a new `### Work already in flight` subsection immediately
  after the **Run discovery** paragraph in *Runs and run directories* —
  the paragraph whose blind spot it is, so a reader meets the limit where
  the rule that has it is stated.
- Collaborators: `capture` and `idea`, which recite it; `next`, which is
  explicitly *not* a collaborator (see D3).

### `skills/capture/SKILL.md` — the maintenance entry

- Responsibility: perform the check at its two starting moments — seed
  claim (step 2) and tracker-intake seeding (step 3) — before writing
  `defect.md`.
- Collaborators: the protocol section it recites.

### `skills/idea/SKILL.md` — the spine entry

- Responsibility: the same check at its seed-claim moment (step 2).
- Collaborators: as above.

### `lint.py` `_recital` pin — the anti-rot

- Responsibility: fail loudly if either starting skill stops naming the
  rule. Nothing more: it checks that the words are there, never that an
  agent obeyed them.
- Collaborators: `check_skill_recitals`, which already owns "stage skills
  recite protocol facts" and already has a maintenance-entry hook
  (`_capture_problems`).

## Data model

None. No artifact gains a field, no frontmatter key is added, and
`protocol.py`'s tables are untouched — this rule is about the moment
before an artifact exists, so there is nothing for the orientation tables
to say about it.

## Interfaces & contracts

### The in-flight check (protocol-level, performed by an agent)

- **Input:** what this run would change — for a seed, the files and
  behaviour its text names; for an intake issue, the same from its body.
- **Output:** either nothing (proceed) or a named open change proposal
  that already does this work.
- **Failure modes, all of which must be visible rather than silent:**
  - *The review surface cannot be read* (no network, no credentials, no
    such surface). The run proceeds and records that the check could not
    run — this is the one thing the fix must not get wrong, because a
    check whose failure looks like a clean result is `maintenance:
    empty-is-not-the-same-as-broken`, shipped four hours ago.
  - *A partial match* — an open proposal touching the same files for a
    different reason. Not a stop; it is exactly the conflict-surface
    reading this run itself did to choose a seed, and it belongs in the
    brief as context.
  - *A true duplicate.* Stop and surface. The pipeline does not decide
    which of two agents' work wins; it declines to build the second one
    unattended.

### `_capture_problems` / the idea-side pin (mechanical)

- **Input:** a skill's `SKILL.md` text and its label.
- **Output:** the repo's standard label-prefixed problem strings, empty
  when the recital is present.
- **Failure modes:** deterministic and offline. It cannot consult a
  review surface, cannot fail because of network state, and cannot pass
  or fail differently in two checkouts of the same commit.

## Stack & dependencies

- **Stdlib only, no new module.** The pin extends a checker that exists.
- **No new external call anywhere in skill bodies.** The concrete command
  belongs to packaging, which is the protocol's own rule for tracker
  tooling.

## Decisions & alternatives

- **D1 — The protocol owns the rule; the skills recite it** over *writing
  it into `capture` and `idea` only*. Two copies of a rule is the defect
  this repo has written five ADRs about; and the protocol is the file a
  second harness reads.

- **D2 — Prose plus a recital pin** over *a tool that queries the review
  surface*. A tool would put a tracker CLI inside a skill body, which the
  protocol forbids by the same sentence that keeps the intake marker in
  packaging. It would also be the third owner of "list open PRs" in this
  repo. Cost, stated plainly: a prose rule is one an agent can skip, and
  the pin proves only that the words exist. That is a real weakness and
  the honest ceiling of a harness-neutral fix.

- **D3 — The check lives at the claiming stages, not in `next`** over
  *checking when the router lists seeds*. `next` offers; `capture` and
  `idea` commit. Putting the guard at the commit point means one owner
  and no false stop when a human is only browsing. The protocol already
  scopes the backlog's readers this way, so this follows an existing
  boundary rather than drawing a new one.

- **D4 — Extend `check_skill_recitals`** over *a new test in
  `tests/test_protocol_conformance.py`*. The checker already owns "skills
  recite protocol facts" and already has the maintenance-entry hook. A
  test-only pin would be a second owner of the same question, and this run
  would be creating one while claiming to fix a class of not-noticing.
  Cost: `lint.py` is claimed by open PR #324, so this buys a merge
  conflict. Measured rather than feared — #324's hunks are at lines 17,
  33–82 and 543–586, and this touches ~158–171, so the conflict is
  textual distance, not overlap.

- **D5 — Leave `work-queue`'s preflight line alone** over *folding it into
  a citation of the new protocol section*. It states an adjacent but
  different fact — merge *order*, to stop branches stacking conflicts —
  and rewriting a sentence in a skill this run has no other business in is
  the "improve adjacent code" the implementation discipline forbids. The
  new section names the relationship instead, so a later reader can see
  they are cousins rather than copies.

- **D6 — A stop, not a warning**, when a true duplicate is found. The
  weaker form ("note it and continue") is what an agent does anyway under
  momentum, and #303 shows the cost lands within a day. A stop is
  recoverable in one sentence from a human; a rebuild is not recoverable
  at all.

## ADRs

**None — no decision met the ADR bar.** The bar is all three: hard to
reverse, surprising without context, and the result of a real trade-off.
D1 and D3 follow boundaries the protocol already draws. D2 is the
protocol's existing packaging split applied once more. D4 and D5 are
reversible in one commit each. D6 is the only one with real trade-off
weight, and it is recorded in the section itself where the agent reading
it will actually meet it — which is where the architect skill says a
one-line record is enough.

Worth naming, because it is the kind of thing a later run will re-derive:
if the prose rule proves skippable in practice — a second duplicate after
this merges — that IS the evidence D2 lacks, and the tool it rejected
becomes a decision worth an ADR rather than a preference.

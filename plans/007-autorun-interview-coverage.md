# Plan 007: Make autorun's brief cover the early-stage interview inputs and make its assume-vs-stop rule decidable

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 79b08fc..HEAD -- skills/autorun/SKILL.md skills/idea/SKILL.md`
> If either file changed since this plan was written, compare the "Current
> state" excerpts against the live text before proceeding; on a mismatch,
> treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug (skill instruction)
- **Planned at**: commit `79b08fc`, 2026-07-03

## Why this matters

`autorun` promises to "drive many stages unattended" from a one-time brief. But
the brief it collects in step 1 does **not** cover several fields the very first
stage (Idea) requires, and autorun's own rule says an open question the brief
can't answer is *stop-and-surface*. So a realistic run stalls at Idea — the
promise breaks at stage one. Three smaller defects compound it: the
"choice-shaped vs open" split that decides assume-vs-stop is defined only by
example (two executors diverge on the same gap), the description claims "every
stage still produces its artifact" (false when UX is skipped), and it mislabels
three must-haves as "the idea stage's evidence." All four are instruction fixes
in one file; landing them makes unattended runs actually reach past Idea and
behave the same way twice.

## Current state

This is a **skill (markdown instruction) file**, not code. The fixes are wording
changes; there is no test suite for skill semantics — the gate is `lint.py`
(frontmatter/structure) plus a careful read-through against the Idea skill.

**Defect A — brief under-covers Idea's required inputs.** `skills/autorun/SKILL.md:26-33`
(step 1) collects: feature/product description, run scale + slug, "the must-haves
no stage can proceed without: target users, the problem, and why now", scope
boundaries, success criteria, stack/design constraints, the `ux:` decision, and
release authorization. But `skills/idea/SKILL.md:22-30` requires the interviewer
to "Cover at least" seven fields — and the brief is silent on four of them:

```
skills/idea/SKILL.md:23-30
   - What is the problem, stated from the sufferer's perspective?
   - Who exactly has it? How do they cope today?          <- brief silent on "cope today"
   - Why now — what changed to make this worth doing?
   - What evidence exists that the problem is real ...?    <- brief silent
   - What's the rough shape of a solution? (A hunch ...)   <- brief silent
   - What would make you call this a success in one sentence?
   - What are the biggest unknowns or ways this dies?      <- brief silent
```

Under the standing rule (below), "what evidence exists" is an evidentiary open
question with no skill-recommended option → stop-and-surface. So the Idea
subagent stops on the first run.

**Defect B — assume-vs-stop split is not operationally decidable.**
`skills/autorun/SKILL.md:52-55` (the subagent's standing instructions):

```
     where the brief is silent on a choice-shaped question, take the
     stage skill's recommended option and log the choice in the stage
     artifact's frontmatter under `assumptions:` ...; an
     open question the brief can't answer is stop-and-surface, never a
     guess;
```

"choice-shaped" vs "open question" is defined only by contrast, with no test to
classify a given question. `:90-91` gives a stop-side list ("irreversible
choices, spend, external commitments") but no rule for the assume side.

**Defect C — description over-claims.** `skills/autorun/SKILL.md:3` (frontmatter
description) ends: "does not skip the pipeline — every stage still produces its
artifact." This contradicts the UX-conditional skip: when `prd.md` records
`ux: not-applicable`, no `ux.md` is produced (`skills/autorun/SKILL.md:92-93`
Rules; `docs/pipeline-protocol.md` UX skip; `protocol.py` next-stage logic).

**Defect D — mislabeled parenthetical.** `skills/autorun/SKILL.md:30-32`:
"the must-haves no stage can proceed without: target users, the problem, and
why now (the idea stage's evidence)". Idea's `evidence` is a **distinct** field
("What evidence exists that the problem is real", `idea/SKILL.md:27`), not a
synonym for users/problem/why-now.

**Conventions to honor** (this skill must keep matching them):
- Vocabulary: `CONTEXT.md` — use "stage", "artifact", "run", "assumption"; avoid
  "workflow"/"phase"/"deliverable"/"step" (as pipeline synonyms). The skill
  currently conforms; keep it that way.
- Frontmatter: single-line `name:` and `description:` (see any sibling
  `skills/*/SKILL.md`); `lint.py` checks `name` matches the slug and description
  is non-empty. Do not turn the description into a block scalar.
- Section headings `## Process` / `## Rules` are the house style (all stage skills).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Lint    | `python3 lint.py` | `lint: 0 problem(s) across 13 skills`, exit 0 |
| Tests   | `python3 -m unittest discover tests` | `OK`, exit 0 (unchanged; no skill test) |

## Scope

**In scope**:
- `skills/autorun/SKILL.md` only.

**Out of scope** (do NOT touch):
- `skills/idea/SKILL.md`, `skills/prd/SKILL.md`, or any other stage skill — this
  plan aligns autorun *to* them, it does not change them.
- `docs/pipeline-protocol.md`, `protocol.py`, `CONTEXT.md`.
- Do NOT retune the description for trigger-eval performance (see STOP
  conditions) — fix only its factual over-claim.

## Git workflow

- Branch: `fix/autorun-interview-coverage` off `main`.
- Conventional Commits, e.g. `fix: autorun brief covers Idea inputs; assume/stop rule made decidable`.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1 (Defect A + D): expand the step-1 brief to cover every early-stage interview input

In `skills/autorun/SKILL.md` step 1 (`:26-33`), extend the must-have bullet so the
brief carries the full set of fields Idea (and PRD) interview for, and fix the
"evidence" mislabel. Replace the current must-have bullet:

```
   - the must-haves no stage can proceed without: target users, the
     problem, and why now (the idea stage's evidence);
```

with an enumeration aligned to `idea/SKILL.md:23-30`, e.g.:

```
   - the inputs the interview-only early stages need, since the brief is
     their only source — the Idea stage covers all of these (idea/SKILL.md):
     the problem from the sufferer's view; who has it and how they cope
     today; why now; what evidence exists the problem is real (anecdote
     counts, labelled as such); the rough shape of a solution (a hunch,
     not a design); a one-sentence success statement; and the biggest
     unknowns or ways this dies. A brief that omits one of these makes that
     stage stop-and-surface by design — so collect them up front;
```

Keep the other step-1 bullets (scale/slug, scope, stack, `ux:`, release auth)
as-is. Do not remove the release-authorization bullet or the `autorun-brief.md`
write instruction.

**Verify**: `python3 lint.py` → `lint: 0 problem(s) across 13 skills`, exit 0;
and by read: every field named in `idea/SKILL.md:23-30` now appears in autorun's
step-1 brief list.

### Step 2 (Defect B): make the assume-vs-stop boundary a rule, not an example

In the standing instructions (`:52-55`), replace the "choice-shaped … / open
question …" contrast with an operational test tied to a concrete signal — the
stage skill offering a recommended option. For example:

```
     where the brief is silent, apply this test: if the stage skill
     presents named options with a recommended default, take that default
     and log it in the stage artifact's frontmatter under `assumptions:`
     (the protocol's soft-gating convention, and the only place assumptions
     live); otherwise — any question with no skill-supplied default,
     including every evidentiary question — stop and surface, never guess;
```

Keep the existing `:90-91` "expensive to get wrong" stop list; it now reads as
examples of the stop side, consistent with the rule.

**Verify**: by read — the assume path names a testable condition ("skill presents
named options with a recommended default"); no remaining reliance on the
undefined term "choice-shaped".

### Step 3 (Defect C): correct the description's skip over-claim

In the frontmatter description (`:3`), change the tail clause. Replace:

```
does not skip the pipeline — every stage still produces its artifact.
```

with:

```
does not shortcut the pipeline — each stage either produces its artifact or records a protocol-sanctioned skip.
```

Keep the description a single line (no block scalar); keep the "it is not the
router" disambiguation clause intact. Make the same correction to the Rules
line at `:92-93` only if it now reads inconsistently (it currently says
"Conditional stages follow the protocol's skip-recording rules" — leave it if so).

**Verify**: `python3 lint.py` → exit 0 (frontmatter still single-line, `name`
still `autorun`, description non-empty).

### Step 4: full gates and commit

**Verify**: `python3 lint.py` → `lint: 0 problem(s) across 13 skills`;
`python3 -m unittest discover tests` → `OK`.

```bash
git add skills/autorun/SKILL.md
git commit -m "fix: autorun brief covers Idea inputs; assume/stop rule made decidable"
```

## Test plan

There is no unit-testable surface for skill semantics. Verification is:
- `python3 lint.py` stays green (structure/frontmatter intact), and
- a read-through checklist: (A) every `idea/SKILL.md:23-30` field appears in
  autorun step 1; (B) the assume path is gated on "skill presents a recommended
  default"; (C) the description no longer asserts every stage produces an
  artifact; (D) no parenthetical calls users/problem/why-now "the evidence".

If the operator later wants behavioral confidence, the follow-up is an output
eval for autorun (`docs/output-evals.md`) with a deliberately gappy brief,
asserting it stops at the right stage rather than guessing — out of scope here.

## Done criteria

- [ ] `python3 lint.py` exits 0 with `lint: 0 problem(s) across 13 skills`
- [ ] `python3 -m unittest discover tests` exits 0
- [ ] `grep -c "every stage still produces its artifact" skills/autorun/SKILL.md` → 0
- [ ] `grep -c "choice-shaped" skills/autorun/SKILL.md` → 0
- [ ] Read-through checklist A–D all satisfied
- [ ] `git status --short` shows only `skills/autorun/SKILL.md` modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The autorun or idea excerpts don't match the live files (drift — someone may
  have already expanded the brief; reconcile instead of duplicating).
- Aligning the brief to Idea would require *changing* what Idea asks for — it
  must not; this plan follows Idea, not the reverse.
- You find yourself wanting to rewrite the description for better trigger-eval
  routing. autorun has **no trigger-eval baseline yet** (LEDGER row is `—`);
  wording tuned for triggering is a separate, eval-driven task. Fix only the
  factual over-claim in Defect C and stop.

## Maintenance notes

- If the Idea skill's required-field list (`idea/SKILL.md:23-30`) changes, the
  autorun step-1 brief must change with it — they are now coupled by intent. A
  reviewer should diff both when either moves.
- Deferred out of this plan: an autorun output eval, and any tightening of the
  (long) description for trigger discrimination — both need a trigger/output eval
  run to judge, which costs real model runs and belongs in its own change.
- Watch that PRD's inputs don't develop the same gap: if `skills/prd/SKILL.md`
  grows required interview fields the brief doesn't carry, extend step 1 again.

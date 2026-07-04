# Plan 009: Reconcile the utility-skill definition (ADR-0023 + CONTEXT.md) with what autorun actually is

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 79b08fc..HEAD -- docs/adr/0023-utility-skills.md CONTEXT.md skills/autorun/SKILL.md protocol.py`
> If any of these changed since this plan was written, compare the "Current
> state" excerpts against the live text before proceeding; on a mismatch,
> treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (independent of plan 007, but both touch autorun's framing —
  see Maintenance notes)
- **Category**: docs (decision drift)
- **Planned at**: commit `79b08fc`, 2026-07-03

## Why this matters

The utility-skill category was written when `address-pr-review` was its only
member, and both ADR-0023 and `CONTEXT.md` define a utility skill by what it
*isn't*: it acts on surrounding work "rather than advancing a run's artifacts."
Then `autorun` joined the category — and autorun's entire job is advancing a
run's artifacts (idea → ship), one stage at a time. So the taxonomy now has a
member that contradicts its own written definition. Mechanically autorun fits
(no own artifact, no template, no soft gate, never routed to), but the prose
misleads anyone reasoning from the definition. This is a documentation-drift fix:
make the definition describe the category as it now actually is.

## Current state

Doc-only change. No code is wrong — the fix is to the *definitions* that describe
the code.

- `protocol.py` registers both skills as utility skills (the mechanical membership
  is correct — verify with `python3 -c "import protocol; print(protocol.UTILITY_SKILLS)"`
  → `['address-pr-review', 'autorun']`).
- `docs/adr/0023-utility-skills.md:6-12` defines the category by exclusion:

```
A third kind now exists: **utility skills** — skills
that act on the work surrounding the pipeline (the first is
`address-pr-review`, which works reviewer feedback on an authored PR)
rather than advancing a run's artifacts.
```

  The structural bullets that follow (`:14-29`) are accurate for autorun (no
  stage artifact, no `TEMPLATE.md`, no soft gate, not routed to). Only the
  one-line "rather than advancing a run's artifacts" framing breaks.
- `CONTEXT.md:33-40` (the `Utility skill` glossary entry) repeats the same
  framing:

```
**Utility skill**:
A directly-invocable skill acting on the work surrounding the pipeline (e.g.
address-pr-review, which works reviewer feedback on an authored PR) rather
than advancing a run's artifacts. No stage artifact, no template, never
routed to by /next; a full skill for install, lint, ledger, and trigger-eval
purposes (ADR-0023).
```
- autorun advances artifacts: `skills/autorun/SKILL.md:41` (orients via the
  protocol's next-stage rules) and `:58-64` (dispatches a subagent per stage to
  produce each stage's artifact).

**ADR conventions to honor** (`docs/adr/README.md:1-14`): an *accepted* ADR is
never rewritten — you supersede it with a new one. But ADR-0023 is **provisional**
("recommended answer adopted while awaiting confirmation — pivot freely"), so a
provisional ADR may be amended in place. This change refines a definition; it does
not reverse the decision. Recommended path: **amend ADR-0023 in place** and note
the refinement; do not renumber or supersede unless the operator prefers a new
ADR. If you do add one, follow the `NNNN-slug.md` naming and add an index row to
`docs/adr/README.md`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Lint    | `python3 lint.py` | `lint: 0 problem(s) across 13 skills`, exit 0 |
| Tests   | `python3 -m unittest discover tests` | `OK`, exit 0 (unchanged) |
| Membership | `python3 -c "import protocol; print(protocol.UTILITY_SKILLS)"` | `['address-pr-review', 'autorun']` |

## Scope

**In scope**:
- `docs/adr/0023-utility-skills.md` — broaden the definition.
- `CONTEXT.md` — the `Utility skill` glossary entry, to match.
- Optionally `docs/adr/README.md` — only if you choose to add a new ADR instead
  of amending (index row).

**Out of scope** (do NOT touch):
- `protocol.py` `UTILITY_SKILLS` — the membership is correct; do not move autorun
  out of the category.
- `skills/autorun/SKILL.md`, `skills/address-pr-review/SKILL.md` — the skills are
  fine; this fixes the *definition*, not the skills.
- Any other ADR, or the ADR status of 0023 (leave it `provisional`).

## Git workflow

- Branch: `docs/utility-skill-definition` off `main`.
- Conventional Commits, e.g. `docs: broaden utility-skill definition to fit autorun (ADR-0023)`.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Broaden the ADR-0023 definition

In `docs/adr/0023-utility-skills.md`, replace the exclusion-based framing
(`:6-12`) so the category is defined by its structural invariants (which both
members share) rather than by "not advancing artifacts" (which autorun does).
Target shape:

```
A third kind now exists: **utility skills** — directly-invoked skills that
own no stage artifact, have no soft gate, and are never routed to by /next.
They act on the work around a run: `address-pr-review` works reviewer
feedback on an authored PR; `autorun` orchestrates a full run, dispatching
a stage subagent per stage (it drives the stage artifacts into existence
without owning one itself). This extends ADR-0010's taxonomy (itself
provisional); it does not contradict it — stages and the router are untouched.
```

Keep the "What a utility skill is and is not" bullets (`:14-29`) — they already
hold for both members. Add one sentence acknowledging autorun as the
orchestrator case so a future reader isn't surprised that a utility skill
touches every stage.

**Verify**: `python3 lint.py` → exit 0 (the ADR isn't linted, but nothing else
should break); `grep -c "rather than advancing a run's artifacts" docs/adr/0023-utility-skills.md` → 0.

### Step 2: Update the CONTEXT.md glossary entry to match

In `CONTEXT.md`, change the `Utility skill` definition (`:33-40`) to the same
structural framing (directly-invoked; owns no stage artifact; no template; never
routed to by /next), and note both members, so the canonical vocabulary and the
ADR agree.

**Verify**: `grep -c "rather than advancing" CONTEXT.md` → 0; the entry names the
invariants, not the exclusion.

### Step 3: gates and commit

**Verify**: `python3 lint.py` → `lint: 0 problem(s) across 13 skills`;
`python3 -m unittest discover tests` → `OK`.

```bash
git add docs/adr/0023-utility-skills.md CONTEXT.md
git commit -m "docs: broaden utility-skill definition to fit autorun (ADR-0023)"
```

## Test plan

No test surface. Verification is `lint.py` staying green plus two greps
confirming the "rather than advancing artifacts" framing is gone from both the
ADR and CONTEXT.md, and a read-through that the new definition still excludes
stage skills and the router (the category must stay meaningful — a utility skill
is still *not* a stage skill and *not* the router).

## Done criteria

- [ ] `grep -c "rather than advancing a run's artifacts" docs/adr/0023-utility-skills.md` → 0
- [ ] `grep -c "rather than advancing" CONTEXT.md` → 0
- [ ] The ADR and CONTEXT.md both define utility skills by invariants (no artifact / no gate / not routed) and name both members
- [ ] `python3 lint.py` exits 0; `python3 -c "import protocol; print(protocol.UTILITY_SKILLS)"` unchanged
- [ ] `git status --short` shows only `docs/adr/0023-utility-skills.md` and `CONTEXT.md` (and `docs/adr/README.md` only if you added a new ADR)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- ADR-0023 is no longer `provisional` (someone accepted it) — an accepted ADR must
  be superseded with a new one, not amended; switch to the add-ADR-0025 path and
  report.
- The excerpts don't match the live docs (drift — the definition may already have
  been reworded).
- You conclude autorun should *not* be a utility skill after all — that's a
  taxonomy decision for the operator, not a doc edit; stop and surface it rather
  than moving it out of `UTILITY_SKILLS`.

## Maintenance notes

- If plan 004 (CLAUDE.md entry doc) lands, its "three skill kinds" line should use
  the same broadened definition — keep them consistent.
- The bar for future utility skills (`ADR-0023:31-34`) is unaffected; leave it.
- A reviewer should confirm the new definition still *discriminates*: a utility
  skill is directly-invoked, owns no artifact, and is never routed to — that's
  what separates it from a stage skill, and it must stay crisp for the trigger
  eval's coverage policy.

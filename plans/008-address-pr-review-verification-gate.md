# Plan 008: Make address-pr-review gate the push on green verification

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 79b08fc..HEAD -- skills/address-pr-review/SKILL.md skills/ship/SKILL.md`
> If either file changed since this plan was written, compare the "Current
> state" excerpts against the live text before proceeding; on a mismatch,
> treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug (skill instruction)
- **Planned at**: commit `79b08fc`, 2026-07-03

## Why this matters

`address-pr-review` tells the agent to run the repo's verification commands
"before pushing," but never says a **red** result blocks the push. An executor
following it literally can run tests, see them fail, and push anyway — landing a
broken commit onto a PR that a human is actively reviewing. The sibling `ship`
skill already states the gate explicitly ("Never ship on a red verification").
This adds the one missing clause so verification is a gate, not a ritual.

## Current state

Skill (markdown instruction) file; the fix is a wording change. No test suite
for skill semantics — the gate is `lint.py` plus a read-through.

`skills/address-pr-review/SKILL.md:31-35` (step 4):
```
4. **Address the actionable comments in code.** Group related asks into
   coherent commits. Run the repo's own verification commands (tests,
   lint — discover them from the repo, don't assume a stack) before
   pushing. Push to the PR branch; never force-push over history a
   reviewer has already read.
```
`skills/address-pr-review/SKILL.md:58` (Rules):
```
- Verification runs before every push, not just the last one.
```
Neither says what to do when verification is red. Contrast the pattern to match,
`skills/ship/SKILL.md:47`:
```
- Never ship on a red verification — route back instead.
```

**Conventions to honor**: house vocabulary (`CONTEXT.md`) — no
"workflow"/"phase" drift; single-line frontmatter description (`lint.py` checks
`name`==slug and non-empty description); `## Process` / `## Rules` headings.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Lint    | `python3 lint.py` | `lint: 0 problem(s) across 13 skills`, exit 0 |
| Tests   | `python3 -m unittest discover tests` | `OK`, exit 0 (unchanged) |

## Scope

**In scope**:
- `skills/address-pr-review/SKILL.md` only (step 4 and/or the Rules list).

**Out of scope** (do NOT touch):
- `skills/ship/SKILL.md` (it's the exemplar, already correct) or any other skill.
- Any Python, docs, or protocol file.

## Git workflow

- Branch: `fix/address-pr-review-verification-gate` off `main`.
- Conventional Commits, e.g. `fix: address-pr-review pushes only on green verification`.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Make the push conditional on green in step 4

In `skills/address-pr-review/SKILL.md` step 4, change the verification sentence so
the push is gated. Replace:

```
   Run the repo's own verification commands (tests,
   lint — discover them from the repo, don't assume a stack) before
   pushing. Push to the PR branch; never force-push over history a
   reviewer has already read.
```

with:

```
   Run the repo's own verification commands (tests,
   lint — discover them from the repo, don't assume a stack) before
   pushing, and push only when they pass. If verification is red, fix it
   or surface the failure — never push a red build onto a PR under review.
   Push to the PR branch; never force-push over history a reviewer has
   already read.
```

**Verify**: `python3 lint.py` → `lint: 0 problem(s) across 13 skills`, exit 0.

### Step 2: Reinforce the gate in the Rules list

In the Rules section, extend the verification rule (`:58`) so the gate is stated
where a skimming executor will see it:

```
- Verification runs before every push, not just the last one — and a red
  result blocks the push; fix or surface first.
```

**Verify**: `python3 lint.py` → exit 0; read-through confirms the gate appears in
both the step and the Rules.

### Step 3: full gates and commit

**Verify**: `python3 lint.py` → exit 0; `python3 -m unittest discover tests` → `OK`.

```bash
git add skills/address-pr-review/SKILL.md
git commit -m "fix: address-pr-review pushes only on green verification"
```

## Test plan

No unit-testable surface. Verification is `lint.py` staying green plus a
read-through: the skill now (a) pushes only on green in step 4, and (b) states
the red-blocks-push rule in the Rules list, consistent with `ship`'s phrasing.

## Done criteria

- [ ] `python3 lint.py` exits 0 with `lint: 0 problem(s) across 13 skills`
- [ ] `python3 -m unittest discover tests` exits 0
- [ ] `grep -c "push only when they pass" skills/address-pr-review/SKILL.md` → 1
- [ ] `grep -c "red result blocks the push\|red build onto a PR" skills/address-pr-review/SKILL.md` → ≥ 1
- [ ] `git status --short` shows only `skills/address-pr-review/SKILL.md` modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The step-4 or Rules excerpt doesn't match the live file (drift — the gate may
  already have been added).
- Adding the gate seems to conflict with another instruction in the skill (it
  shouldn't — report the conflict rather than resolving it silently).

## Maintenance notes

- Keep this consistent with `ship`'s verification-gate phrasing; if `ship`'s
  wording changes, consider mirroring it here.
- A reviewer should confirm the gate doesn't accidentally forbid pushing a
  work-in-progress fix that a reviewer explicitly asked to see red — the intent
  is "don't push red silently," not "never push until fully green"; the wording
  ("fix it or surface the failure") preserves the surface-then-decide path.

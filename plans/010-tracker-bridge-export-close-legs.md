# Plan 010: Carry the tracker-mirror export and close legs in the skills that own them

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat b880c9a..HEAD -- skills/decompose/SKILL.md skills/implement/SKILL.md`
> If either file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `b880c9a`, 2026-07-03
- **Issue**: https://github.com/mattbutlerengineering/skills/issues/86

## Why this matters

ADR-0026 defines the issue-tracker bridge as a one-way mirror with three
sync legs, each at a stage boundary: **import** at run seeding / Decompose
drafting, **export** at Decompose (publish work items as tracker issues,
record the mapping), and **close** at Implement item boundaries (completing a
work item closes its mirrored issue). The protocol doc carries all three
(`docs/pipeline-protocol.md:94-99`); `skills/decompose/SKILL.md` carries
only the import leg inline, and `skills/implement/SKILL.md` carries none.
An opt-in tracker run therefore imports fine but leaves published issues
unmapped and mirrored issues open after their breakdown items resolve —
exactly the tracker/breakdown drift ADR-0026 exists to prevent. This plan
makes the skills that own the export and close legs restate them as
process reminders, mirroring how decompose already restates import.

This is decision drift, not new design: ADR-0026 and `pipeline-protocol.md`
are the spec; this plan only pulls the two un-carried legs into skill text.

## Current state

Files in scope (the only files you should modify):

- `skills/decompose/SKILL.md` — the Decompose stage skill. Step 3 ("Draft
  the breakdown") ends with an inline tracker-import reminder; the export
  leg is absent. Relevant excerpts as of `b880c9a`:

  Step 3, last bullet (`skills/decompose/SKILL.md:29-33`):
  ```
     - Opt-in tracker import: when the user points at existing issues in the
       project's issue tracker (or asks to work the backlog), fold them in
       as work items carrying their issue references in the protocol's
       `(tracker: #123)` form. Imported items still need acceptance
       criteria — derive one from the issue and the PRD, or interview.
  ```

  Rules, last bullet (`skills/decompose/SKILL.md:52-53`):
  ```
  - The project's issue tracker mirrors the breakdown, never replaces it
    (ADR-0026): imported or exported, the checkboxes here remain the state.
  ```
  (Note the Rule already says "imported or exported" — the export concept is
  acknowledged here but never given a process step. This plan adds the step.)

- `skills/implement/SKILL.md` — the Implement stage skill. Step 4 ("Per
  item, test-first") ends at checking the item off; the close leg is absent.

  Step 4 (`skills/implement/SKILL.md:22-29`):
  ```
  4. **Per item, test-first:**
     - Turn the item's acceptance criterion into a failing test at the highest
       seam the codebase offers (prefer existing test seams over new ones).
     - Watch it fail for the right reason.
     - Write the minimum implementation that passes, matching the
       architecture's contracts and the codebase's existing style.
     - Refactor with the tests green.
     - Check the item off in `breakdown.md`.
  ```

Spec already on disk (do NOT modify — these are the source of truth the new
text must match, inlined here so you don't have to re-derive intent):

- `docs/pipeline-protocol.md:94-99`:
  ```
  Sync happens only at stage boundaries — import at run seeding or
  Decompose drafting (existing tracker issues become work items recording
  their originating issue references), export at Decompose (work items may
  be published as tracker issues, mapping recorded in the breakdown), close
  at Implement item boundaries (completing a work item closes its mirrored
  issue).
  ```
- `docs/adr/0026-tracker-mirror-one-way.md:16-22`:
  ```
  - **Import at run seeding** — existing tracker issues become work items in
    the breakdown artifact, each recording its originating issue reference.
  - **Export at Decompose** — the breakdown's work items may optionally be
    published as tracker issues, with the item-to-issue mapping recorded in
    the breakdown artifact.
  - **Close at Implement item boundaries** — completing a work item closes
    its mirrored issue.
  ```
- The work-item reference form the bridge already uses:
  `docs/pipeline-protocol.md:101-109` and `skills/decompose/TEMPLATE.md:17` —
  `- [ ] **<Item>** — <one line> (tracker: #123)`.

### Repo conventions to honor

- **Harness neutrality** (`docs/pipeline-protocol.md:150-155`): skill content
  must name no specific tracker CLI. The protocol's mirror section itself
  follows this — it says "the issue tracker" and "`#123` is the issue
  reference in the tracker's own notation" without naming `gh`. Match that:
  say "the tracker" / "the harness's issue tooling," never `gh` or a CLI in
  the new skill text. (The README and packaging may name tooling; the skills
  do not.)
- **Vocabulary** (`CONTEXT.md`): use "work item" (not "issue" when referring
  to a breakdown entry; "issue" is reserved for tracker items), "breakdown",
  "stage". The import bullet already uses "work items"; the new export/close
  text must too.
- **Style**: match the existing inline reminder's voice — a leading `Opt-in`
  adjective, a when/then shape, ending with how acceptance or state is
  preserved. One sub-bullet under the existing step, not a new top-level
  step, to keep the process ordering unchanged.

## Commands you will need

| Purpose    | Command                                      | Expected on success |
|------------|----------------------------------------------|---------------------|
| Lint       | `python3 lint.py`                            | `lint: 0 problem(s) across 15 skills`, exit 0 |
| Tests      | `python3 -m unittest discover tests`         | `OK` (105 tests), exit 0 |
| Export grep| `grep -n "tracker export" skills/decompose/SKILL.md` | one match (the new sub-bullet) |
| Close grep | `grep -n "mirrored issue" skills/implement/SKILL.md` | one match (the new sub-bullet) |

The Python commands are the repo's only verification surface (see
`README.md:97-98`); they cover `evalSchema`/`protocol`/lint. This plan edits
no Python — both must remain green to prove no accidental code change. The
two greps are the plan's own done gates for the new text.

## Scope

**In scope** (the only files you should modify):
- `skills/decompose/SKILL.md`
- `skills/implement/SKILL.md`

**Out of scope** (do NOT touch, even though they look related):
- `docs/pipeline-protocol.md` — already defines all three legs; the skills
  are the gap, not the spec.
- `docs/adr/0026-tracker-mirror-one-way.md` — the decision; decision docs are
  superseded with a new ADR, never rewritten.
- `skills/autorun/SKILL.md` — already carries the seeding/import-from-brief
  side (`autorun/SKILL.md:35-39`); not part of the export/close gap.
- `skills/decompose/TEMPLATE.md` — the checkbox reference form is already
  there; the export reminder belongs in the step, not the template.
- Any `.py` file (`protocol.py`, `eval_schema.py`, `lint.py`,
  `trigger_eval.py`, `orientation.py`). There is no code behavior to change;
  the mirror's close/export are skill-text conventions, not module logic.
- The routing eval set `evals/routing.json` and `evals/output/*`.

## Git workflow

- Branch: `advisor/010-tracker-bridge-legs`
- One commit, message style (conventional commits, matching `git log --oneline`):
  `docs: carry the tracker-mirror export and close legs in decompose and implement`
- Do NOT push or open a PR unless the operator instructs it.

## Steps

### Step 1: Add the export leg to Decompose

In `skills/decompose/SKILL.md`, add a new sub-bullet immediately **after**
the existing "Opt-in tracker import" bullet (the one ending at line 33), so
import comes before export in the process order. The new sub-bullet should
sit at the same indentation as the import bullet (the bullet list under
step 3's "Fill `TEMPLATE.md` (in this skill's directory):").

Target shape (match the import bullet's voice; harness-neutral — name no
CLI; use "work items" not "issues" for breakdown entries):

```
   - Opt-in tracker export: when the user wants the breakdown published to
     the project's issue tracker, create a tracker issue for each work item
     (or per milestone, where that reads better), and record the
     item-to-issue mapping on the checkbox line in the protocol's
     `(tracker: #123)` form — the same form imported items already carry.
     The breakdown remains the state; the tracker is the mirror.
```

Leave the existing import bullet and the rest of step 3 unchanged. Do not
reorder or merge the two bullets.

**Verify**: `grep -n "tracker export" skills/decompose/SKILL.md` → prints exactly one line: the new sub-bullet. Then `python3 lint.py` → `lint: 0 problem(s) across 15 skills`, exit 0.

### Step 2: Add the close leg to Implement

In `skills/implement/SKILL.md`, append one new sub-bullet to step 4's
bullet list, immediately after the existing "Check the item off in
`breakdown.md`" bullet (`skills/implement/SKILL.md:29`). Keep it at the same
indentation (the per-item sub-bullet list under step 4).

Target shape (harness-neutral; name no CLI; pair the action with its
no-op when no tracker is in play, so a non-tracker run is unaffected):

```
   - If the item carries a `(tracker: #NNN)` reference, close the mirrored
     issue in the tracker via the harness's issue tooling when you check it
     off. Items with no tracker reference close nothing — a run without a
     tracker mirror is unchanged.
```

Leave step 4's earlier bullets and everything else in the skill unchanged.

**Verify**: `grep -n "mirrored issue" skills/implement/SKILL.md` → prints exactly one line: the new sub-bullet. Then `python3 -m unittest discover tests` → `OK` (105 tests), exit 0.

### Step 3: Confirm no scope creep

**Verify**: `git status --short` → only `skills/decompose/SKILL.md` and `skills/implement/SKILL.md` are modified. If any other path appears, treat as a STOP condition.

## Test plan

No new unit tests are warranted: the stdlib modules (`protocol.py`,
`lint.py`) have no logic keyed on skill-text content, and the repo
intentionally does not assert skill prose with code (see
"Considered and rejected" in `plans/README.md` — the lint checkers cover
structure, not narrative). The verification surface for this change is:

- The two grep done-gates (the new text exists, exactly once, in each file).
- `python3 lint.py` clean (no structural break — e.g. no accidental
  frontmatter edit).
- `python3 -m unittest discover tests` green (no accidental .py edit).

A future output eval for `implement` (not in scope here — recorded as a
direction item in `plans/README.md`) is what would catch the close leg
behaviorally; this plan makes the prose correct so such an eval can target it.

Model the prose style on the existing import bullet
(`skills/decompose/SKILL.md:29-33`) and on `address-pr-review/SKILL.md:30-37`
(another skill that names tracker-thread actions in harness-neutral terms —
"Use whatever PR tooling the harness provides (for GitHub, the `gh` CLI)").
Note: `address-pr-review` does name `gh` in parenthetical; for the tracker
close, prefer the stricter harness-neutral form (no CLI name) used by the
protocol's own mirror section, since ADR-0026's bridge is tracker-agnostic.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 lint.py` prints `lint: 0 problem(s) across 15 skills`, exit 0
- [ ] `python3 -m unittest discover tests` prints `OK` (105 tests), exit 0
- [ ] `grep -n "tracker export" skills/decompose/SKILL.md` returns exactly one matching line
- [ ] `grep -n "mirrored issue" skills/implement/SKILL.md` returns exactly one matching line
- [ ] `git status --short` lists only `skills/decompose/SKILL.md` and `skills/implement/SKILL.md`
- [ ] `grep -rn "gh \|git hub\|github" skills/decompose/SKILL.md skills/implement/SKILL.md` returns no matches (harness neutrality preserved)
- [ ] `plans/README.md` status row for 010 updated

## STOP conditions

Stop and report back (do not improvise) if:

- The excerpts in "Current state" don't match the live code (the codebase
  has drifted since `b880c9a`).
- Either grep done-gate returns more or fewer than one line (the new text
  collided with an existing phrase — reword rather than duplicate).
- `lint.py` or the test suite reports a problem you didn't introduce.
- The export or close reminder seems to require naming a specific tracker
  CLI — the spec is tracker-agnostic; if it reads like it needs `gh`, the
  wording is wrong, STOP and report.
- A reviewer dispatching you asks for something beyond the two skill-text
  edits described here.

## Maintenance notes

- A future `evals/output/implement.json` (direction item, not in scope)
  should include an expectation that a work item carrying
  `(tracker: #NNN)` gets its issue closed on check-off; this prose gives
  that eval a target to assert against.
- If ADR-0026 is ever superseded to allow background sync or
  orientation-reads-tracker, the "the breakdown remains the state; the
  tracker is the mirror" framing in the new export bullet becomes wrong
  and must be revisited.
- The two new sub-bullets are the third and last place the `(tracker: #NNN)`
  form is referenced; the form itself is owned by
  `docs/pipeline-protocol.md:101-109` and `skills/decompose/TEMPLATE.md:17`.
  If that form changes, all three sites move together.
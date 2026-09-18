---
stage: review
run: maintenance:a-permission-drop-nothing-fails-on
date: 2026-08-30
assumptions:
  - "No live operator input; nothing found is blocking."
  - "Open-PR recon ran before the fix was written: six open PRs touch these workflows or their test files (#416, #373, #356, #349, #347, #333) and none of them changes a `permissions:` block. Checked by diffing each open branch against main and grepping the diff for permissions lines."
---

# Review: a permission drop nothing fails on

## Findings

### 1. A recorded table duplicates the YAML — accepted, with the reason

The table restates values that already exist in the workflow files, and
this repo treats a second copy of a fact as a defect (`one_owner.py`,
ADR-0061). Accepted here because the two copies are not the same kind of
thing: the workflow is the configuration, the table is the
specification it must satisfy, and the whole value is that they must be
changed together. A permission grant that can change in one place
quietly is the defect being fixed.

`one_owner.py` does not flag it — `EXCLUDED = ("factory/", "tests/")` —
so this is an argument for the reader, not a suppression.

### 2. Derivation was tried first — recorded, not silently dropped

defect.md carries the rejected derivation with both of its
over-approximations and the exact false failures it produced. Without
that, the next person to read this file has the same idea, builds the
same thing, and finds out the same way.

### 3. The mutant that found the run's own bug — noted

Writing the table by hand got `assembler.yml:dispatch` wrong on the first
attempt, missing `actions: write` behind a comment. The parser caught it.
That is a point in favour of the parser being content-driven rather than
another hand list, and it is why closure is asserted in both directions
rather than trusting the table to be complete.

### 4. `contents: write` is pinned as tightly as `issues: write` — deliberate

`test_every_job_holds_exactly_its_recorded_grant` compares the whole
dict, so a job that *gains* `contents: write` it does not need fails too.
That is the direction a security review cares about, and it costs nothing
extra. The trade is that any legitimate permission change now requires
touching the table — see finding 1; that is the intent.

### 5. `label_sync` appears in the derivation's writer set — no action

The rejected derivation lists `label_sync` among tracker-writing modules
(`["label", "create", ...]`). No workflow job runs it directly; it is
reached through detector L and the sweeps. Noted so a later reader does
not treat its absence from the table as an omission.

## Not found

- No change to any workflow, tool, or payload file. The diff is one new
  file under `tests/` plus this run's four artifacts.
- No mirrored file touched, so no `update-manifest` in the commit and no
  detector E interaction.
- No conflict with the six open PRs on these files: none touches a
  `permissions:` block, and this change adds a new file rather than
  editing theirs.

## Verdict

Ship.

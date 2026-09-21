---
stage: review
run: maintenance:a-command-the-stamp-cannot-run
date: 2026-08-27
assumptions: []
---

# Review: a command the stamp cannot run

## What was examined

The run's whole diff: `factory_init.py` (`_PRODUCT_TOOLS` deleted,
`product_form` rewritten, one comment clause corrected) and
`tests/test_factory_init.py` (one new class, one existing test renamed
and completed). Read alongside `product_makefile`, the root and payload
Makefiles, `TestLockstep` in `tests/test_gates.py`, and every `MIRRORS`
entry, to establish which entries the new predicate admits and which it
must not.

## Findings

### Critical

None.

### Major

**The predicate is structural, and its two clauses are load-bearing.**
`"/" not in name` excludes the six workflow entries and `.github/CODEOWNERS`
— their root spellings already carry a path, so `python3
.github/workflows/validator.yml` is not a command anyone writes and
respelling it would be meaningless. `rel != name` excludes the Makefile,
whose payload home is its own name. Both are asserted by
`test_a_file_mirrors_does_not_move_is_left_alone`, so a future MIRRORS
entry that breaks either assumption fails here rather than in a stamped
repo. Verified against every current entry: the seventeen admitted are
exactly the `tools/factory/*.py` mirrors.

**Deriving widened the respelling from seven tools to seventeen, and
that is the point rather than a side effect.** Ten of the new ten are
files no Makefile target invokes today, six of them seam modules that
never will. Respelling a command nobody writes costs nothing; failing to
respell one somebody writes breaks a stamp. The asymmetry is why the
derived direction is the safe one, and it is why the payload Makefile is
byte-identical today (verification §6).

### Minor

**`TestLockstep`'s target enumeration is still hand-typed.**
`tests/test_gates.py` names each Makefile target and its expected
commands as constants, so a target added for a new tool is compared to
nothing there at all. The new
`test_every_root_makefile_command_is_respelled_or_dropped` closes the
half that matters for the stamp — an unrespelled command — but not the
half about a target existing in one Makefile and not the other.
**Deferred**, owner: `TestLockstep` (`tests/test_gates.py`). Out of
scope here on two counts: that file is contended by open PRs #320 and
#328, and the claim belongs to the Makefile lockstep rather than to
`factory_init`'s transform.

**The respelling is still string replacement, not parsing.**
`command.replace(f"python3 {name}", ...)` would not match `python -m`
invocations or a command that reaches a tool some other way. That is
unchanged by this run and matches what the Makefile actually contains;
noting it so the next reader does not mistake the derivation for a
guarantee about arbitrary command shapes. No action.

**`test_each_factory_tool_moves_under_tools_factory` was renamed.** It
became `test_the_named_factory_tools_move_under_tools_factory` and
gained the missing `budget_guard.py`, because "each factory tool" is now
a claim the new class makes over `MIRRORS`, and two tests must not both
claim to be the complete one. A rename is a diff line in a file another
PR touches; it is confined to a line neither open PR's hunks reach
(#320's single hunk in this file is at ~line 270).

## Process findings

**ADR-0036 clause 2 is not satisfied.** A non-authoring reviewer must
re-execute the verification and record it on the pull request. This
review is self-authored, so the branch is deliberately **held out of the
merge queue** — no PR is opened, nothing is merged.

**One of the four new tests is a reproduction; three are pins.** Said
plainly in `verification.md` §4 rather than left to be inferred from a
failure count. The defect is latent — today's Makefile happens to invoke
only the seven tools the old tuple carried — so a run that claimed four
reproductions would be overstating it.

**No manifest regeneration was needed and none was made.**
`factory_init.py` is not in its own `MIRRORS`, and the generated payload
Makefile came out byte-identical.

## Fix / defer decisions

| Finding | Severity | Decision |
| --- | --- | --- |
| The predicate's two exclusion clauses | major | asserted by a test, verified against every MIRRORS entry |
| Respelling widened 7 → 17 | major | intended; byte-identical output proves it |
| `TestLockstep`'s hand-typed targets | minor | deferred — contended file, different owner |
| Replacement is string-shaped, not parsed | minor | no action, unchanged by this run |
| A test renamed in a contended file | minor | accepted; hunks do not overlap |
| ADR-0036 clause 2 unsatisfied | process | branch held out of the queue |

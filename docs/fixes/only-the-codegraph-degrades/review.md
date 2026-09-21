---
stage: review
run: maintenance:only-the-codegraph-degrades
date: 2026-08-27
assumptions: []
---

# Review: only the codegraph degrades

## What was examined

The run's whole diff: `orientation_pack.py` (one new helper, two call
sites), its payload mirror, `factory/manifest.json`, and
`tests/test_orientation_pack.py` (one new class, one new import). Read
alongside the module's only caller, `assembler.assemble_prompt`, and
`factory_init.MIRRORS` to establish where the module actually runs.

## Findings

### Critical

None.

### Major

**`_read_or_note` and `_python_structure` now both know how a failed
read degrades.** They are not the same rule — `_python_structure` must
distinguish a read failure from a parse failure, catches `SyntaxError`
too, and phrases its note "could not be parsed" because that is the
question the codegraph asks. Collapsing them would change a message an
existing test pins (`test_an_unparseable_python_file_degrades_and_does_
not_crash`) and would put the `.py` path through a helper whose contract
is "return the text", which is not what that function wants. **Kept
separate deliberately.** The near-duplication is real and worth naming:
if a third reader appears in this module, the two should be revisited
together rather than a third copy added. `one_owner.py` does not flag it
(it looks for shared constants and shared payload keys, not shared
except clauses), so this note is the only record.

### Minor

**An ADR that is cited but absent is still silently skipped.**
`adr_path` returns `None` and the loop `continue`s, so a reader cannot
tell "no ADR-0041 in this repo" from "no ADR-0041 cited". That is
existing, tested behaviour about a *missing* file, and this run is about
an *unreadable* one — a different question with a different right
answer. Untouched, and named here so the next reader of this module has
it. **Deferred**, owner: `orientation_pack.orientation_pack`'s ADR loop.

**The `is_file()` guard is now belt-and-braces.** With the read
degrading, `is_file()` no longer prevents anything the `except` would
not catch — a missing CONTEXT.md would raise `FileNotFoundError`, an
`OSError`. It is kept because it produces a *better* message: "(no
CONTEXT.md at repo root)" says the file is absent, where the generic
note would only say it could not be read. Deliberate, no action.

**The note text is not a problem string.** It goes into a prompt, not
into a checker's return, so it does not carry a `label:` prefix the way
`lint:`/`gates:`/`wq:` strings do. That matches `_python_structure`'s
existing note, which is the local convention for this module. No action.

## Process findings

**ADR-0036 clause 2 is not satisfied.** A non-authoring reviewer must
re-execute the verification and record it on the pull request. This
review is self-authored, so the branch is deliberately **held out of the
merge queue** — no PR is opened, nothing is merged.

**`factory/manifest.json` is contended by nine open PRs.** Every branch
that touches a mirrored file regenerates it, so this is structural, not
a collision with this change specifically. The resolution is the
documented one: regenerate on the branch after any rebase, never
hand-merge the hashes.

**The tests pin the defect, not the scaffolding.** All six were run RED
against `origin/main`'s `orientation_pack.py` with the new test file
already present (verification §3), and they errored rather than failed,
which is what a missing guard looks like.

## Fix / defer decisions

| Finding | Severity | Decision |
| --- | --- | --- |
| Two near-duplicate degrade rules in one module | major | kept separate, reasoning recorded |
| A cited-but-absent ADR is silently skipped | minor | deferred — different question, owner named |
| `is_file()` is now belt-and-braces | minor | kept for the better message |
| The note is not a `label:` problem string | minor | no action, matches the module |
| ADR-0036 clause 2 unsatisfied | process | branch held out of the queue |

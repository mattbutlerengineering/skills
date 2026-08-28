---
stage: review
run: maintenance:a-tenth-role-nothing-fails-on
date: 2026-08-27
assumptions: []
---

# Review: a tenth role nothing fails on

## What was examined

The run's whole diff: one new class, three tests, in
`tests/test_factory_charters.py`. Read alongside `factory_roles.py` (the
seam and its stated purpose), every existing check in the suite,
`charter_files()` and the other `ROLES`-derived helpers,
`tests/test_factory_roles.py` (which pins `assembler.CHARTER_BY_TYPE`'s
values into the vocabulary), and `factory/CHARTERS.md`.

## Findings

### Critical

None.

### Major

**The fix is a gate, not a behaviour change, and the artifacts say so.**
Nothing in production moved. That is the correct scope — the seam is
right and the ten existing checks are right; what was missing is the
assertion that closes their domain. A run that "fixed" this by adding an
on-disk enumeration to `factory_roles.py` would have added a production
function with one caller, against the repo's own bar for a shared
definition (multiple real callers *and* observed divergence). The
enumeration lives in the test, beside the partner assertions it inverts.

**The prefix check is load-bearing and easy to miss.**
`test_every_agent_stub_on_disk_is_a_chartered_role` globs `*.md`, not
`factory-*.md`, and asserts the `factory-` prefix separately. Globbing
the narrower pattern would have made a stub named `securityreviewer.md`
invisible to the very test written to find stray stubs — the same
one-directional mistake one level down. The two assertions are ordered so
the prefix failure reads first and names the file.

### Minor

**The three tests are pins, not reproductions.** They pass on
`origin/main`. `verification.md` states this in "Not verified" and
substitutes criterion 4 — drift injected in all three places, each
assertion shown to fire, the drift removed and the removal evidenced.
Worth being explicit about because the previous four runs in this series
all had a genuine red-to-green transition and this one does not.

**`INDEX_ROLES` will also match a path in prose, not only in the table.**
The regex scans the whole file for either path shape, so a role named in
a paragraph would be checked too. That is wider than "the table" as the
test name implies, and it is the safer direction — a stale mention in
prose is the same staleness — but the name promises less than the test
does. No action; noted so the next reader is not surprised.

**The index's other hand-typed role facts stay unchecked.**
`CHARTERS.md` opens with "The nine chartered roles [...] — PM, architect,
UX designer, planner, engineer (`swe`), QA, reviewer, support,
toolsmith" and later reads the pipeline off as an arrow chain. Both are
prose restatements of `ROLES` with no path in them, so neither the new
regex nor anything else compares them to the vocabulary; a tenth role
leaves the word "nine" behind. **Deferred**, owner: `CHARTERS.md`'s
index tests. Out of scope — pinning a prose count is a different kind of
assertion from pinning a path, and this run's claim is about the three
places a role is *encoded*.

**`one_owner` cannot see this diff at all.** Its `EXCLUDED` tuple skips
`tests/`, so the steady nine findings say nothing about whether these
three tests duplicate something. Recorded in the verification rather than
presented as a clean bill.

## Process findings

**ADR-0036 clause 2 is not satisfied.** A non-authoring reviewer must
re-execute the verification and record it on the pull request. This
review is self-authored, so the branch is deliberately **held out of the
merge queue** — no PR is opened, nothing is merged.

**The reproduction created files in the working tree and removed them.**
Two stray files, one stray directory, one edited index row, all injected
deliberately and all removed before commit, with `git status --short`
quoted as the evidence. `CHARTERS.md` was restored via `git checkout --`
rather than hand-edited. Called out because a run that writes into
`factory/` and then commits is exactly the accident this protocol should
make visible.

**No contended file is touched.** `tests/test_factory_charters.py`
appears in no open PR and on no other agent branch, and the diff moves no
payload byte, so there is no `factory/manifest.json` conflict to resolve
on merge — unlike the previous run.

## Fix / defer decisions

| Finding | Severity | Decision |
| --- | --- | --- |
| A gate, not a behaviour change | major | intended; production scope deliberately empty |
| The `factory-` prefix check | major | kept and asserted separately |
| Pins, not reproductions | minor | stated in "Not verified"; drift injection substituted |
| `INDEX_ROLES` is wider than the name | minor | no action; safer direction |
| Prose "nine" and the arrow chain | minor | deferred — different kind of assertion |
| `one_owner` blind to `tests/` | minor | recorded, not claimed as coverage |
| ADR-0036 clause 2 unsatisfied | process | branch held out of the queue |

---
stage: review
run: maintenance:a-program-lives-in-the-workflow
date: 2026-08-30
---

# Review — a program lives in the workflow

## What was examined

The whole diff of this run: `validator.py` (the new command),
`Makefile` and `factory/templates/Makefile` (the target), `factory_init.py`
(the product header literal and `missing_make_targets`),
`.github/workflows/validator.yml` and its payload mirror,
`skills/doctor/SKILL.md`, `factory/manifest.json`, and the two test files.
Three passes: correctness, design, security.

## Findings

### Major — 1, fixed

**`DISPATCH_ACTION`'s comment over-claimed about the action word.** It
said "every consumer branches on the PR's body, author and labels, never
on the action word", which reads as *nothing anywhere uses the action*.
`.github/workflows/validator.yml` uses `github.event.action` in six
`if:` conditions.

*Failure scenario.* A future editor reads the comment, believes the
action word is inert, and changes `DISPATCH_ACTION` to something else —
or adds a job whose `if:` depends on it and expects the synthetic file
to satisfy it. Neither works: GitHub evaluates `github.event.action`
against the REAL event, which on a `workflow_dispatch` run is a
workflow_dispatch and carries no action at all. That is exactly why
those jobs carry `github.event_name == 'workflow_dispatch'` alongside.

*Fixed.* The comment now states the narrow truth — nothing reads the
word back out of this file, and the workflow's conditions read GitHub's
event, not this one — and says why "opened" is nonetheless the right
word to write.

Confirming the first half of that claim:

```
$ grep -rn 'event\["action"\]\|event.get("action")' --include='*.py' . \
    | grep -v tests/
$ echo "exit=$?"
exit=1
```

### Minor — 2, both accepted as-is

**`main` resolves `repo_root()` before dispatching `pr-event`, which
does not need it.** Checked rather than assumed:
`knowledge_plane.repo_root` cannot raise — it walks ancestors for
`.git` and falls back to the module's own directory. So the unused
resolution costs a few `stat` calls and nothing else, and threading a
conditional through `main` to avoid them would be worse code than the
one it replaced.

**`EVENT ?= pr-event.json` can leave an untracked file at the repo root**
when someone runs `make pr-event` by hand without `EVENT=`. This is the
existing convention, not a new hazard: `FINDINGS ?= findings.txt` has the
identical property, and the repo carries no `.gitignore` at all — adding
one for this alone would be a new convention smuggled in under a bug fix.

## Observations — not findings, no change made

**The same sentence is on five more files, and this run left it alone.**
`assembler.yml`, `cost-report.yml`, `gate-digest.yml`,
`toolsmith-mine.yml`, `design.yml` and `assembler.py` all say the
workflow "names no commands of its own". Three of them do name commands
— `assembler.yml` runs a git worktree dance and `tail`, `cost-report.yml`
runs `gh variable set` inside an `if`, `gate-digest.yml` commits and
pushes.

They were read and deliberately not touched. The distinction:

- Each of those headers *continues* with its own qualifier —
  "Everything gh-shaped … goes through `make gate-digest`", "The one
  step that needs judgment goes through `make assembler`" — so a reader
  gets the real rule in the same breath. `validator.yml` said the
  unqualified "Every step goes through a `make` target" and then ran a
  program.
- None of them carries the actual hazard. The defect here is not a
  wrong sentence, it is a **contract-bearing program with three
  hand-maintained copies**. `gh` and `git` lines are plumbing, which is
  precisely what the corrected wording now permits.
- Rewriting five more mirrored workflow headers plus two test docstrings
  that quote the old phrasing is a refactor, and this repo puts refactors
  in their own change.

`design.yml`'s claim is, as it happens, simply true — its only run step
is `make web-quality`.

The cost of stopping here is a vocabulary split: `validator.yml` says
"repo tool", its five siblings say "commands". That is worth a follow-up,
and it is seeded rather than silently absorbed.

**`tests/test_gates.py:1632` and `tests/test_design_pipeline.py:5` quote
the old phrasing in their docstrings.** Same reasoning, same seed.

## Security

No new surface. `--pr` is `.isdigit()`-validated by `parse` before it
reaches the URL, so the path segment cannot carry anything else; the
value is the same one the replaced shell interpolated unvalidated into
`repos/${GITHUB_REPOSITORY}/pulls/${PR}`, so this is strictly narrower
than what it replaces. `GITHUB_REPOSITORY` comes from the runner. No
token is read, logged, or written — `gh` is invoked through the injected
seam and inherits its own environment. The payload written to
`$RUNNER_TEMP` is the PR object GitHub already served to the step that
used to build it.

One thing worth naming rather than leaving implicit: the file now
written is the same PR object as before, including the PR body, and it
lands in `$RUNNER_TEMP` exactly as it did. Nothing about the blast
radius changed.

## Fix / defer

| Finding | Severity | Decision |
| --- | --- | --- |
| `DISPATCH_ACTION` comment over-claims | major | fixed in this run |
| `repo_root()` resolved but unused for `pr-event` | minor | accepted, reasoning above |
| `EVENT` default can litter the repo root | minor | accepted, matches `FINDINGS` |
| Five sibling workflows repeat the old wording | observation | seeded, not changed |
| Two test docstrings quote the old wording | observation | seeded, not changed |

No critical findings. The battery was re-run after the major fix and is
green (`verification.md` §8).

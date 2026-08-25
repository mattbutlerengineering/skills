---
stage: review
run: maintenance:a-blind-find-is-not-a-failed-agent
date: 2026-08-25
assumptions:
  - "No live operator — this run is driven from autorun-brief.md, so every severity call and every fix/defer decision below is mine, taken against CLAUDE.md, CONTEXT.md, the cited ADRs and the run's own artifacts. A severity the operator disagrees with is a line to correct, not a design change"
  - "Depth is scaled to the blast radius defect.md records: one factory verb, one workflow condition, nothing user-facing. The verb and the condition got a full-depth pass; the ADR and the run's own documents got a lighter one"
  - "Verify's battery is the floor and was re-run here only because this review changed two files (see Finding 4). What I re-derived beyond it was chosen from verification.md's own Not verified list"
  - "Nothing was pushed and no PR was opened during review. Ship is the next stage"
---

# Review: a blind find-pr is not a failed agent

## Scope

`git diff origin/main..HEAD` — six commits (`7414c4f` through `2fd5f5c`),
12 files, +659 / −27 — plus the two files this review itself changed and
the manifest repin they forced (+16 / −12 uncommitted at the time of
writing).

What that covers, by subject:

- **The verb** — `assembler.pr_for_issue` and the `find-pr` leg of
  `main`: the new `Find` namedtuple, the three return paths, and the two
  outputs written to `$GITHUB_OUTPUT`.
- **The condition** — the six added lines in
  `.github/workflows/assembler.yml`: the comment and the third clause of
  the failure step's `if:`.
- **The suite** — `tests/test_assembler.py`, four new cases and three
  updated, including the YAML pin in `TestValidatorDispatchLockstep`.
- **The record** — `docs/adr/0063-a-terminal-verdict-requires-having-looked.md`
  (provisional) and its `docs/adr/README.md` index row.
- **The payload** — the regenerated `assembler.py` and `assembler.yml`
  twins under `factory/templates/`, and the changed lines in
  `factory/manifest.json`.

**What I re-derived rather than read.** I traced the workflow's step
graph by hand for every combination of agent outcome and find outcome
(the table under Finding 2), because the run's value depends entirely on
which of those combinations the new clause actually reaches — and
neither the breakdown nor the verification artifact had drawn it.

**Not reviewed.** The chartered agent itself, `make wo-failed` and
`make find-pr` (unchanged), the other five workflows, and the eight
one-owner findings that predate this run.

## Findings

### 1. The change may be a no-op — major, deferred

**Scenario.** GitHub does not record a step's `$GITHUB_OUTPUT` writes
when that step exits nonzero. `find-pr` writes `looked=false` and *then*
exits 1. If the write is discarded, `steps.find.outputs.looked` reads
`''`, `'' != 'false'` is true, and the flip fires exactly as it does
today: a rate-limited `gh` still marks the work order `wo:failed`.

**Why it is deferred rather than fixed.** The failure mode *is* the
status quo, so the change cannot be worse than what it replaces — it can
only fail to help. And it is not settleable offline: `write_outputs`
provably runs before `report()` in `main` (read it), and outputs from a
failed step are documented as recorded, but documentation is not an
observation. No fixture, fake or local run can produce GitHub's
expression evaluator.

**What settles it.** The first real blind `find-pr` in the factory: if
the order stays on `wo:in-progress` and the run is red, the assumption
held. Until one occurs this stays an open question, and I would rather
ship the honest version of it than a confident one.

### 2. The engagement window is narrower than the brief implies — minor, recorded

The find step carries no status-check function, so GitHub applies
`success()` implicitly. That makes the step graph:

| agent step | find step | `looked` | flip? | right? |
|---|---|---|---|---|
| failed | **skipped** | unset | yes | yes — no agent delivery to misjudge |
| succeeded, no PR | ran, exit 1 | `true` | yes | yes — an observed absence |
| succeeded, gh blind | ran, exit 1 | `false` | **no** | yes — this is the fix |
| succeeded, PR found | ran, exit 0 | `true` | n/a | job is green |

So the new clause engages in exactly one row. `defect.md` reads as
though any blind `gh` could mis-blame an agent; in fact a blind `gh`
during a *failed* agent run never reaches the find step at all.

This is not a defect — the narrower behaviour is the correct one — but
it makes the `!=` rather than `==` choice load-bearing rather than
defensive: row one depends on an unset output still flipping, and an
`== 'true'` condition would have silently stopped marking failed agents
failed. The workflow comment says this; the ADR says this; I am
recording that I checked it against the real step graph rather than
against the comment.

### 3. `Find.problems` aliases the seam's list — minor, pre-existing, not fixed

On the read-failure path `pr_for_issue` returns `Find(None, False,
read.problems)` — the caller receives the list `cli.GhResult` owns, not a
copy, where the other two paths return `list(read.problems)` plus
appends. No current caller mutates it, and the pre-existing code did the
same thing before this run touched it. Flagged, not fixed: this is
adjacent code, and CLAUDE.md's surgical-scope rule puts a cleanup of the
seam's return convention in its own change.

### 4. I desynced the payload mirror during this review — minor, fixed in-run

Fixing the two text findings below meant editing `assembler.py`, a file
in `factory_init.MIRRORS`, *after* I4 had already run
`update-manifest`. The suite caught it immediately:

```
FAIL: test_every_mirrored_root_file_matches_its_payload_copy
      (mirror='assembler.py')
```

Re-running `python3 -B factory_init.py update-manifest` restored it and
the suite went green. Recorded because it **corrects a note in the
previous run's `release.md`**: that run logged an "intermittent
single-test failure" whose identity was lost to tail-truncated output
twice, with stale bytecode as the leading hypothesis. This occurrence is
neither intermittent nor bytecode — it is deterministic, and the cause
is editing a mirrored root file after pinning. Whether it explains the
earlier two is unproven (those reportedly cleared on re-run without a
regeneration, which a stale mirror would not do), so this does not close
that question; it removes one guess and adds a confirmed cause. The
lesson that generalises: **capture full suite output to a file**, which
is what turned a three-run mystery into a one-line diagnosis.

### Text findings, both fixed in-run

- `pr_for_issue`'s docstring opened mid-phrase (`…whether\n this run got
  to look, problems). The\n join is…`) because I inserted the new clause
  and left the old wrap. Rewrapped.
- `TestFindPrVerb`'s class docstring still described a verb that writes
  one output. It now writes two, and the second is the one ADR-0063
  turns on. Rewritten to describe both and to say that both must be
  written even when the verb exits nonzero.

### Considered and rejected as findings

- **"A skipped find step flips an order nobody looked at, contradicting
  ADR-0063's own principle."** It does flip, but the principle is about
  *the agent's delivery*: row one of the table above is a run that died
  before dispatch could produce anything to observe, so there is no
  absence being wrongly attributed. The ADR states this carve-out
  explicitly.
- **"The suppressed flip strands the order on `wo:in-progress`."** True,
  and it is the trade the ADR names rather than a defect it missed. I
  confirmed the bound: `READY_LABEL` is `wo:ready-for-agent` in all three
  of `assembler.py`, `work_queue.py` and `validator.py`, so a stranded
  order is never re-dispatched to a second agent, and no reaper exists to
  act on it. A stuck order is loud in the gate digest and recoverable by
  hand; a false `wo:failed` is silent and terminal.

## Design

The change matches `architecture.md`'s contract exactly: a named fact the
caller reads rather than a condition it infers. It is the same shape as
`cli.GhResult.truncated` and as `gate_digest.Item.aged` from the previous
run — three modules now, one convention. The trap it removes is the one
CLAUDE.md's seam rule exists for: `pr is None` was true in three
situations that mean three different things, and the workflow branched on
it as though it meant one.

No deviation from the architecture. No new shared module (the convention
travels as a pattern, which is correct — `factory_init.MIRRORS` and the
seam rule both require observed divergence before extraction, and there
is none).

## Security

No secrets in the diff. `$GITHUB_OUTPUT` takes only `str(int)` and the
literals `"true"`/`"false"` — no listing-derived text reaches it, so the
output-injection surface is unchanged and empty. `issue_number` is
`int()`-cast behind an `isdigit()` guard in `main`. `gh` arguments remain
a fixed list, never a shell string. The failure step's added clause reads
a step output, which GitHub does not interpolate into the shell.

## Verdict

Ship. One major finding, deferred with its settling condition named; four
minors, three fixed in-run and one flagged as pre-existing. Battery green
after the review's own edits: 1348 tests OK, `lint: 0 problem(s) across
24 skills`, `gates: 0 problem(s)`, `selftest: ok`, `one-owner: 9
problem(s)` (baseline, unchanged).

---
stage: architect
run: feature:decompose-lessons
date: 2026-10-20
ux: skipped — CLI text output and skill text only; no screens or flows.
assumptions:
  - "No live interview: every PRD open question was settled from autorun-brief.md, idea.md, prd.md, the code and read-only measurements on this clone, taking the recommended default each time. ADR-0113 (provisional) is written because the file's on-disk shape and the pinned import edges outlive the commit; every other choice changes in one commit."
  - "Measured 2026-10-20 with `python3 decompose_signals.py` on this clone (37 runs, 0 problems; refs include PR heads if fetched). Per-signal hit runs: re-plan 3 (feature:decompose-outcome-signals observed 2/13, feature:first-live-dispatch inferred 4/8, maintenance:a-timestamp-the-digest-cannot-parse inferred 6/7); design gaps 2 (decompose-outcome-signals, pr-body-preflight; both observed); review-traced 13 of 36. Contrast pairs under the rule below: re-plan 26, design gap 4, review 145 (every one of the 13 review hits has at least 10 clean runs of its kind). Pairs exist today, but they come from only 3 + 2 + 13 hit runs, and the 145 review pairs are low-selectivity: 13 of 36 runs hit, so review is a weak contrast. Expected lessons if run today: 5 (replan/feature/added, replan/maintenance/dropped, design_gaps/feature/routed, review/feature/named, review/maintenance/named). No number here is estimated."
  - "Recommended default taken (a run of the same kind, PRD open question 1): a clean run for a hit run H on a signal is a measured run of the same kind (the run-ref prefix: feature, maintenance, product) whose count on that signal is 0 and whose signal label (observed or inferred) equals H's. Kind is the run-ref's own scale, so no new notion of kind is invented. The same label is required because an inferred zero is weaker evidence than an observed one. Of the clean runs, the exemplar is the first in run-path order, deterministic and arbitrary; the lesson text names only that one so a source list stays short. Alternatives measured: same kind only gives re-plan 43 pairs, all runs 81; same kind and observed only gives re-plan 3 pairs, which would leave maintenance re-plan with none."
  - "Recommended default taken (lesson identity and text, PRD open questions on format): id is `<signal>/<kind>/<detail>`, the detail the signal's own typed field (re-plan: the largest of added, dropped, split, merged, ties in that order; design gaps: routed; review-traced: named). One lesson per id. The text is a fixed template over the pair's numbers only, a description of the contrast and never advice: e.g. `feature runs that re-planned mostly by adding rows: first-live-dispatch 4 of 8 items (inferred), launch-demo 0 of 14 (inferred)`. No tool path takes text from a person or a model, so the brief's no-hand-written-lesson rule holds by construction; EDIT exists as an operation used by `update`, not as a command."
  - "Recommended default taken (where, format): `docs/factory/decompose-lessons.jsonl`, beside costs.jsonl. JSONL over markdown because detectors C and I scan every markdown, fences included. Line 1 is `{\"seen\": [...]}`; each other line one lesson `{\"id\", \"importance\", \"text\", \"sources\", \"voted\"}` sorted by id. One lesson per line as the brief requires; the header is not a lesson. Recorded in ADR-0113."
  - "Recommended default taken (votes, PRD criterion step size): UPVOTE adds 1 and DOWNVOTE subtracts 1; a new lesson starts at 2; at 0 the line is removed. ExpeL's convention; the PRD asked Architect to confirm. A vote comes from a voter run: a run not yet in `seen`, of the lesson's kind, whose decompose boundary is observed, whose signal is measurable, and which is treated (its decompose commit descends from the commit that first added the lessons file, so its draft could have read it). A voter that hit the lesson's signal DOWNVOTEs (the lesson did not prevent the failure); a voter that was clean UPVOTEs. Each voter votes once per lesson, recorded in `voted`. This is ExpeL's rule (upvote a lesson that coincides with success, downvote one that coincides with failure), not a causal claim."
  - "Recommended default taken (who runs the update): the Owner, by `python3 decompose_lessons.py update`, a root-only maintenance command outside every stage, gate and workflow. No pipeline stage runs it: the stamped repo has no tool, and a stage that writes the file would put the Owner's review gate behind an unattended write. The write is a normal diff in a PR the Owner reads. Dropped lessons cannot return from the same runs: `seen` holds every run already folded in, and a new lesson is derived only from a hit run not in `seen`."
  - "Recommended default taken (root-only, PRD open question): root-only. No payload tool imports it. New root-only to mirrored pairs: decompose_lessons to cli and to factory_config (the floor, `resolve_calibrate_floor`). `decompose_signals` is root-only and crosses no mirror. The set moves 50 to 52; the pin and a `factory.py` VERBS row (`decompose-lessons`) are Implement's, and ADR-0113 records the edges. No seam module is added: the tool has exactly one caller of `decompose_signals.measure` for pair derivation and nothing diverged, so CLAUDE.md's seam rule is not met."
  - "Recommended default taken (how Decompose reads it, PRD open question): skill text only. A new step in skills/decompose/SKILL.md reads the target repo's `docs/factory/decompose-lessons.jsonl` if present and treats each line as a hypothesis about past outcomes, ordered by importance, never as a rule and never as a reason to drop an acceptance criterion; absent or empty means draft as before. The skill never runs the tool and never writes the file, so it works in a stamped repo that has neither. This is a skill change: it rides the wave's release PR (ADR-0095) and this branch does not touch .claude-plugin/plugin.json. Known gap: until that release is installed, runs drafted from the old cached skill never read the file though they count as treated; the comparison below therefore overstates exposure early, and Operate cross-checks the release date."
  - "Recommended default taken (measurement against the re-plan rate, PRD open question): `python3 decompose_lessons.py` (no argument, read-only) prints re-plan rate for treated runs against untreated runs, restricted to observed-label runs, with numerator and denominator taken only from `decompose_signals.measure`. Treated is fixed by git ancestry from the commit that first added the lessons file, not by anything the lessons tool writes. Unmeasurable runs are counted and named, never zero. The tool prints a rate comparison only when treated observed runs meet `factory_config.resolve_calibrate_floor` (5, the same floor #1047 and Conductor use); below it, `no verdict: <r> treated run(s) is below the minimum of <floor>`. Even above the floor the line is descriptive (`treated higher | not higher`), with no significance claim. Measured baseline today: observed re-plan 2/52 over 5 runs, combined 12/260 over 30 runs (4.6%), i.e. one re-plan of two rows in a 10-row run moves the rate about 4 points, so this measure cannot reliably detect harm at present volume. That is stated in the output, not hidden."
  - "Recommended default taken (not surfaced): nothing here is expensive to reverse without an ADR, and every choice has a stated default, so nothing is surfaced. The one residual judgement a human may want is whether to keep review-traced as a source at all (low selectivity, 13 of 36); the brief makes the three signals binding, so it stays."
---

# Architecture: A ranked lessons file for Decompose

## Approach

One root-only, stdlib module, `decompose_lessons.py`, with a pure core and
two thin adapters (git through `cli.runner`, the lessons file through
`cli.read_file` and one atomic write). It takes the run records
`decompose_signals.measure` already returns, derives contrast pairs of a
hit run and a clean run of the same kind, collapses pairs to lessons by id,
and keeps them in `docs/factory/decompose-lessons.jsonl`. `update` is the
single writer: it votes existing lessons with new treated runs, then adds
or edits lessons from new hit runs, then drops any lesson at 0. The
no-argument command is read-only and prints the pair count, the lessons,
and the treated-versus-untreated re-plan comparison. The Decompose skill
reads the file as plain text at draft time.

The other shape compared was a ranked-lessons file written by the Owner or
by a model summarising retro notes, with the tool only voting. It loses
because it lets a lesson in whose text no record backs, which is the failure
ExpeL measured (29% from raw reflections against 39%), and the brief rules
retro prose out.

| PRD success criterion | Where |
|---|---|
| ADD refused with no source, file byte-identical | Lesson operations |
| ADD at importance 2 with sources | Lesson operations, File |
| UPVOTE +1, DOWNVOTE -1, sources intact | Lesson operations |
| At 0 the line is removed; at 1 it remains | Lesson operations |
| Vote/EDIT on an unknown lesson refused | Lesson operations |
| EDIT keeps importance and sources; refused if it leaves none | Lesson operations |
| Only re-plan, design-gap, review pairs; no band miss, no retro prose | Pair derivation |
| No pair leaves the file empty or absent, string printed | Report, update |
| Decompose skill reads the file, absent/empty case | Skill step |
| Figures computed from records, no seeded lesson | Pair derivation, File |
| Stdlib, no network; plugin.json unchanged | Stack |
| Five repo checks pass | ADR-0113, VERBS row, pin |

## Components

### Pair derivation (`pairs`)

- Responsibility: from the RunRecords, per signal in {re-plan, design gaps,
  review-traced}, each measurable hit run H (count above 0) paired with the
  first clean run in run-path order of H's kind and H's label. Returns
  `{signal, kind, detail, hit, clean, text}`. A hit run with no clean run of
  its kind and label yields no pair. Unmeasurable runs never become hit or
  clean. Only these three signals exist in this module; there is no
  band-miss or text input to reach it.
- Collaborators: `decompose_signals` (records as given). Pure.

### Lesson operations (`add`, `edit`, `upvote`, `downvote`)

- Responsibility: pure functions over a list of lessons, each returning
  `(new_list, problems)`. They own the invariants: a lesson has at least one
  source run; importance starts at 2; a vote moves it by 1; it is removed at
  0 and never stored below 1; EDIT keeps importance, sources and voted; an
  unknown id is a problem and creates nothing.
- Collaborators: none. Pure; the list is never mutated in place.

### Voting (`votes`)

- Responsibility: for each lesson and each voter run (see Data model),
  decide UPVOTE or DOWNVOTE from the lesson's signal on that run, skipping
  a run already in the lesson's `voted`. `treated` is computed here from
  one git fact per file: the commit that first added the lessons file, and
  whether it is an ancestor of the run's decompose boundary commit
  (`git merge-base --is-ancestor`).
- Collaborators: Lesson operations, the injected git runner.

### File (`load`, `dump`)

- Responsibility: parse and write the JSONL file. A malformed line, a
  lesson without sources, a duplicate id or an importance below 1 is a
  problem and nothing is written. The write is one whole-file replace
  (temp file then `os.replace`).
- Collaborators: `cli.read_file`.

### Comparison (`compare`)

- Responsibility: pool re-plan (sum of `count` over sum of `items_at_d`)
  over observed-label measurable runs split into treated and untreated;
  name the unmeasurable ones; refuse a verdict below the floor.
- Collaborators: `factory_config.resolve_calibrate_floor`. Pure over
  records and the treated set.

### Report and front door (`render`, `main`)

- Responsibility: load config and file, run measure, print through
  `cli.report`, own exit codes, perform `update`'s write. A `factory.py`
  VERBS row `decompose-lessons` is required by `tests/test_factory_cli.py`.
- Collaborators: everything above, `decompose_signals.measure`, `cli`.

### Skill step (`skills/decompose/SKILL.md`)

- Responsibility: one step between the soft gate and the draft that reads
  the file and states the absent-or-empty case. Skill text only.
- Collaborators: none; it never runs the tool.

## Data model

Access patterns: (1) Decompose reads the whole file once per draft; (2)
`update` reads it, folds new runs in, and rewrites it whole; (3) the report
reads it and the records. Consistency: single writer (the Owner running
`update`), so a whole-file replace is enough; a concurrent update is the
Owner's merge conflict on a small sorted file.

```
{"seen": ["feature:a", "maintenance:b", ...]}           # line 1, sorted
{"id": "replan/feature/added", "importance": 2,
 "text": "feature runs that re-planned mostly by adding rows: ...",
 "sources": ["feature:first-live-dispatch", "feature:launch-demo"],
 "voted": []}                                            # one per lesson, sorted by id

Pair   {signal, kind, detail, hit, clean, text}
Voter  a run not in `seen`, of the lesson's kind, decompose label observed,
       signal measurable, and treated
Treated  the commit first adding the file is an ancestor of the run's
         decompose boundary commit
```

Invariants and owners: run records and labels belong to `decompose_signals`;
the floor belongs to `factory_config`; importance, source and removal rules
belong to Lesson operations; `seen` belongs to File and is what stops a
dropped lesson being re-derived.

## Interfaces & contracts

### `python3 decompose_lessons.py` (also `python3 factory.py decompose-lessons`)

- Input: git history read-only through `decompose_signals.measure`, the
  lessons file if present, `factory.json`. No arguments; no network.
- Output, stdout, in this order. Implement pins the exact strings:
  - `decompose-lessons: <p> contrast pair(s) from <h> hit run(s): re-plan <a>, design gaps <b>, review-traced <c>`
  - when none: `decompose-lessons: no contrast pair found — no lesson derived`
  - one line per lesson: `decompose-lessons: <id> importance <n> — <text> (sources: <runs>)`
  - the comparison, `decompose-lessons: re-plan treated <c>/<i> over <r> run(s), untreated <c>/<i> over <r> run(s) (observed only; <u> unmeasurable); descriptive, treated higher|not higher`
    or `decompose-lessons: no verdict: <r> treated run(s) is below the minimum of <floor>`
  - the `cli.report` summary line.
- Exit: 0 with no problems (an empty pair set and a refused verdict are
  data); 1 with problems; 2 on any unknown argument, usage printed.

### `python3 decompose_lessons.py update`

- Input: as above, plus a clean worktree for the lessons file's directory.
- Output: one line per ADD, EDIT, UPVOTE, DOWNVOTE and drop, with the lesson
  id; then `decompose-lessons: wrote <path>` or, when nothing changed,
  `decompose-lessons: unchanged`. No pair and no file: nothing is written.
- Failure modes: `measure` returning no result (git absent or timed out at
  `GIT_TIMEOUT`, retry safe: every call is local and read-only) prints its
  problems and writes nothing; a malformed existing file prints the line
  number and writes nothing; a lesson op problem is printed and the whole
  update is abandoned, file byte-identical.

### Lesson operations

- Input: a lesson list and the operation's arguments. Output: a new list
  and `[]`, or the original list and one problem string, e.g.
  `decompose-lessons: add refused: <id> cites no source run`,
  `decompose-lessons: <op> refused: no lesson <id>`. Never mutates, never
  raises on a bad id.

### Skill step

- Reads `docs/factory/decompose-lessons.jsonl` in the target repo. Absent or
  holding only the `seen` line: draft unchanged, no message. Malformed: say
  so once and draft unchanged. A lesson is a hypothesis about past
  outcomes ordered by importance, never a rule and never a reason to relax an
  `Accept:` line.

## Stack & dependencies

- Python 3 stdlib only (`json`, `os`, `pathlib`, `subprocess` via `cli`).
- Imports `cli`, `factory_config` (mirrored) and `decompose_signals`
  (root-only). Two new root-only to mirrored pairs and one pin edit, in
  ADR-0113. No `factory_init.MIRRORS` entry, no manifest regen.
- Docs touched: a CLAUDE.md "on demand, free" bullet beside
  `decompose_signals.py`, and a CONTEXT.md entry, **Decompose lesson**. No
  Makefile or CI line: a measurement and a maintenance command, not a gate.
- Wave release: the skill change needs the wave's `chore(release)` PR
  (ADR-0095); this branch leaves plugin.json alone.
- Tests: through the public interface with a fixture record list and an
  injected git runner: each PRD criterion by exact string, a fixture with a
  band miss and a retro note that reaches no lesson, a dropped lesson that
  does not return on the next update, a voter that predates the file that
  does not vote, the floor refusal, and pair derivation worked by hand.

## Decisions & alternatives

- **Same kind and same label for a clean run** over any run, or observed
  only: any run gives re-plan 81 pairs but mixes kinds with different
  re-plan norms; observed only gives 3 re-plan pairs and no maintenance.
- **Derived, descriptive text** over advice text: advice written in the tool
  is a hand-written lesson by another route; a description of the contrast
  carries no claim the records do not back.
- **JSONL under docs/factory** over markdown or a docs/ page: detectors C and
  I scan all markdown (ADR-0113).
- **`seen` header** over deriving only from the current pairs: without it a
  lesson dropped at 0 returns on the next update from the same runs, and
  the file would never forget.
- **Voters must be treated** over any new run: a run whose draft could not
  have read the file says nothing about the file.
- **Owner-run `update`** over a stage step or a workflow: no unattended
  writer to a file the next draft reads.
- **No new shared module** over extracting the run-kind or label logic:
  one caller of `measure`, no observed divergence (CLAUDE.md seam rule).
- **Descriptive comparison, floor from `factory_config`** over a
  significance test: at 5 observed runs and 52 rows a test is theatre.
- **Skill reads, never runs** over a skill that calls the tool: the tool is
  root-only and a stamped repo has none.

## ADRs

- ADR-0113 (provisional): the lessons file's JSONL shape and its `seen`
  header, the single derived writer, and decompose_lessons joining the
  root-only importers of cli.py and factory_config.py. The other
  decisions fail the hard-to-reverse leg: one commit changes them.

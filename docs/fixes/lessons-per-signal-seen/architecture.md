---
stage: architect
run: maintenance:lessons-per-signal-seen
date: 2026-10-23
assumptions:
  - "prd.md is absent by protocol: this is a maintenance run with re-entry: architect, whose predecessor is defect.md (pipeline-protocol.md, Maintenance-run orientation). No ux: echo for the same reason; defect.md states no user-facing surface beyond CLI lines."
  - "No live interview. Every open question defect.md and autorun-brief.md left to Architect is settled from the code and from read-only measurements on this clone, taking the recommended default each time. Not an Owner answer."
  - "Header key stays `seen` (the skill's wording and its pinned phrase keep holding); only the entry form changes to `<signal>:<run ref>`. Alternative, a new key, loses on the skill text and on a skill release that nothing reads the header to need."
  - "Migration: `load` refuses the old per-run shape and does not upgrade it. Default taken because the cheaper honest option is the one that cannot guess: any mapping of an old entry to signals either reproduces the review loss (all three) or re-derives dropped review lessons (two). `git ls-tree -r --name-only origin/main | grep lessons.jsonl` prints nothing, so no real file exists to migrate; the owner's recovery is to delete the file and run update."
  - "Size bound: MAX_LESSONS_BYTES = 1024 * 1024 (1 MiB), not 4 MiB. Measured 2026-10-23: `python3 decompose_signals.py`'s measure over this clone gives 41 runs, an old header of 1,430 bytes and a new one of 5,336 bytes with all three signals measured for every run; defect.md measured a worst-case lesson line at 838 bytes and a realistic 5-lesson file at about 1.1 KB, so a file today is about 6.5 KB. 1 MiB is about 160x that and about 2.7x a deliberately extreme ledger of 300 worst-case lessons (250 KB) plus 1,000 runs (about 130 KB header). The Decompose skill reads the file whole into a draft, so 4 MiB (the eval_trends bound, set for single JSON records) would admit a file the skill could not usefully read."
  - "Zero-item wording is a third and fourth tail, not a refusal: a zero-item pool is data, the line stays exit 0. Wording chosen to name which pool has no rate, so the untreated 5/40-against-0/0 case no longer reads as a comparison."
  - "The ADR number 0116 was re-checked 2026-10-23: `git ls-tree --name-only origin/main docs/adr/` ends at 0115 after a fetch and `gh pr list --state open` is empty."
---

# Architecture: a lessons ledger that keeps a signal that matures later

## Approach

`seen` becomes a set of `(signal, run)` pairs, written on line 1 as
`<signal>:<run ref>` strings. A run is seen for a signal exactly when the
signal was measured for it in the fold, whatever its count; a run
unmeasurable for a signal is not seen for it, and so can still produce or
vote on that signal's lessons once it matures. Everything else stays: the
header key, the lesson lines, vote order, early exposure, the derived-only
rule. Two small honesty fixes ride along (a zero-item pool no longer prints
"not higher", and `load` refuses a file above a named size). The shape is
one module and its tests; the one decision that outlives the commit is the
on-disk header form, so it gets ADR-0116 superseding ADR-0113's header
decision in part.

Two shapes were compared. (a) Keep the per-run key and fold a run only once
all three signals are measured: it needs no format change, but a run that
never gets a review (a maintenance run closed without `review.md`) would
never enter `seen`, and a lesson dropped at 0 would be re-derived from it
on every update. Review pinned that path in ba31d36. (b) The per-signal key:
a larger header (about 3.7x measured) and one more concept, but each
signal's maturity date is independent and nothing is re-derived. (b) wins.

## Components

### Seen key (`seen_key`, new, in `decompose_lessons.py`)

- Responsibility: the one function that builds and the one regex that
  validates a header entry, `<signal>:<run ref>`, over the signal names
  `decompose_signals.SIGNALS` carries (`replan`, `design_gaps`, `review`).
  The entry splits on its first `:`; the signal names contain no `:` and
  none is a run kind, which is why an old per-run entry (`feature:c`,
  `product`) can never parse as a new one.
- Collaborators: Pair derivation, Voting, File, Fold.

### Pair derivation (`pairs`)

- Responsibility: unchanged except the skip. `skip` is now a collection of
  seen keys; a hit run is skipped when `seen_key(signal, hit run)` is in it.
  The clean partner is never consulted against `skip`.
- Collaborators: Seen key.

### Voting (`votes`, `_ballot`)

- Responsibility: a ballot is refused when `seen_key(lesson signal, run)` is
  in `seen`, not when the run is. The prefilter keeps a run only if it has
  at least one lesson signal it is unseen for, so a run seen for every
  signal its kind's lessons use costs no git call (the cost the old
  `rec["run"] not in seen` prefilter saved).
- Collaborators: Seen key.

### File (`load`, `serialize`, `dump`, `_parse`)

- Responsibility: `_parse` validates each header entry (below);
  `serialize` writes `sorted(set(seen))`; `dump`'s `not (lessons or seen)`
  guard is unchanged; `load` refuses an oversize file before reading it.
- Collaborators: `cli.read_file` (the guarded read, unchanged).

### Fold (`fold`)

- Responsibility: the returned `seen` is the input plus the key of every
  `(signal, run)` the records measure (`_hit_label(rec[signal], num)` is not
  None). That one rule subsumes the three old ones (every complete run,
  every hit run, every voter): a hit run and a voter are measured for their
  signal by construction, and a run with an implement boundary is measured
  for re-plan and design gaps unless the signal itself is unmeasurable.
- Collaborators: Pairs, Voting, Seen key.

### Comparison (`compare`)

- Responsibility: the verdict tail, now with a no-comparison form for a
  pool with no rate (Interfaces).

## Data model

Access patterns are ADR-0113's (Decompose reads the file whole; `update`
reads, folds and rewrites it whole; one writer). Only line 1 changes.

```
{"seen": ["design_gaps:feature:a", "replan:feature:a", "review:feature:a",
          "replan:product", ...]}                        # line 1, sorted
{"id": ..., "importance": ..., "text": ..., "sources": [...], "voted": []}   # unchanged
```

Entry grammar: `(replan|design_gaps|review):<REF>` with `REF` the module's
existing run-ref pattern (`feature:<name>`, `maintenance:<name>`,
`product`).

What "complete" means per signal, i.e. when the fold adds the key:

| signal | measured (key added) | not measured (key not added) |
|---|---|---|
| `replan` | the run's re-plan value has no `unmeasurable` and carries a label and an integer `count` | no decompose/implement boundary, a repeated work-item key, a read failure |
| `design_gaps` | the value has no `unmeasurable` and carries a label and an integer `routes` | no `Design gaps found` section yet, no boundary |
| `review` | the value has no `unmeasurable` and carries a label and an integer `named` | no `review.md` yet, or one whose finding heading is absent (`{findings: 0, reason}`) |

Invariants and owners: run records and labels belong to `decompose_signals`;
the entry grammar and the "measured" test (`_hit_label`) belong to
`decompose_lessons` (File and Fold share the one `seen_key`); importance,
source and removal rules belong to Lesson operations. A lesson dropped at 0
cannot return from a run seen for its signal; a run unmeasured for the
signal cannot have contributed to it, so it is not a source of the dropped
lesson.

## Interfaces & contracts

### `load(path, shown)` and the header

- Input: the file text. Output: `(lessons, seen, problems)`, `seen` a list of
  validated keys.
- Failure modes (all label-prefixed, first problem only, nothing else
  returned, exit 1 through `report`):
  - non-list or non-string header: unchanged,
    `decompose-lessons: <shown> line 1: expected the seen header`.
  - an old per-run entry (it fullmatches the run-ref pattern):
    `decompose-lessons: <shown> line 1: seen entry '<entry>' is the old per-run shape (ADR-0116); delete the file and run update to rebuild it`
  - any other string that is not `<signal>:<run ref>`:
    `decompose-lessons: <shown> line 1: seen entry '<entry first 60 characters>' is not <signal>:<run ref>`
  - a file above the bound, checked by `stat` before the read:
    `decompose-lessons: <shown> is <size> bytes, above the 1048576-byte bound; not read`
    (the `eval_trends` wording; a missing file or a `stat` error is left to
    `cli.read_file`, as there). Exit 1.
- A refusal is not a migration: nothing is rewritten, so the Owner's
  recovery is to delete the file and run `update`, which loses importances
  and votes (none exist on `main`). `update` and the read-only report both
  reach the refusal through `load`.

### `MAX_LESSONS_BYTES`

`MAX_LESSONS_BYTES = 1024 * 1024`, a module constant beside `LESSONS_PATH`,
with a comment carrying the measurement above. Enforced only in `load`;
`update`'s second `read_file` happens after `load` accepted the same path.

### `compare(records, treated_set, floor)`

Unchanged inputs and the unchanged line up to `descriptive,`. After the
floor check, when either pool holds zero items the tail is:

- `descriptive, no comparison: rate undefined for the treated pool (0 items)`
- `descriptive, no comparison: rate undefined for the untreated pool (0 items)`
- `descriptive, no comparison: rate undefined for both pools (0 items)`

otherwise `descriptive, treated higher` or `descriptive, treated not higher`
as today. The pool figures `0/0` stay printed in the line. Exit stays 0: a
zero-item pool is data. The `lean:` comment at the old guard goes with the
guard it described.

### Voting and pairs contracts

`pairs(records, skip=())`: `skip` holds seen keys. `votes(..., seen)`:
`seen` is the list of keys. `fold(...)` returns the sorted key list.

### The Decompose skill

`skills/decompose/SKILL.md` lines 21 and 29 say "Line 1 is a `seen`
header" and "holds only the `seen` header". Both stay true (the key is
`seen`; the file is a lessons file whose only line is that header), the
step reads lessons and not the header's contents, and the pinned phrases
at `tests/test_decompose_lessons.py` (`When the file is absent, or holds
only the \`seen\` header, ...`) are unaffected. No skill edit, so no wave
release PR is owed by this run. An old-shape file is, to the skill, a
well-formed file of lessons; only the tool refuses it.

## Stack & dependencies

- Standard library only, as the module is. No new import: the dual-membership
  pin stays 55. `decompose_lessons` stays root-only.

## Accepted behaviour changes (old rule against new rule)

Both rules run over the inputs where they differ:

1. A run with an implement boundary and review unmeasurable at fold time:
   old rule seen outright; new rule seen for `replan` and `design_gaps`
   only. Its review hit can later pair, and it can later vote on review
   lessons. This is the fix.
2. A run whose design-gaps value is unmeasurable (`Design gaps found`
   section not written yet) with an implement boundary: old seen; new not
   seen for `design_gaps` until measured. Same class, caught by the same
   rule, not reproduced separately.
3. A run with no implement boundary but a measurable review: old unseen
   (unless a hit or voter); new seen for `review`. Equivalent in effect:
   the old rule would have folded it as a hit or voter anyway whenever it
   mattered.
4. A run measured clean for a signal: old seen once complete; new seen for
   that signal at once. Same effect.
5. A review with no finding heading (`{findings: 0, reason}`): old seen
   once complete, and never a hit; new not seen for `review`, so it can
   still mature. A run that stays in this state costs one `_hit_label`
   call per update and no lesson.
6. A header of old per-run entries: old tool accepts it; new tool refuses
   it (above). No such file exists on `main`.
7. A zero-item pool: old tail `descriptive, treated not higher`; new tail
   as above. Any pool with items prints the same text as before.
8. The file's header is about 3.7x larger (1,430 to 5,336 bytes over this
   clone's 41 runs).

Unchanged by design: vote order (sequential, so up, down, down ends at 1);
early exposure (operational); the first clean run in record order is still
the exemplar.

## Decisions & alternatives

- **Per-signal key over per-run** — see Approach; the alternative (fold a
  run only when fully measured) re-derives dropped lessons from runs that
  never get a review. ADR-0116.
- **Same `seen` key, new entry form over a new key** — the skill's wording
  and pin keep holding and no skill release is owed; the cost is that a
  tool older than this change would silently misread a new header, which
  the ADR records (one checkout, root-only tool). ADR-0116.
- **Refuse the old shape over upgrading it** — an upgrade guesses; every
  mapping either reproduces the loss or resurrects dropped lessons; no file
  exists to save. ADR-0116.
- **1 MiB over 4 MiB** — the skill reads the file whole into a draft, so the
  bound protects the reader, and 1 MiB already exceeds any plausible
  ledger; one line to change later, so no ADR.
- **No-comparison tails over refusing the line** — the pool counts are
  still useful data; the line only stops claiming an order.
- **Seen = measured, one rule, over three rules (complete, hit, voter)** —
  one definition the tests can state; the old three collapse into it.
- **Not decided here:** vote order and early exposure (documented
  decisions, brief-binding).

## ADRs

- ADR-0116 (provisional): the `seen` header is one `<signal>:<run ref>`
  entry per measured (signal, run), the old shape is refused, and a size
  bound guards the read. Supersedes ADR-0113's header-shape decision in
  part (status line and index row updated). Passes the three legs: hard
  to reverse (ADR-0113 itself says a format change rewrites every line of
  an existing file and needs a superseding ADR), surprising without
  context (a reader expects one ref per run, and expects an old file to be
  upgraded, not refused), and a real trade-off (three rejected
  alternatives above). The size constant, the zero-item wording and the
  seen-equals-measured rule fail the hard-to-reverse leg: each is one line
  or one commit to change, so they keep their one-line records here.

## Traceability

| Brief item | Where |
|---|---|
| Per-signal `seen` | Seen key, Pairs, Voting, File, Fold; Data model table |
| New ADR, supersession, status and README | ADRs; ADR-0116 |
| Migration decision | Interfaces, `load`; assumptions |
| Zero-item pool | Interfaces, `compare` |
| Size bound | Interfaces, `MAX_LESSONS_BYTES` |
| Skill needs no edit, no `plugin.json` edit | Interfaces, The Decompose skill |
| Import and pin unchanged (55) | Stack & dependencies |

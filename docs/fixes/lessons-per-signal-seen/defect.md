---
stage: capture
run: maintenance:lessons-per-signal-seen
date: 2026-10-23
re-entry: architect
origin: issue #1061 (docs/features/decompose-lessons/review.md, 'Major (deferred)' and four minors), scoped by docs/fixes/lessons-per-signal-seen/autorun-brief.md
assumptions: ["re-entry: architect. The protocol (Maintenance-run orientation) sends design-touching work to Architect; the on-disk shape of the lessons file changes, and ADR-0113's Consequences section says a format change needs a new ADR that supersedes it, so this is not a scoped fix. The brief says the same. Not an Owner answer", "Intake is #1061 named by the brief (type:chore, no intake marker), so no intake: field; the issue closes from the PR (Closes #1061)", "In-flight check ran: gh pr list --state open returned [] and the only lessons branches are feat/decompose-lessons (shipped as #1050), feat/kb-weknora-lessons (unrelated) and this run's own: nothing matched", "The next free ADR number is 0116 (git ls-tree origin/main docs/adr/ ends at 0115 after a fetch, no open PR holds one); Architect re-checks at write time", "The migration question (load upgrades the old per-run shape vs refuses it) is left to Architect, which the brief requires to log it; Capture records the evidence only: no lessons file is committed on main, so no real file needs migrating", "The 'size constant' value is Architect's/Implement's; Capture records the measurement and a candidate only. Not an Owner answer"]
---

# Defect: the lessons ledger loses a signal that matures later, and says less than it knows in two places

## Defect (or Condition)

`decompose_lessons.py` (shipped #1050, ADR-0113, provisional) has one
deferred major and three minors the brief takes in. Vote order and early
exposure are documented decisions and stay.

1. **Major: `seen` is per run, so a signal that matures later is lost.**
   `update` folds every run with an implement boundary into `seen`. A
   run's review signal exists only once `review.md` is written, after
   Implement. An `update` between Implement and Review folds run R into
   `seen` with the review unmeasurable; when `review.md` lands, R's review
   hit is skipped (`pairs(skip=seen)`) and R can no longer vote on a review
   lesson (`votes` skips any `rec["run"] in seen`). Expected: seen is one
   entry per (signal, run), so a run unmeasurable for one signal still
   counts for it later. The loss is silent, an undercount never a wrong
   figure.
2. **Minor: a zero-item pool prints `0/0` as "not higher".** The rate is
   undefined; the line claims a comparison.
3. **Minor: no size bound.** `load` (and the Decompose skill) read the
   file whole. Expected: a refusal above a named size constant, a labelled
   problem, exit 1, like `eval_trends.MAX_RECORD_BYTES`.

## Reproduction / Evidence

All run 2026-10-23 on `ab8c94a`. Scratch work under
`/private/tmp/claude-501/-Users-mbutler-github-skills/9a27056e-40ad-47c2-a869-dd1e59a7bd2e/scratchpad/cap/`
(`$S/cap`); nothing written in the repo. The harness is the module's own
`update(root, run, measure=...)` with an injected `measure` returning
records built by `tests/test_decompose_lessons.py`'s `record`/`replan`
helpers, in a throwaway `git init` directory (no network, no model).

**1. Lost signal** (`python3 -I $S/cap/repro1.py`). Records H (replan hit,
gap hit), C (clean), R (clean replan, review unmeasurable at stage 1; one
review finding naming an item, `findings 2, named 1`, at stage 2). H and
C make a replan and a design-gaps pair so stage 1 writes a file at all.

```
== A: update between Implement and Review
stage1 -> ['decompose-lessons: ADD design_gaps/feature/routed', 'decompose-lessons: ADD replan/feature/added', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'] []
stage2 -> ['decompose-lessons: unchanged'] []
{"seen": ["feature:c", "feature:h", "feature:r"]}
... (2 lessons; no review/ lesson)
== B: control, first update after Review
stage2 -> ['decompose-lessons: ADD design_gaps/feature/routed', 'decompose-lessons: ADD replan/feature/added', 'decompose-lessons: ADD review/feature/named', 'decompose-lessons: wrote ...']
{"id": "review/feature/named", ... "text": "feature runs whose review findings name an item: r 1 of 2 findings (observed), h 0 of 0 findings (observed)", "sources": ["feature:h", "feature:r"], ...}
```

Same final measurements; A (R in `seen` from stage 1) yields `unchanged`
and no review lesson, B yields the review lesson. Only the update history
differs. This is the review's "reproduced in a scratch fold" run through
the real `update` path. Vote path is the same defect: `votes` filters
`rec["run"] not in seen` (decompose_lessons.py:452), so R also cannot vote
on an existing review lesson.

**2. The `0/0` line** (`python3 -I $S/cap/repro2.py`). The code is
`decompose_lessons.py:589-590`: `higher = u[1] > 0 and t[0] * u[1] > u[0] * t[1]`,
printed at `:595` as `'higher' if higher else 'not higher'`. The comment at
`:587-589` already says a zero-item untreated pool "reads 'not higher'".
Both pools reproduce at the floor of 5 treated runs:

```
treated zero-item pool (5 runs, 0 items):
decompose-lessons: re-plan treated 0/0 over 5 run(s), untreated 1/20 over 2 run(s) (observed only; 0 unmeasurable); descriptive, treated not higher
untreated zero-item pool (1 run, 0 items), treated 5/40:
decompose-lessons: re-plan treated 5/40 over 5 run(s), untreated 0/0 over 1 run(s) (observed only; 0 unmeasurable); descriptive, treated not higher
```

The second is the worse one: treated 5/40 against an undefined rate is
printed as "not higher". The existing pins are `TestCompare`
(tests/test_decompose_lessons.py:838-870), which hold no zero-item case.
Note the treated case reaches "not higher" by arithmetic (`0*u == u*0`),
the untreated one by the explicit `u[1] > 0` guard; the fix must cover
both pools.

**3. Unbounded read** (`S=$S python3 -I $S/cap/repro3.py`). `load` goes
through `cli.read_file(path, shown, str)` (decompose_lessons.py:221),
which reads the whole text; `grep -n "MAX\|size"` of the module finds no
bound and `dir(dl)` has no `MAX*` constant.

```
file bytes 3145741
peak bytes during load 6424963          # tracemalloc: whole 3 MiB text held, ~2x
result ['decompose-lessons: big.jsonl line 2: not valid JSON']
```

A 3 MiB file is read and held before any check; it is only rejected
because its content is junk. `update` additionally reads the file a
second time (`:551`), so the cost is paid twice per run. The reference
pattern is `eval_trends.py:56` `MAX_RECORD_BYTES = 4 * 1024 * 1024`
(refusal at `:338-340`).

**Size of a realistic ledger.** Five real lessons from the repro's
`update` output weighed 471 bytes for 2 lessons and 690 bytes for 3 (so
lesson lines of 204-218 bytes with 2 sources, header 49 bytes with 3
runs; an actual 5-lesson file is about 1.1 KB). The verified
decompose-lessons run measured 30 seen runs and 5 lessons with 2 to 9
sources each. A worst-case lesson line with 9 sources and typical slugs
computes to 838 bytes; five of them plus a 60-run header is about 6.6 KB
and 300 such lines about 250 KB. Candidate, not a decision: 1 MiB (about
4x a 300-line worst-case ledger and about 150x today's realistic file),
or 4 MiB to match `MAX_RECORD_BYTES`; Architect picks and states the
multiple. Note the seen header grows by (signal, run) entries after the
fix: up to three entries per run (re-plan, design gaps, review), roughly
3x today's header, still a few KB.

**Every place the `seen` shape is read or written** (grep, 2026-10-23;
`.claude/worktrees/` copies are other branches and excluded):

Code, `decompose_lessons.py`:
- :102 comment naming the line-1 shape; :122-214 `_parse` (header
  validation :205-210, error text `expected the seen header`);
  :217-224 `load` (docstring :218-219); :227-231 `serialize` (writes
  `{"seen": sorted(seen)}`); :234-253 `dump` (`not (lessons or seen)`
  :241); :446-465 `votes` (`rec["run"] not in seen` :452); :468-471 fold
  comment; :515-531 `fold` (`pairs(records, skip=set(seen))` :522,
  `folded = set(seen) | complete | hit runs | voters` :529-531, returned
  sorted); :534-566 `update` (load :538, votes :544, fold :547,
  serialize/dump :556-558); :325-350 `pairs(records, skip)` (the
  per-run skip, `hit["run"] in skip` :333).
- No other module reads it: `factory.py`, `CLAUDE.md`,
  `tests/test_dual_membership.py` mention decompose_lessons but not
  `seen`.

Tests, `tests/test_decompose_lessons.py`: :148-150 `jsonl(seen, *lessons)`
helper; :170-175 round trip; :178 `test_dump_sorts_lessons_by_id_and_seen`;
:193 header literal; :210-212 `seen of non-strings` malformed case;
:257 `expected the seen header` pin; :532-535 `cast` helper passes `seen`
to `votes`; :555-564 a seen run does not vote; :634-648 fold twice
idempotent; :657-666 voters in seen; :683-684 late hit enters seen;
:712-716; :721-726 `test_every_complete_run_is_folded_into_seen`;
:770-774 update writes seen; :783 and :956 `{"seen": []}` literals;
:1015 skill text pin ("holds only the `seen` header").

Skill text: `skills/decompose/SKILL.md:21` ("Line 1 is a `seen` header;
...") and :29 ("holds only the `seen` header"). The skill reads lines,
not the header's contents, but its words name the header, so a header
rename would put its text out of date and tests/test_decompose_lessons.py
:1015 pins that exact phrase. A skill edit means a wave release PR for
the Owner (ADR-0095); never touch `.claude-plugin/plugin.json`.

Decisions and design docs: `docs/adr/0113-...md:25` (the on-disk shape
decision, the one a superseding ADR replaces), :49 (Consequences: the
header stops dropped lessons being re-derived), :46-47 (format change
needs a superseding ADR); `docs/adr/README.md:136` (ADR-0113's row; the
superseded-by status wording is at :5-12); `docs/features/decompose-lessons/architecture.md`
:11-13 (assumptions), :127 (shape), :134 (Voter), :142 (invariant owner),
:184 (skill sentence), :216 (decision rationale), :232 (ADR ref);
`docs/features/decompose-lessons/breakdown.md` :37, :59, :65, :123 (S9/S10
log). History that quotes the old shape and stays as written: `review.md`
:8-9, :39, :57, :100, :107-126, :179-180, :220, :239; `release.md:86`;
`verification.md` :124, :212, :229, :244. `CONTEXT.md:108-109` defines
Decompose lesson and does not mention `seen`.

## Root-cause hypothesis

Hypothesis: `seen` was keyed on the run because the ledger's job was
"don't re-derive from the same runs", and S9/S10 settled that a run is
complete once it has an implement boundary (breakdown.md:123). That is
true for replan and design gaps, whose inputs exist by Implement, and
false for review, whose input exists only after `review.md`. One key for
three signals with different maturity dates is the cause; the fix the
review named is a (signal, run) key. The zero-item line and the size
bound are omissions the review already flagged, not regressions.

## Blast radius

- Who: the Owner, as the only person who runs `update`, and the Decompose
  skill's draft, which weighs lessons. Nothing else reads the file.
- How badly: the major is a silent undercount of review-signal evidence
  (fewer review lessons, fewer votes), never a wrong figure; the
  mitigation in force is to run `update` after Ship, not mid-run. The
  minors cannot bite today: replan does not produce zero-item breakdowns,
  and no lessons file exists.
- Since when: #1050, shipped 2026-10-20 (0.22.0 release is the first to
  carry the skill step). No lessons file is committed on main, so no
  existing file needs a real migration; a compatibility shim must still be
  tested.
- Downstream scale: S-M. One root-only module, its test file, a new
  provisional ADR superseding ADR-0113's on-disk-shape decision (status
  line and README row updated), possibly no skill change.

## Ruled out

- Vote order (up, down, down stays at 1; down, down, up drops it):
  sequential voting is ExpeL's own rule and the original brief's; a
  net-sum rule changes a recorded semantic. Stays a documented decision.
- Early exposure: committing the first lessons file only after 0.22.0 is
  installed is operational, not code.
- Skipping `seen` for runs without a review (a quick fix keeping the
  per-run key): not viable, since `seen` also stops dropped lessons being
  re-derived (ADR-0113 Consequences); shrinking it would resurrect them.
  Review pinned that path in ba31d36.
- Re-entering at Implement: the on-disk line-1 shape changes and ADR-0113
  says a format change needs a superseding ADR, so it is design-touching.

## Notes

- Hand-off: `architect` skill. Open design questions Capture records and
  does not answer: the per-signal entry grammar (review suggested
  `signal:run`); whether `load` upgrades old per-run entries or refuses
  them with a labelled problem (cheaper honest one, per the brief); what
  an old per-run entry means for each signal (it carried "complete"
  semantics, so upgrading it to all three signals reproduces the loss for
  review on already-folded runs); the size constant and its multiple; the
  zero-item wording (a labelled, pinned string).
- No permanent test may assert a path is "unchanged against main".
- The `update` repro writes only into mkdtemp directories under the
  scratchpad; `docs/factory/decompose-lessons.jsonl` was never written in
  this repo.

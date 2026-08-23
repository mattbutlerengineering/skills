---
stage: operate
run: maintenance:deepening-tool-seams
date: 2026-08-22
assumptions:
  - "No live user input at any point — this run is driven from autorun-brief.md, so every judgment below is mine against the brief, defect.md, CLAUDE.md and what the tree and the Actions history actually say. Nothing here was approved live."
  - "Step 4 says 'against prd.md's success criteria and idea.md's success-in-one-sentence'. This run has neither — maintenance runs skip both — so outcomes are judged against autorun-brief.md's 'Success criteria' and 'Target state' and defect.md's 'Target state that ends this run'. The protocol's maintenance-run orientation supports the substitution: it drops Idea and PRD from the run entirely."
  - "Step 3's 'let it breathe' is answered yes rather than deferred. The merge was 2026-08-19T03:35Z and this retro is written 2026-08-22 (repo clock through 2026-08-23T04:10Z UTC): four days, four scheduled gate-digest runs, two dispatched toolsmith-mine runs, three gate-latency rows written to the live ledger by the deepened walk, and four subsequent code PRs touching the same files. That is real post-ship history. What has NOT breathed is ADR confirmation and the live-failure paths, and both are named as missing rather than waited for."
  - "Criterion 1 is scored as Verify's narrowing S1 already restated it — what got one owner is the window RULE, not the seven per-tool values, which architecture.md decided stay per-tool. Read as literally written ('the seven LIST_WINDOW constants collapse to a parameter') the criterion is unmet at HEAD, and scoring it that way would grade the run against a sentence its own design stage superseded and recorded superseding."
  - "The surviving _utcnow twins and the two remaining month-string spellings are not counted as regressions. architecture.md's frontmatter recorded taking item 4 at its narrow size with the reason; they were never in the target state."
  - "ADR-0056's status is reported, not changed. Confirming a provisional ADR is the operator's act (release.md's assumption; ADR-0054's precedent, five days then and nine now). This stage records that it is still open and seeds the general condition."
  - "The three missed instances in the generalization section are attributed to the SEEDING deepening review at fbfa3c3, not to any stage of this run. review.md's Scope section bounds the run's own review to this change; hunting fresh candidates elsewhere in the tree was never its job."
  - "Signal-strength labels are mine. 'Measured' is used only where a quoted command output or run log carries the number; a single green production run is labelled anecdote even when it is green."
  - "Nothing was committed. This artifact and five appended docs/backlog.md lines are left in the working tree for the operator, alongside a sibling run's uncommitted files that this stage did not touch."
---

# Retro: one owner each, four times

Maintenance run, `re-entry: architect`, seeded by a deepening review at
`fbfa3c3` (2026-08-18), shipped as PR #302 → `60f867f` on
2026-08-19T03:35Z. This retro is written 2026-08-22 at `main` tip
`7650052`, against the tree, git history and Actions state as they are —
read-only, every command re-run here rather than carried from an earlier
artifact.

The bet was not "fix four bugs". It was: **one fact, many owners is a
recurring class in this tree, and collapsing four instances of it makes
the tree cheaper to edit.** The four instances held. The class did not
stop recurring, and the sharpest thing this retro has to say is about the
review that seeded the run rather than about the run.

## Outcomes vs. intent

### Criterion 1 — one window rule

> "Each of the four facts has exactly one owner in the tree, demonstrable
> by grep: one window rule…"

Held. Exactly one production line in the tree types a `--limit`:

```
$ grep -rn '"--limit"' --include="*.py" . | grep -v ./.claude/ | grep -v ./factory/
cli.py:353:    argv = list(args) if window is None else [*args, "--limit", str(window)]
tests/test_sweeps.py:37:             "--limit", str(sweeps.LIST_WINDOW)]
tests/test_sweeps.py:686:                "--limit", str(sweeps.LIST_WINDOW)]])
tests/test_label_sync.py:209:                 "--limit", "1000"]
tests/test_cli.py:229:                           "--limit", "100"]])
```

The four test hits are assertions about what the seam sends, which is the
right place for them. Fourteen production call sites across nine modules
go through `cli.gh_read` — `label_sync`, `assembler`, `work_queue`,
`validator`, `dashboard` (3), `sweeps` (2), `gate_digest` (2),
`rejection_mining` (3) — and `gh_json` / `full_window` have no production
callers left anywhere in the tree.

`LIST_WINDOW` is still declared seven times, unchanged in count from
`fbfa3c3`. That is the design, not a regression: each is now a per-tool
*value* passed as `window=`, and the rule that used to be retyped around
it (matching `--limit`, the failure catch, the truncation test, the label
prefix) has one owner. `work_queue`'s duplicate literal — the live
divergence the brief named — is gone, and the comment in its place says
why it cannot come back:

```
# How far back the ready listing can see. cli.gh_read owns the window —
# the limit it sends gh and the truncation it reports are the same
# number, so it can only be typed once, and the duplicate literal this
# constant used to disagree with has nowhere left to live.
LIST_WINDOW = 100
```

- Signal strength: **measured** (grep at HEAD, four days after merge).

### Criterion 2 — one gate vocabulary

Held. `human_gates.py` owns `GATES`, `gate_labels`, `label_events`,
`waited_seconds`, `completed_stays`, `gate_passages`, `gate_rejections`
and `waiting_since`. `gate_digest.py:42`, `dashboard.py:51` and
`rejection_mining.py:42` import from it; nothing imports gate vocabulary
from `gate_digest` any more. Detector J names the module instead of
slicing a tuple:

```
gates.py:769:LABEL_DECLARERS = {
gates.py:772:    "human_gates": lambda mod: mod.gate_labels(),
```

The stay partition that was written twice is one walk: `completed_stays`
returns `[(start, end, confirmed)]`, `gate_passages` keeps the confirmed
ones and `gate_rejections` keeps the rest, and
`tests/test_human_gates.py:255`
(`test_together_they_are_exactly_the_completed_stays`) executes the
invariant that used to be a prose comment.

- Signal strength: **measured**, and see the production evidence under
  criterion 6 — this is the one item that has actually run in anger.

### Criterion 3 — one `product_form`, plus the missing lockstep class

Held, both halves.

```
$ grep -rn "product_form" --include="*.py" . | grep -v ./.claude/
factory_init.py:59:def product_form(command):
…
tests/test_gates.py:18:from factory_init import product_form
tests/test_gates.py:1702,1710,1798,1820,1841,1861,1881: [product_form(c) for c in …]
```

No local rebinding survives in `tests/test_gates.py`; the line-18 import
is the only `product_form` the suite has. The `toolsmith-mine` lockstep
class exists — `TOOLSMITH_MINE_TARGET` at `tests/test_gates.py:1666`,
asserted at `:1878` (root Makefile) and `:1881` (payload Makefile, through
`product_form`).

One honest footnote, carried from `release.md` and still true: that class
pins the command *text*. Whether the target could actually run in a
stamped repo was a different defect, and it was a real one — see the
seeds section.

- Signal strength: **measured**.

### Criterion 4 — one month-to-date definition

Held in code; still latent in production.

`cost_ledger.dispatched(entries, month)` is the single row-selection
rule, and both callers use it — `cost_report.aggregate` (cost_report.py:71)
and `work_queue.month_to_date` (work_queue.py:198). Each keeps its own
arithmetic and its own cap comparison, as designed.

Recomputed against the live ledger at HEAD:

```
ledger rows: 41 problems: []
gate rows: 22 nonzero-cost gate rows: 0
work_queue.month_to_date: 0.0
cost_report.aggregate month: 0.0
naive sum incl gate rows: 0.0
```

The ledger has grown by 3 rows and 3 gate rows since `fbfa3c3` (38/19 →
41/22), and **every gate row still costs `$0.00`**. So the two figures
agree today for exactly the reason they agreed before the fix, and the
divergence remains observable only in the test fixture the run added.
This is the one criterion where the change is correct and its value is
still unfalsifiable from production data.

- Signal strength: **measured** for "they agree"; the fix's payoff is
  **latent** — no production number has changed and none will until a
  gate row costs money.

### Criterion 5 — nothing broke in four days

The full battery, re-run here at `7650052` with the working tree as it is:

```
Ran 1282 tests in 16.099s
OK

lint: 0 problem(s) across 24 skills

gates: 0 problem(s)
selftest: ok
```

1,282 tests, up from the 1,271 at the merge commit; 24 skills, up from 23
(the `automate` skill landed in #304). CI on `main` since the merge:
**34 runs, zero failures** — 27 success, 6 `assembler` jobs skipped by
design, and one with no conclusion at all: `32213104308`, the starved
validator run on `7cc5207` that `release.md` already recorded as never
leaving the queue and that `06c7108` superseded. The window covers
`validator` pushes, four scheduled `gate-digest` runs and two
`toolsmith-mine` dispatches. The only `main` failures anywhere nearby
predate the merge (`toolsmith-mine` 2026-08-17, `gate-digest`
2026-08-15).

- Signal strength: **measured**.

### Criterion 6 — is the deepened interface actually being used?

Split answer, and the honest half is the first one.

**No new code has adopted it, because no new code needed to.** Across the
23 commits since `60f867f`, the diff adds and removes *zero* lines
mentioning `gh_read`, `human_gates`, `cost_ledger.dispatched`,
`month_to_date`, `LIST_WINDOW` or `gate_labels`:

```
$ git diff 60f867f..HEAD -- '*.py' | grep -E "^[+-]" \
    | grep -E "gh_read|human_gates|cost_ledger\.dispatched|month_to_date|LIST_WINDOW|gate_labels"
(no output)
```

Four days produced four code PRs and not one new gh listing, so the
"would a new caller reach for the seam or copy a sibling?" question is
**untested**. Evidence of adoption is what the brief wanted and it does
not exist yet.

**What does exist is weak positive evidence of two other kinds.**

1. *The ritual was not re-typed through two refactors of the same files.*
   #312 (ADR-0058) and #316 (ADR-0060) rewrote `sweeps.py` heavily — it
   lost 126 lines — and both `gh_read` call sites survived untouched. A
   file being restructured is exactly where a shallow interface gets
   re-copied, and it was not.
2. *The decisions were cited and one was generalized.* ADR-0060 reasons in
   the vocabulary this run's ADR established, cites ADR-0056 by name on
   the naming question, and then **fixes the payload rule ADR-0056 got
   right for the wrong reason**. ADR-0056 said `human_gates.py` is
   "mirrored into the payload like every other shared module"; ADR-0060
   corrected that to "a module is mirrored iff a payload tool imports it,
   not because it is shared", and CLAUDE.md now carries the corrected
   form (lines 37-45). This run's module satisfies the real rule
   (`gate_digest.py` in the payload imports it), so nothing is broken —
   but the reason it gave was a coincidence generalized into a principle,
   and it took four days for something to need the principle and find it
   wrong.

**The one place the deepened code has run in anger.** The scheduled
`gate-digest` at 2026-08-20T05:47Z drove the new `human_gates` walk
against live GitHub timelines and produced a non-null result, committed
to the ledger by the run itself:

```
2026-08-20T05:48:08Z gd: 0 item(s) waiting, 3 new gate-latency row(s)
2026-08-20T05:48:08Z gate_digest: 0 problem(s)
```

```
+{"wo": "WO-0002", …, "outcome": "gate_wait:merge:3324459s", "at": "2026-08-19"}
+{"wo": "WO-0003", …, "outcome": "gate_wait:merge:3324462s", "at": "2026-08-19"}
+{"wo": "WO-0013", …, "outcome": "gate_wait:merge:3324462s", "at": "2026-08-19"}
```

That is `cli.gh_read` (issue list + timeline API), `human_gates.label_events`,
`completed_stays` and `gate_passages` all working correctly against real
data, and it closes the `gate-digest` third of `release.md`'s
carry-forward 7.

- Signal strength: **pattern** for "nothing regressed" (4 scheduled runs,
  0 problems); **measured** for the 08-20 run; **absent** for adoption by
  new callers.

### The sharp one — did the class generalize, or does it keep recurring?

It keeps recurring, and worse than that: **it was already recurring at the
commit the review was taken at, in files this run edited, and the review
did not see it.**

Two more instances were found and fixed on 2026-08-22, four days after
this run shipped. Both were in the tree at `fbfa3c3`:

| Instance | In tree since | Closed by |
|---|---|---|
| `knowledge_plane.DONE_ROW` duplicating `gates.MERGED_ROW` | 2026-08-10 (#221) | ADR-0058, #312 |
| `sweeps.reconcile_drift` vs `dashboard._drift` | 2026-08-13 (#268) | ADR-0060, #316 |
| `sweeps.issue_lifecycle` retyping `cli.label_names` | 2026-08-10 (#204) | **still open** |

The third row is new here — found while verifying the second — and it is
the most uncomfortable of the three. At `fbfa3c3`, `sweeps.py` line 63
imported `label_names` from the cli seam and used it at line 409, while
line 220 held a private retyping of the same labels-array walk. #316 then
moved that copy into `plane_drift.py` **unchanged** (ADR-0060 says so in
so many words), where both of its callers still import `cli.label_names`
and use it a few lines away:

```
sweeps.py:63:from cli import gh_read, label_names, report
sweeps.py:291:    live = set(label_names(listing))
dashboard.py:46:from cli import CLI_FAILURES, gh_read, gh_runner, label_names
dashboard.py:181,251:  … label_names(issue) …
plane_drift.py:36-39:  labels = issue.get("labels")
                        names = [entry.get("name") for entry in labels
                                 if isinstance(entry, dict)] …
```

So the count is roughly: the seeding review confirmed six candidates, this
run fixed four, and at least three more instances of the same class were
sitting in the same tree — two of which needed their own ADRs within four
days, and one of which survived a refactor whose entire purpose was
collapsing a duplicate rule.

**The fix did not generalize.** It could not: nothing in the tree detects
this class. The detector suite covers citations, checksums, staleness and
taxonomy; there is no detector for "this fact is stated twice", so the
only finder is a manual deepening review, and the measured hit rate of the
one that seeded this run is 4 of 7. A closely related symptom shows up in
the prose too: `rejection_mining._excerpt`'s docstring still says
"sanitized through sweeps' pattern" while line 43 imports `sanitize` from
`knowledge_plane` — the owner moved in #306 and the sentence naming it was
never re-read. ADR-0058 records the same shape from the other side
("gates.py gave 'only the checked form counts' as the reason for a
separate owner, and since August the knowledge plane has had a
checked-only form").

The bet that this is a real recurring class was **right**. The implied
hope that fixing four instances would slow the recurrence was **wrong**,
and there is now enough evidence to say so with dates rather than a
feeling.

- Signal strength: **measured** (git history, three dated instances, two
  closed by ADRs written four days later).

### The uncomfortable one — was the out-of-scope line true?

`autorun-brief.md` says:

> **Folding the knowledge-plane row regexes.** ADR-0037 defers this until
> a real divergence is observed. None was observed in this review.

The git history says the duplicate was there, eight days old, at the exact
commit the review was taken at:

```
$ git log -S 'DONE_ROW' --pretty='%h %ad %s' --date=short -- knowledge_plane.py
7988962 2026-08-22 refactor(factory): one owner for the checked-row grammar (#312)
4333370 2026-08-10 feat(skills): work-queue — run several ready work orders in parallel (#221)

$ git log -S 'MERGED_ROW' --pretty='%h %ad %s' --date=short -- gates.py
7988962 2026-08-22 refactor(factory): one owner for the checked-row grammar (#312)
208ffdb 2026-07-11 feat(factory): WO-0008 detectors D (blueprint-drift), G (cost-ledger), I (staleness) (#130)
```

```
$ git show fbfa3c3:knowledge_plane.py | grep -n "^DONE_ROW"
94:DONE_ROW = re.compile(r"^\s*[-*+]\s+\[x\]", re.IGNORECASE)

$ git show fbfa3c3:gates.py | grep -n "^MERGED_ROW"
106:MERGED_ROW = re.compile(r"^\s*[-*+]\s+\[x\]", re.IGNORECASE)
```

Byte-identical pattern, byte-identical flags, both present.

**The verdict, precisely.** The sentence is *literally true and
substantively misleading.* Literally: ADR-0037's deferral condition is an
observed **divergence**, and two byte-identical regexes have not diverged
— ADR-0058 later measured 0 disagreements over 924 breakdown lines plus 12
adversarial shapes. Nothing had drifted, so nothing was there to observe.
Substantively: the clause reads as "the roster was looked at and is
unchanged", and the roster had grown from three owners to four nineteen
days earlier. The review reported a fact about a roster it had not
re-counted, and `gates.py`'s own stated reason for keeping a separate
owner had already gone stale.

So: **not a scoping error, and not new drift either.** It is a
review-coverage finding, which is the more useful of the two — a scoping
error would be one run's mistake, and this is a hole in how the class is
detected at all. ADR-0058 says the same thing about itself: "Nothing said
so, because the roster had been fixed at three nineteen days earlier and
was never revisited."

- Signal strength: **measured**.

### The ADR the run produced

`docs/adr/0056-human-gates-module.md` exists and its status is
**provisional**, four days on. That is exactly what `release.md` predicted
and it is a live carry-forward — but the interesting finding is that it is
not alone:

```
0054-front-door-routes-humans.md                          provisional  (2026-08-13)
0055-deferred-stops-and-payload-charters.md               accepted     (2026-08-14)
0056-human-gates-module.md                                provisional  (2026-08-18)
0057-lifecycle-legs-agree-about-an-uncited-pr.md          provisional  (2026-08-22)
0058-checkbox-regex-roster-is-two-owners.md               provisional  (2026-08-22)
0059-restructure-is-blocked-by-nine-files.md              provisional  (2026-08-22)
0060-one-cross-plane-drift-rule.md                        provisional  (2026-08-22)
```

Six of the last seven ADRs are provisional, the oldest for nine days.
Every one of them was written by a run that correctly declined to invent
an operator confirmation, and nothing in the pipeline ever comes back to
ask. `docs/adr/` is the repo's stated home for decisions and CLAUDE.md
says to supersede rather than rewrite — but a decision nobody confirms is
citable without being settled, and the next run has to re-derive whether
it may lean on it. ADR-0060 already did that work for ADR-0056 and reached
"the noun is earned here in a way it was not for `human_gates`", which is
a fine outcome but is a second run paying to re-open a first run's
reasoning.

- Signal strength: **measured** (seven files, seven status lines).

### The release's own carry-forwards

`release.md`'s item 7 asked whoever came next to "watch one scheduled run
of `label-sync`, `gate-digest` and `toolsmith-mine` after this merge for a
nonzero exit or a changed problem line". Status:

- **`gate-digest` — closed.** Four scheduled runs (08-19, 08-20, 08-21,
  08-22), all success, one of them non-null (above).
- **`toolsmith-mine` — closed enough.** Two dispatches post-merge
  (`32219180419` 08-19T05:22Z, `32532180432` 08-21T22:15Z), both success.
  The first ran one minute after the sibling run's permissions fix merged,
  so `rejection_mining`'s `gh_read` PR listing has now succeeded against
  real GitHub.
- **`label-sync` — cannot be closed as written.** There is no
  `label-sync.yml`; `gh workflow list` returns eight workflows and none is
  it, and no Makefile target invokes `label_sync.py` either. It is the one
  factory tool with no runner at all, so its `cli.gh_read` path executes
  only when a human types the command. The watch the release asked for
  can never happen, and nobody would have noticed without going to look.
- **The live-failure path is still unproven.** Every post-merge
  observation is a *success*. That a live rate-limit or auth failure lands
  in `CLI_FAILURES` now the catch moved into `cli.gh_read` is still
  untested outside fixtures — the same words `verification.md` used, four
  days later and still true.

- Signal strength: **pattern** for the successes; **absent** for failure
  paths.

## Run retrospective

**Keep**

- **Confirming every candidate at its call sites before scoping.** All
  four items landed with no re-scoping mid-run and no "actually this isn't
  a duplicate" reversal. The brief's line-numbered evidence is the reason
  the Architect stage could argue about interface shape instead of about
  whether there was a problem.
- **Writing down the narrowings instead of softening the criteria.**
  Verify's S1/S2/A1 narrowings, carried through Ship as narrowings, are
  the reason this retro could score criterion 1 honestly rather than
  discovering the seven constants and calling it a regression.
- **The precedent-inheritance habit.** Ship read `deepening-cli-seams`'s
  closing advice and avoided both of its hiccups; it then wrote its own
  three forward, and this retro used them. That chain is working.
- **Refusing to widen.** Six of the brief's out-of-scope items are still
  out of scope and untouched; the run did not grow. Given that the class
  is everywhere, this was the difference between a shippable change and an
  unreviewable one.

**Change**

- **A deepening review needs a mechanical pre-pass.** The manual review
  found 4 of at least 7 instances of the class it was hunting, and the
  three it missed included one in a file the run edited. Grep-level
  candidates (identical module-level regex/constant bodies; a module that
  imports a seam helper and also retypes it) would have surfaced all
  three and cost minutes.
- **When an ADR states a general rule, check whether it is the rule or a
  coincidence.** ADR-0056's "mirrored like every other shared module" was
  true of the instances then existing and wrong as a principle; ADR-0060
  had to correct it four days later. The tell was available at the time —
  the rule was stated as an observation about neighbours, not as a
  mechanism.
- **Cite an owner by name in prose and something should re-check it.**
  Three separate stale-citation instances turned up while verifying this
  retro (`gates.MERGED_ROW`'s stated reason, ADR-0039's roster sentence,
  `rejection_mining._excerpt`'s "sweeps' pattern"). Prose that names an
  owner is the first thing to rot when the owner moves.
- **A carry-forward should name a mechanism that exists.** "Watch one
  scheduled run of `label-sync`" was written without checking that
  `label-sync` has no schedule.

**Stop**

- **Stop treating "no divergence observed" as evidence that a duplicate
  does not exist.** ADR-0037's deferral condition is about *drift*, and
  the brief's out-of-scope line quietly upgraded it to a claim about
  *duplication*. Two byte-identical owners are a duplicate whether or not
  they have drifted yet; the honest form is "a fourth owner exists and has
  not drifted", which is a scoping decision a reader can disagree with.
- **Stop writing provisional ADRs into a pipeline with no confirmation
  step.** Not stop writing them — the status is honest — but stop treating
  the write as the end of the transaction when six of seven are still open
  and one is nine days old.

## Idea seeds

Appended to `docs/backlog.md`:

- A duplicate-owner detector, with this run's measured miss rate as the
  case for it.
- The still-open instance: `plane_drift.issue_lifecycle` retyping
  `cli.label_names`.
- Provisional ADRs are never revisited — six of the last seven are open.
- `label_sync.py` has no runner, so one of the four changed gh-read paths
  cannot be observed in production.
- A resolution note on this run's own stamped-payload seed, which #306
  closed.

## Run complete

Closed 2026-08-22, at `main` tip `7650052`, four days after the merge.
The four facts each still have one owner, the battery is green, CI has not
gone red once, and the deepened gate walk has produced correct output
against live GitHub. The run did what it said it would.

What it did not do — and could not have, on its own — is make the next
instance less likely. Three more were already in the tree when the review
that seeded this run was taken, two of them needed their own ADRs within
four days, and one is still open. The seeds above are the input to the
next Idea-stage run, and the first of them is the one that matters.

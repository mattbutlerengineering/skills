---
stage: operate
run: maintenance:one-fact-one-owner
date: 2026-08-23
assumptions:
  - "Written pre-release, at the operator's direction. The skill's 'let it breathe' step offers to come back once there is real usage; there is none and there cannot be yet — origin/main is still 7650052, local main is ca77b4c with 17 unmerged commits, no PR and no issue exist, and the daily improvement routine has never run one_owner.py (the playbook on origin/main matches neither `one_owner` nor `one-owner`). Every outcome below is therefore labelled MEASURED and never OBSERVED IN USE, and the run's central question is recorded as UNANSWERED rather than scored."
  - "Signal vocabulary. The template offers anecdote | pattern | measured, none of which separates 'measured under test' from 'observed in use'. Each outcome carries the template's label plus an explicit usage state, and the two are never merged into one word."
  - "No live user input at any point — this run is driven from autorun-brief.md. Every judgment here is mine, taken against the run's own artifacts, CLAUDE.md and the cited ADRs. A call the operator disagrees with is a line to correct, not a design change."
  - "Where two artifacts disagree about a count, the artifact that logged the findings wins. review.md carries eight findings, two 'Decision: fix before Ship' and six 'Decision: deferred', so release.md's pre-flight line reading 'nine are deferred with logged reasons' is scored here as an overcount — and carried into the retrospective as a finding rather than quietly corrected."
  - "Adjudication depth is carried forward exactly as each stage labelled it and is never re-adjudicated here: two of the eight true findings were adjudicated at full depth by Review, two spot-checked by Verify, four read only as tool output. The seeds say which is which."
  - "No tracker artifact, no eval write, no LEDGER change, no cost-ledger row. defect.md rules out tracker interaction; this run touches no eval definition; evals/results/ and docs/factory/costs.jsonl are append-only surfaces with their own writers."
---

# Retro: a pre-pass that asks whether a fact is stated twice

**This is a pre-release retro, and the distinction is the whole point of
reading it.** The work is prepared and stopped: `release.md` records the
branch, the PR body, the merge step and a three-stage rollback plan, and
executes none of them. Nothing has been merged, nobody has used the tool,
and the trigger that was supposed to make it habitual — step 9 of the
improvement routine's Orient section — exists only in this working tree.

So this retro can say with evidence what the tool **does**, and cannot yet
say anything about what it is **worth**. Those two claims are kept apart
below on purpose.

## Outcomes vs. intent

There is no `prd.md` (maintenance runs skip it) and no `idea.md`. The
criteria are `defect.md`'s, and its success-in-one-sentence is: *"The run
ends when a mechanical check exists, runs from a documented command, finds
the one live instance unaided, and stays silent on the recorded deliberate
duplicates."*

### Something mechanical now answers "is this fact stated twice?"

- What happened: `one_owner.py` exists (443 lines, five public interfaces,
  61 test cases across 975 lines), runs from `python3 one_owner.py` and
  from `python3 factory.py one-owner`, prints nine `one-owner:`-prefixed
  problem strings at HEAD through `cli.report`, and exits 1. It is
  deliberately outside `make check` and outside every workflow, so a
  finding can never colour main red.
- Signal strength: **measured** — `verification.md` scores 20 criteria at
  19 PASS, 1 PASS-AS-AMENDED, 0 FAIL, with the battery quoted verbatim,
  and `release.md` re-ran the battery at `ca77b4c` rather than inheriting
  it (`Ran 1344 tests … OK`, `lint: 0 problem(s) across 24 skills`,
  `gates: 0 problem(s)`, `selftest: ok`).
- Usage state: **not observed in use.** Nothing is merged. No human has
  read its output except the stages of this run.

### It finds the live instance unaided

- What happened: the pass prints
  `one-owner: cli.py:376 label_names and plane_drift.py:31 issue_lifecycle
  read the same payload keys (labels, name) — one fact, one owner`, and
  `grep -n -e label_names -e issue_lifecycle -e plane_drift -e 'cli\.py'
  one_owner.py` returns nothing. The tool was not told about the fixture,
  and the fixture was deliberately left unfixed so there would be
  something live to prove it against.
- Signal strength: **measured**, and it is the single strongest result in
  the run — the acceptance criterion was designed to be unfakeable and it
  held under Review's independent re-derivation.
- Usage state: measured on **one** instance in **one** tree. That the tool
  finds a known duplicate is proven; that it finds the *next* one is not.

### It stays silent on the recorded deliberate duplicates

- What happened: `protocol._CHECKBOX` versus `knowledge_plane.ROW` — the
  canonical deliberate pair — is silent with **no carve-out involved**,
  because the two patterns and their flags genuinely differ and the
  identity rule is exact. The one recorded exception, the `runner('git')`
  group, is annotated at all three definitions, each marker naming another
  member and citing ADR-0061, and the group is silent as a result.
- Signal strength: **measured**, with the scope of the claim stated as
  Verify stated it: "false positive" here means "a pair the repo has
  already decided". Of the nine remaining findings, one is the fixture and
  eight are true and undecided — two adjudicated at full depth by Review
  (`budget_guard.record` versus `cost_ledger.row_key`, and the
  `READY_LABEL` triple), two spot-checked by Verify, four read only as
  tool output.
- Usage state: **not observed in use.** Precision under a *changing* tree —
  the property that decides whether a pre-pass gets read or ignored — has
  had one day and one tree of evidence.

### A test that would have caught each of the three historical instances — AMENDED

- What happened: the suite catches misses 1 and 3 against fixture trees
  and **pins miss 2 as a known miss**. Architect measured that no cheap
  syntactic rule reaches a re-implementation (`sweeps.reconcile_drift` at
  7 statements over 69 lines versus `dashboard._drift` at 3 over 21,
  sharing no identical text), built two candidate rules and rejected both
  on evidence, and surfaced the gap instead of redefining the criterion.
  The operator amended the criterion mid-run; the amendment is recorded in
  `architecture.md`, in `breakdown.md` C2 and in the assertion's own
  comment, whose failure message says that a finding there would be
  **welcome**.
- Signal strength: **measured against the amended criterion**; the
  criterion as originally written is **not met**, and this retro does not
  soften that. Two of three.
- Usage state: not applicable — this is a property of the suite, and the
  suite runs in CI from the moment the change merges.

### The carve-out mechanism has a real user and pays rent in both directions

- What happened: ADR-0061 (provisional) records that a carve-out lives at
  the definition site, that its reason is required, that its citation must
  resolve, and that silence is a property of the whole *group* — every
  member marked and every member named by another's marker — so a new
  owner cannot admit itself. Three live markers close a cycle
  (`budget_guard` → `dashboard` → `one_owner` → `budget_guard`), and
  Review walked deletion, rename and binding-removal of each member and
  found the surviving files speak up every time.
- Signal strength: **measured on day one**, by fixture and by hand on the
  live tree.
- Usage state: **not observed over time**, which is the only timescale the
  claim is about. ADR-0039's roster was correct on 2026-07-22 and stale by
  2026-08-22; this mechanism's whole argument is that it cannot rot
  quietly. Nineteen days is the benchmark it has to beat, and it has had
  none.

### The central question of the run: UNANSWERED

`defect.md`'s condition is not that duplicates get created — every
instance in its evidence table was a competent change with a local
reason — it is that **nothing re-reads the tree after a fold**, so the
class recurs. Whether a pre-pass actually stops that recurrence is not
knowable from anything in this run's evidence, and this retro records it
as open rather than as a win or a loss.

**What would settle it, concretely:**

1. The change merges, and the routine's §2 step 9 runs daily from `main`
   (today that step does not exist there).
2. A **new** duplicate — one created after the merge — appears in
   `one_owner.py`'s output, is named in a routine report or a
   `docs/backlog.md` proposal **within days of the commit that created
   it**, rather than surfacing weeks later in a manual deepening review or
   an emergency ADR. That is the target `defect.md` set: "in days rather
   than at the next manual review."
3. The inverse settles it too. A new duplicate of the *re-implementation*
   shape (the `reconcile_drift` / `_drift` miss the suite pins) would land
   unseen, because no cheap syntactic rule reaches it — the pass would
   have narrowed the class rather than closed it.
4. A third outcome is the one `defect.md` names as how this dies: the
   eight true findings sit unadjudicated, the pass keeps printing nine
   problems every morning, and people stop reading it. The seeds below
   exist so that outcome is visible rather than silent.

Until at least (1) and one of (2)/(3) have happened, the honest score is:
**the tool behaves as specified; nobody knows yet whether it prevents
anything.**

## Run retrospective

### The stage walk

**Capture** — cheap and high-yield. It wrote `re-entry: architect` and
deliberately no inline breakdown, then re-verified every hash, date, PR
number and line number in the brief against HEAD and issued three
corrections. One of them mattered a lot: the brief's "detector letters
A–L are all in use, so M is next" was simply false (`J` and `K` read
`unused` in the `DETECTORS` roster), and the brief's own `J`-roster
observation turned out to be a live instance of this run's class already
owned by a mid-flight work order — so Capture ruled it out of scope
instead of letting Architect widen into it. Its scanning-hazard note
(three stale agent worktrees holding `MERGED_ROW` definitions the tracked
tree deleted, hidden only by a *local, uncommitted* `.git/info/exclude`)
went straight into the design as the git-derived universe rule.

**Architect** — the stage the run existed for, and it answered the design
question with measurement rather than taste. A throwaway feasibility probe
was run at HEAD and at `fbfa3c3`, so the two-key floor comes from the
fixture, the structural floor (no bare numeric/boolean/`None`) beat a
character threshold on measured evidence, whole-function-body comparison
was built and produced **zero** groups, and a seam-call fingerprint was
built and rejected because it fires hardest on the seam being adopted
correctly. It also surfaced the one criterion it could not meet instead of
quietly restating it. Two things it got wrong were caught downstream, both
because it measured the tree *before* the tool existed: the `runner('git')`
group is a triple, not a pair, and "touches no checksum" was true of the
tool and false of the change.

**Decompose** — the stage that earned the most. It **routed a design gap
back to Architect** rather than absorbing it: the design's day-one
annotation lands in `budget_guard.py`, which is a `factory_init.MIRRORS`
entry with a byte-identical payload twin, so the architecture's "touches
no checksum" was contradicted by its own first example, and the marker
would ship into every stamped repo citing an ADR that repo does not have.
It named three real alternatives and refused to pick one. The operator
answered it — markers in mirrored files are fine, and ADR-0061 states
*why* as a rule so the next annotation does not re-open it — and two fully
root-only alternative groups (`Path(__file__).resolve().parent` and the
`expected,id,kind,query` pair) were measured and rejected, because
annotating either would have decided a duplicate the run had put out of
scope. Decompose also **absorbed** two mechanical gaps with the deriving
authority named for each: `factory.py`'s verb row (forced, because
`tests/test_factory_cli.py` derives `VERBS` from a scan for
`if __name__ == "__main__":`) and the `runner('git')` triple (forced,
because `ast.unparse` identity makes the tool's own binding a member).
Both were lookups, not decisions — and it said so.

**Implement** — thirteen items, all checked, thirteen for thirteen with no
item reopened. The test-ordering rule was served inside each item and
recorded in the commit bodies, which the breakdown argued for up front
rather than after the fact. Eight deviations were logged, none
design-level, including two that show the discipline holding: the line
count (443, past the "200-400 typical" band, analysed as 36% docstring and
198 code lines rather than defended) and an adjacent smell in `CLAUDE.md`
logged and **not** fixed. This is also where the one real process failure
happened — see below.

**Verify** — 20 criteria, 19 PASS + 1 PASS-AS-AMENDED + 0 FAIL, the
battery quoted verbatim, and a seven-entry "Not verified" list that names
what it did **not** do, including "the eight remaining findings were not
each independently re-adjudicated" and "`update-manifest` was not re-run,
because running it would write to the working tree". It scored the amended
criterion as amended and reconciled the nine live findings against the
architecture's pre-registered ten, explaining both moved line numbers as
the three-line marker blocks.

**Review** — 0 criticals, 2 majors, 6 minors; 2 fixed before Ship, 6
deferred with reasons. It re-derived rather than re-read: four throwaway
fixture trees for boundaries the suite does not reach, two of the eight
findings adjudicated by reading the sources, a docstring-to-code ratio
measured across all 28 root modules, and the run's three tripwires
re-confirmed (`plane_drift.py` absent from the diff, `gates.py` absent
entirely, nothing imports `one_owner`). Both fix-before-Ship items were
documentation defects in this run's own new material, and both were fixed
(`881787b`, `58db94a`).

**Ship** — prepared and stopped, and pre-flighted considerably further
than "prepare and stop" required. It synthesized a `$GITHUB_EVENT_PATH`
payload of the real shape, drove `gates.check_pr_traceability` against the
literal PR body with two working controls (removing the `Closes` line and
replacing the waiver each produce the expected failure), then ran the
whole suite with that payload present — and still filed the result as a
**prediction**, naming three reasons CI can differ (the real payload is
GitHub's, `#<N>` must be a real open issue, and two other jobs read live
tracker state). It also closed Verify's `update-manifest` gap read-only by
recomputing both write steps in memory (0 differing keys, 0 drifted
mirrors, no byte written), stamped a scratch product repo from the
payload, and recorded the two things it could not prove (detector B in CI,
and branch protection, which this repo's plan will not let `gh` read).

### Keep

- **Routing a design gap back instead of absorbing it.** Decompose's gap 1
  was a genuine choice with three real alternatives and a shipped-payload
  consequence; absorbing it would have put a marker into every stamped
  repo with no recorded reason. Routing it cost one exchange and produced
  a rule in ADR-0061 that the next annotation will not have to re-argue.
  The contrast is instructive: gaps 2 and 3 were absorbed in the same
  artifact, each with its deriving authority named, so "route it back" did
  not become a reflex.
- **Measuring before committing to a design.** Every threshold in this
  tool came out of a throwaway probe: the two-key floor is derived from
  the acceptance fixture, the structural floor beat a tunable number, and
  two candidate rules were built and rejected on evidence rather than on
  taste. Nothing in the tool is a knob nobody can argue about.
- **Surfacing an unmeetable criterion instead of redefining it.** Miss 2
  was named as unreachable, the operator amended the criterion, and the
  amendment now lives in three places a future reader will hit — including
  the assertion's own comment, which says a finding there would be
  welcome. A quietly reworded success criterion would have been invisible
  in a month.

### Change

- **Re-derive a count, or cite the artifact that owns it — never restate
  it.** ADR-0061 shipped saying its first annotation was a
  `budget_guard` / `dashboard` **pair** while the tree carried three
  markers. The breakdown had already caught the triple as design gap 3,
  in the same run, hours earlier; the ADR text was written from the
  architecture's pre-tool measurement and nothing re-read it. Review
  caught it and it was fixed in `58db94a`. It generalizes, because it
  happened twice: `release.md`'s pre-flight says "nine are deferred with
  logged reasons" where `review.md` logs six — and its own parenthetical
  ("one major … five minors") adds to six. Both are downstream documents
  restating an upstream number instead of citing it.
- **Say what a claim's scope is when the claim is about files.** "Touches
  no checksum" was true of `one_owner.py` and false of the change, and it
  survived into the architecture because nobody asked which files the
  design's own day-one example touched. The fix is not more prose; it is
  attaching the scope to the sentence ("the tool touches no checksum; its
  first annotation touches exactly one") — which is precisely how the
  operator's resolution ended up phrasing it.

### Stop

- **Stop restating the same success criteria verbatim in every artifact.**
  `defect.md`'s seven criteria are re-typed nearly word-for-word in the
  brief, the architecture's traceability table, the breakdown's notes and
  the verification's scoring. Measured rather than estimated, for the
  reason directly above: 208KB of run artifacts (the seven written before
  this one) around 443 lines of tool and 975 lines of test. Depth paid for
  itself exactly where the decisions were hard — the design question,
  gap 1, the amended criterion — and bought nothing where it was
  mechanical copying, which is also the surface the stale-count failure
  above happened on.

## Idea seeds

Appended to `docs/backlog.md` as `(from: maintenance:one-fact-one-owner)`.
Nothing was rewritten, reordered or deleted there; the fixture's own seed
was already present and was not duplicated.

- The carve-out's single escape hatch costs an ADR, and the pressure is
  already visible in the three day-one markers.
- `budget_guard.record` inline-retyping `cost_ledger.row_key`'s ADR-0041
  dedup identity — the sharpest of the pass's own findings.
- The `wo:ready-for-agent` triple: a third owner of a dispatch label with
  no recorded decision behind it.
- The six remaining day-one findings, named group by group, with each
  one's adjudication depth stated.
- The pass's universe rule is applied once and skipped twice (git-quoted
  paths; `_adr_ids` globbing the filesystem).
- Two marker diagnostics that tell the author something false (a
  decorated definition; a counterpart that states no fact).
- `tests/**` is out of the universe and the run's own suite is the first
  thing that costs.
- **Preventive:** nothing asks "does this fact already have an owner?"
  anywhere near the change that creates a second one — the pass finds
  duplicates after they land, and Review reads only its own run's diff.
- A number measured at one stage gets copied forward and nothing
  re-derives it.
- Nobody has measured whether a pre-pass prevents recurrence, and this
  names what would settle it.

## Run complete

Closed 2026-08-23. The run's artifacts are complete and this file
completes them; the **release is not** — `release.md` is a prepared plan
the operator executes, and step 6 (the merge) is a human step under
ADR-0036 clause 3 regardless of who runs the rest. Nothing here created an
issue, a PR, a label or a tag, and no eval, LEDGER or cost-ledger surface
was touched.

The seeds above are the input to the next Idea-stage run. Two of them are
the ones to read first: the preventive seed, because it is the only one
that addresses why the class recurs at all, and the recurrence-measurement
seed, because until it is answered this run's central claim is a design
argument with a green test suite behind it and nothing else.

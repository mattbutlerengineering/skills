---
stage: architect
run: maintenance:one-fact-one-owner
date: 2026-08-23
assumptions:
  - "No ux: echo — the protocol's echo carries a ux-reason FROM prd.md, and a maintenance run has no prd.md, so no ux: decision was ever taken and there is nothing to echo. Recorded here rather than left blank so the absence is not ambiguous downstream; defect.md states the same fact under Constraints (\"User-facing surface: none\")"
  - "prd.md absent by protocol, not by omission — this is a maintenance run whose predecessor is defect.md. defect.md plus autorun-brief.md are the design source; no PRD requirement tracing applies. Where the two disagree, defect.md wins (its three Corrections), and this artifact follows it"
  - "Tool name and problem label: neither input names either. The tool is `one_owner.py` and its problem strings are prefixed `one-owner: ` — CLAUDE.md's bar is stated as 'one fact, one owner' and the run slug is one-fact-one-owner, so the tool takes the repo's own words. Its report summary is `one-owner: N problem(s)` through cli.report"
  - "The file universe excludes tests/**. Neither input decides it; measured, including tests takes the finding count from 10 to 23 at HEAD, and a test that asserts an exact string IS the pin for that string rather than a second owner of it. Recorded as a deferred widening, not a closed question"
  - "The ADR offered below is numbered 0061 — the next free number (docs/adr/ holds 0032 through 0060, and no artifact cites 0061 yet). The number is written without its typed-ID prefix on purpose: an ADR- token for a file that does not exist is a dangling reference to detector C, and this run must leave the battery green. No file is written; the number is a proposal"
  - "The trigger includes one added step in docs/factory/improvement-routine.md §2. The brief lists candidate homes but names no trigger, and that file is tuned by PR and never by the routine itself (CLAUDE.md), so a PR edit is sanctioned. If the operator would rather not touch the routine, the design still works with the documented on-demand command alone — the trigger degrades, the tool does not"
  - "The documented command is recorded in CLAUDE.md beside the existing on-demand tools rather than in a new doc. Neither input says where 'a documented command' is documented; CLAUDE.md already carries the Verify battery and the on-demand list, so a reader looking for how to run something looks there first"
  - "Day-one findings that are neither the fixture nor a recorded decision are true findings, not false positives, and are NOT folded by this run (defect.md's out-of-scope list forbids widening). This artifact enumerates all eight so the classification is on the record; routing them to docs/backlog.md is the run's closing act, not a design element"
---

# Architecture: a pre-pass that asks whether a fact is stated twice

## Approach

The condition is not that duplicates get created — every instance in
`defect.md`'s evidence table was created by a competent change with a
local reason. The condition is that **nothing re-reads the tree after a
fold**, so the only finder the class has is a human doing it by hand, at
4-of-7. The design therefore adds one thing: a read-only pass over the
repo's own Python modules that groups *fact sites* by identity and prints
every identity owned by more than one module, as label-prefixed problem
strings. It is deliberately syntactic and deliberately shallow — it
answers "is this stated twice?", never "do these two things mean the same
thing?" — because the second question is the one that costs more to
maintain than the manual review it replaces (`defect.md`'s hazard 2).

The shape that lost is the obvious one: **a `gates.py` detector**. It
loses on a fact this run cannot design around — the acceptance fixture
must stay in the tree. `defect.md` puts `plane_drift.issue_lifecycle`
out of scope precisely so the tool has something live to prove itself
against, so a detector wired into `CHECKERS` would turn `make check` red
on the fixture on the day it lands and stay red until a *different* run
fixes it. Going green would mean either carving out the fixture — which
contradicts "the tool must find it without being told about it
specifically" — or folding it, which is out of scope. A CI detector and a
retained live fixture are mutually exclusive, and the fixture is the
success criterion. Two further costs land on the same side: `gates.py`
is mirrored into every stamped product repo (`factory_init.MIRRORS`), so
a detector would impose this repo's seam convention on product source
that never agreed to it — and in a stamped repo the pristine
`factory/templates/**` and the installed `tools/factory/**` are
byte-identical mirrors of each other, a wall of duplicates by design.

So the check is a **standalone root tool, run on demand and by the daily
routine, outside `make check`**. That is the bar `defect.md` names for it
("a pre-pass carries a much lower bar because a human reads its output")
and the bar its day-one output actually needs: measured below, at HEAD it
prints ten findings, one of which is the fixture, one of which is a
recorded ADR-0037 decision, and eight of which are genuine undecided
pairs. A queue of eight true-but-undecided findings is a good first
morning for a review pre-pass and a catastrophe for a CI gate.

Detector letter `K` stays unclaimed, `DETECTORS` gains no row, and
`WO-0039`'s mid-flight target is untouched.

## The design question: where the carve-out lives, and what stops it going stale

`defect.md` names this as Architect's to answer and forbids skipping it.
The answer has two halves, and the second is the one that matters.

**Where it lives: at the definition site, in the comment block
immediately above the definition, never in a roster.** The grammar is one
line:

```
# one-owner: <module>.<name> (ADR-####) — <reason>
```

The repo has already run the experiment. ADR-0039 fixed the
checkbox-regex roster at three owners *in prose, in an ADR, three files
away from every regex it enumerated*. Nineteen days later
`knowledge_plane.DONE_ROW` arrived as a fourth, byte-identical to
`gates.MERGED_ROW`, and nothing re-read the roster — ADR-0058 exists to
record that. The one part of that roster that stayed correct is the part
that lived **in the tree, at the definition**: the cross-references at
`knowledge_plane.py:69-77` and `protocol.py:57-60`, which both still say
the right thing today. Locality is not a preference here; it is the only
form of the statement that survived. A carve-out at the definition site
travels with the code, dies with the code, and is read by the person
reviewing the diff that would otherwise add a second owner.

**What stops it going stale: it is re-derived against the tree on every
run, and checked in both directions.**

1. **Under-coverage is caught by the tool's own finding.** A carve-out
   cannot silently absorb a newcomer, because silence is a property of
   the whole group, not of one marker: a group is silent only when
   **every member carries a marker, and every member is named by some
   other member's marker.** A third owner arriving is unmarked and
   unnamed, so the group speaks up. This is exactly the ADR-0039 shape,
   and it is the reason the rule is stated over the group rather than
   per-pair: **a new owner cannot admit itself.** Admitting it means
   editing an existing owner's file, where a reviewer is already looking.

2. **Over-coverage is caught by making the marker pay rent.** Every
   marker must match a duplicate the check actually finds this run. A
   marker whose counterpart was deleted, renamed, or folded matches
   nothing and is reported as stale, by file and line. A carve-out list
   that nothing re-checks is the failure this run exists to fix; this one
   cannot rot quietly, because dead entries are findings.

3. **The citation must resolve.** `ADR-####` must resolve to a file in
   `docs/adr/`. Status liveness is deliberately *not* checked — see
   *Decisions & alternatives*.

4. **A bare marker waives nothing.** The reason clause is required and
   must be non-empty. This is not a new invention: `gates.py`'s
   `NO_WO_DECLARATION` already applies the identical rule to the other
   place this repo lets a change excuse itself ("the declaration owes a
   reason, so a bare marker waives nothing").

The canonical deliberate pair — `protocol._CHECKBOX` versus
`knowledge_plane.ROW` — needs **no** carve-out at HEAD, and the honest
reason is worth stating rather than claiming credit for: their patterns
and flags genuinely differ (`ROW` requires trailing whitespace and no
flags; `_CHECKBOX` captures the box contents under `re.MULTILINE`), and
neither reads payload keys, so neither rule ever groups them. Success
criterion "stays silent on `protocol._CHECKBOX` versus
`knowledge_plane.ROW`" is met by the identity rule being exact, not by
the carve-out. The carve-out's day-one customer is a different pair:
`budget_guard.git_runner` and `dashboard.git_runner`, both `runner('git')`
— which ADR-0037 explicitly sanctions ("Callers alias to their own names
… so their problem strings read unchanged"). That is the first annotation
this design writes, and it is the proof the mechanism has a real user
rather than a hypothetical one.

## Measured against the tree

Every number below comes from a throwaway feasibility probe run against
real trees during this stage — **not** the implementation, which
Implement writes test-first. The probe exists so no threshold in this
design is a guess.

Against **HEAD `7650052`**, 27 modules after exclusions, 10 findings:

```
[same-value] 'CONTINUE'                       budget_guard.py:55 CONTINUE, cost_report.py:44 CONTINUE
[same-value] 'wo:ready-for-agent'             assembler.py:54 READY_LABEL, validator.py:79 READY_LABEL, work_queue.py:39 READY_LABEL
[same-value] ('issue','list','--state',...)   gate_digest.py:91 LIST_ARGS, rejection_mining.py:54 ISSUE_ARGS
[same-value] Path(__file__).resolve().parent  charter_replay.py:49 ROOT, trigger_eval.py:42 ROOT
[same-value] runner('git')                    budget_guard.py:111 git_runner, dashboard.py:61 git_runner
[same-keys ] body,number,state                dashboard.py:195 _pr_by_issue, gate_digest.py:187 run_daily, rejection_mining.py:192 run_mine
[same-keys ] color,description,name           label_sync.py:69 plan, label_sync.py:115 sync, sweeps.py:269 ensure_labels
[same-keys ] expected,id,kind,query           eval_schema.py:182 validate, trigger_eval.py:303 score_case
[same-keys ] labels,name                      cli.py:376 label_names, plane_drift.py:31 issue_lifecycle
[same-keys ] run_id,wo                        budget_guard.py:164 record, cost_ledger.py:126 row_key
```

**The acceptance fixture is line nine, found without being told about
it.** No rule in this design mentions `label_names`, `issue_lifecycle`,
`cli`, or `plane_drift`.

Against **`fbfa3c3`** — the exact 25-module tree the manual deepening
review read and missed 3 of 7 in — 11 findings, including two of the
three misses:

```
[same-value] re.compile('^\s*[-*+]\s+\[x\]', re.IGNORECASE)
                                              gates.py:106 MERGED_ROW, knowledge_plane.py:94 DONE_ROW      <- miss 1
[same-keys ] labels,name                      cli.py:349 label_names, sweeps.py:220 issue_lifecycle        <- miss 3
```

Miss 2 — `sweeps.reconcile_drift` versus `dashboard._drift` — is **not**
found, and no cheap syntactic rule finds it. Measured: at `fbfa3c3` the
two functions are 7 statements over 69 lines and 3 statements over 21,
sharing no identical text and a *narrower* rule on one side. Two
candidate rules were built and both lost on evidence — see *Decisions &
alternatives*. This is the one success criterion the design does not
meet as written, and it is surfaced rather than papered over:
`defect.md` asks for "a test that would have caught each of the three
historical instances". The design's honest answer is a test that catches
two and **pins the third as a known miss**, so the limit is visible in
the suite rather than forgotten — the same way
`tests/test_knowledge_plane.py:101-107` pins `gates.MERGED_ROW`'s
absence. The operator should accept or reject that substitution; it is
not Architect's to decide alone.

> **Resolved 2026-08-23 — the operator accepts the substitution.** The
> criterion is amended for this run: the suite must catch misses 1 and 3,
> and **pin miss 2 as a known miss** with the reason recorded, in the
> shape of `tests/test_knowledge_plane.py:99-107`. Decompose turns this
> into a work item with that acceptance criterion; Verify scores against
> the amended form and must say plainly that it was amended and why. The
> rejected alternative — redesigning to reach `_drift` — was declined on
> the measured evidence in *Decisions & alternatives*, not on cost.

Two thresholds fall out of the measurement rather than out of taste:

- **`same-keys` needs a floor of 2 keys, not 3.** The fixture's shared
  key set is `{labels, name}` — exactly two. A floor of 3 loses it. The
  fixture derives the threshold.
- **`same-value` needs no character threshold at all.** The floor is
  structural: a bare numeric, boolean, or `None` literal is a tuning
  knob, not a stated fact. That single rule drops the only two junk
  groups the tree produces (`100` shared by `sweeps.TITLE_LIMIT` and
  `work_queue.LIST_WINDOW`; `1000` shared by five `LIST_WINDOW`s) and
  keeps every real one, with no number to tune.

## Components

### `one_owner.py` — the tool

- **Responsibility:** answer "which facts in this repo's own Python
  modules have more than one owner, and which of those the repo has
  recorded as deliberate". One module, root-only, ~250 lines, matching
  the repo's 200-400 line norm.
- **Collaborators:** `cli.runner` (the git port) and `cli.report` (the
  problem-string epilogue) — both existing seams, imported the way every
  other root tool imports them; `knowledge_plane.repo_root` for the root.
  Nothing else. It imports no detector module, which is deliberate: a
  tool importing `gates` is the tool-to-tool coupling ADR-0058 removed.
- **Deletion test:** if it vanished, the 4-of-7 manual review is the only
  finder again. It does not forward to anything.
- **Not mirrored.** No payload tool imports it, so by ADR-0060's
  mirrored-iff-imported rule it stays root-only, joins no
  `factory_init.MIRRORS` entry, and touches no checksum. `update-manifest`
  is not required by this run *unless* the routine-doc trigger is
  declined and a Makefile target is chosen instead — see *Decisions*.
- **One self-reference hazard, stated so Implement does not hit it:** the
  tool's own module is in its own universe, and its marker grammar is a
  comment pattern. The marker must therefore be documented in the
  module's **docstring**, never in one of its comments, or the tool
  reports itself as carrying a stale carve-out.

### The `one-owner:` marker — a convention in the tree, not a module

- **Responsibility:** carry one recorded deliberate second owner, at the
  definition it excuses.
- **Collaborators:** the ADR it cites; the other members of its group.
- **Why it is not a file:** an allow-list file is a roster, and the
  roster is the thing that went stale. See *Decisions & alternatives*.

### `tests/test_one_owner.py` — the fixture suite

- **Responsibility:** pin the exact problem strings through the tool's
  public interfaces, against fixture trees reproducing the three
  historical shapes — never against the live tree, so the suite does not
  decay as the tree is cleaned (`defect.md`'s success criterion, and the
  reason the probe above is throwaway).
- **Collaborators:** an injected fake git runner, so the suite never
  shells out.

### The trigger

- **Responsibility:** make the pass happen often enough that a duplicate
  is caught in days, not at the next manual review.
- **Two parts:** a documented on-demand command (`python3 one_owner.py`),
  recorded in `CLAUDE.md` beside the existing non-CI tools; and one
  read-only step in `docs/factory/improvement-routine.md` §2 Orient,
  whose findings become report material and, when a *new* group appears,
  a `docs/backlog.md` seed proposal under Proposals.
- **Deliberately not §3 Health sweep.** §3 classifies main green or red,
  and a one-owner finding must never colour main red — that is the same
  bar the detector home failed. Orient is read-only intel, which is what
  this is.

## Data model

There is no storage, no state file, and no persistence. The tool reads
the tree at one instant and prints. Consistency requirement, stated
per-interaction as the canon asks: **none** — every comparison is within
a single read of a single working tree, so there is nothing to be
eventually consistent with. This is worth saying explicitly because the
obvious wrong turn is a baseline file of "findings we already know
about", which is a roster under another name and rots the same way.

Three values, all in-memory, all plain `namedtuple`s (the
`human_gates.Gate` / `cli.GhResult` precedent):

```
FactSite  = (kind, path, lineno, name, identity)
              kind      "same-value" | "same-keys"
              path      repo-relative posix path
              lineno    1-based, the definition's own line
              name      the module-level binding or function name
              identity  the grouping key (see below)

Marker    = (path, lineno, owner, counterpart, adr, reason)
              counterpart  "<module>.<name>" as written
              adr          "ADR-####" as written
              reason       required, non-empty

Group     = (identity, [FactSite, ...])   two or more distinct modules
```

**The two identities, and what each one claims.**

- `same-value` — a module-level `NAME = <expr>` assignment whose value is
  not a bare numeric/boolean/`None` literal. Identity is
  `ast.unparse(value)`: normalized source text, so formatting and
  line-wrapping differences do not hide a copy, and nothing but exact
  structural equality creates a group. Claim: *these two modules state
  the same value.* This is the `MERGED_ROW`/`DONE_ROW` shape.
- `same-keys` — a function definition anywhere in the module. Identity is
  the sorted set of string literals it uses as `.get("...")` arguments or
  as `[...]` subscripts, when there are at least two. Claim: *these two
  functions read the same named external shape*, which in this repo is
  what a seam owns. This is the `label_names`/`issue_lifecycle` shape,
  and the reason it works is that both walks are about the same two keys
  even though their code differs.

**Access patterns, which is what chose the shape:** exactly one — group
every fact site in the tree by identity, once, in memory, then join
markers to sites by file and line. There is no lookup by name, no
incremental update, and no query the design must serve later. That
rules out any index or cache.

**Invariant, and who owns it:** *a group is silent only if it is fully
covered.* The group owns that rule, not the marker — a marker cannot
decide the fate of a group it belongs to, which is precisely what stops
a newcomer self-admitting. The tool enforces it in one place.

## Interfaces & contracts

### `source_files(root, run=git_runner)` — the universe

- **Input:** the repo root; a `run(args)` callable (production:
  `cli.runner("git")`, tests: a fake).
- **Output:** `([(repo-relative path, source text), ...], problems)`,
  sorted by path.
- **The universe rule, stated because a naive walk is wrong here:** the
  file list comes from `git -C <root> ls-files -- '*.py'`, never from
  `Path.rglob`. Measured at HEAD: `rglob` finds 248 Python files where
  git tracks 96 — 152 of them are stale copies inside
  `.claude/worktrees/agent-*/`, three months-old full checkouts holding
  `MERGED_ROW` definitions the tracked tree deleted at `7988962`. They
  are hidden by `.git/info/exclude:11`, which is **local and
  uncommitted**, so no committed file can be relied on to hide them. A
  tool that walked the filesystem would report a duplicate that does not
  exist, on its first run, on the very symbol the class is famous for.
- **Two exclusions, each with its reason:** `factory/**` — the payload
  under `factory/templates/tools/factory/` is a deliberate byte-identical
  mirror of the root tools whose equality detector E already owns, so
  reading it would report 17 tools as duplicates of themselves, and
  `factory/evals/fixtures/**` holds intentionally broken repos.
  `tests/**` — see *assumptions*.
- **Failure modes:** git missing, not a repo, or failing →
  `CLI_FAILURES` is caught and turned into
  `one-owner: git ls-files failed: <cli.detail(err)>`, with an empty
  file list. **An empty universe is never silently clean**: the caller
  reports the problem and exits nonzero, so a broken environment can
  never read as "no duplicates". A file that cannot be decoded →
  `one-owner: <path> cannot be read: <err>`, that file skipped, the rest
  of the run unaffected.
- **Not a network interface.** `git ls-files` is a local subprocess, so
  no timeout is specified — matching `cli.runner`, which has none by
  design. Retry is trivially safe: the tool is read-only and idempotent,
  and writes nothing anywhere.

### `fact_sites(path, source)` — what one module states

- **Input:** a repo-relative path and its source text.
- **Output:** `([FactSite, ...], problems)`, in source order.
- **Failure modes:** `SyntaxError` → `one-owner: <path> cannot be parsed:
  <err>` and no sites from that module; every other module still
  contributes. Unparseable source is reported, never swallowed — a tool
  that silently skipped a module would go quiet exactly when someone
  broke the module it was watching.

### `markers(path, source)` — what one module claims is deliberate

- **Input:** the same path and source text.
- **Output:** `([Marker, ...], problems)`.
- **Contract:** a marker is a comment line matching the grammar, inside
  the contiguous comment block immediately above a fact site's own line
  (blank lines end the block). Comments are absent from the AST, so this
  is a line scan joined to `fact_sites` by line number — the one place
  the two readers of the same file meet, and the reason the join key is
  the definition's `lineno` rather than anything derived.
- **Failure modes:** a `# one-owner:` line that does not parse →
  `one-owner: <path>:<line> is not a readable one-owner marker
  (expected `# one-owner: <module>.<name> (ADR-####) — <reason>`)`. A
  marker with an empty reason →
  `one-owner: <path>:<line> marks <name> deliberate with no reason — a
  bare marker waives nothing`. A marker attached to no fact site →
  `one-owner: <path>:<line> is a one-owner marker above no definition`.
  In every case the marker silences nothing: a marker that cannot be
  read is not a permission.

### `groups(sites)` — the pure core

- **Input:** a list of `FactSite`.
- **Output:** the groups whose members span two or more distinct modules,
  sorted by identity.
- **Purity:** no filesystem, no subprocess, no clock — testable with a
  literal list, exactly the posture `plane_drift` documents for itself
  and for the same reason: two readers (the tool and its suite) must get
  the same answer from the same data.
- **Failure modes:** none. It is a total function over its input.

### `check(root, run=git_runner)` — the whole answer

- **Input:** repo root, injected runner.
- **Output:** a sorted list of `one-owner: `-prefixed problem strings.
- **Contract, in one sentence per shape:**
  - an uncovered group →
    `one-owner: <path>:<line> <name> and <path>:<line> <name> state the
    same value — one fact, one owner`, or `… read the same payload keys
    (<keys>) — one fact, one owner`, every member listed, sorted by path
    then line;
  - a member with no marker in an otherwise-marked group →
    `one-owner: <path>:<line> <name> joins a recorded deliberate group
    without a marker — a new owner cannot admit itself`;
  - a member no other member names →
    `one-owner: <path>:<line> <name> carries a marker but no other owner
    names it — an existing owner must vouch for a new one`;
  - a marker matching no group →
    `one-owner: <path>:<line> <name> is marked deliberate against
    <counterpart>, but nothing duplicates it — remove the marker`;
  - an unresolvable counterpart →
    `one-owner: <path>:<line> names <counterpart>, which is not defined
    in this repo`;
  - an unresolvable citation →
    `one-owner: <path>:<line> cites <ADR-####>, which is not in
    docs/adr/`.
- **Failure modes:** every failure above is a problem string; nothing
  raises. Determinism is part of the contract — the same tree yields
  byte-identical output in the same order, which is what lets the suite
  assert exact strings.

### `main(argv)` — the command

- **Input:** `sys.argv[1:]` (no options in this cut).
- **Output:** `cli.report("one-owner", check(repo_root()))` — prints each
  problem, prints `one-owner: N problem(s)`, returns 1 when there are
  problems and 0 otherwise.
- **Failure mode that matters most:** exiting nonzero is correct and is
  **not** wired into `make check` or any workflow. The problem-string
  contract is honoured in full; the tool simply is not a gate.

## Stack & dependencies

- **Python 3 standard library only** — `ast`, `re`, `pathlib`, `sys`.
  CLAUDE.md's hard convention; nothing here wants more.
- **`ast` over regex for fact extraction** — `ast.unparse` (3.9+, and CI
  pins 3.12) gives normalized source text for free, which is what makes
  `same-value` immune to reformatting without any comparison logic of its
  own. This is the *cheap* use of `ast`: parse, walk, read literals. It
  is not AST equivalence, not dataflow, not cross-module call analysis —
  the three things `defect.md`'s hazard 2 names.
- **`cli.runner` / `cli.report` / `knowledge_plane.repo_root`** — the
  existing seams. Cost is their interface, not their size: three names,
  each already imported by half the tools in the tree.
- **`git` as the file-universe authority** — a stable, ubiquitous
  dependency the repo already shells out to from `budget_guard.py` and
  `dashboard.py`. Behind a seam because `cli.runner` already is one, and
  because the test double is the second adapter that makes it real.
- **No new shared module.** The tool has one production caller (its own
  `main`) and no observed divergence with anything. CLAUDE.md's bar is
  two real callers **and** observed divergence; anticipated reuse does
  not qualify, and it is not close.

## Decisions & alternatives

- **A standalone on-demand tool** over **a `gates.py` detector `K`** —
  the run must keep `plane_drift.issue_lifecycle` unfixed as its live
  fixture, so a CI detector would be red from the day it lands with no
  in-scope way to go green.
- **A standalone on-demand tool** over **a `make one-owner` target** —
  the root Makefile mirrors into the product Makefile through
  `factory_init.product_makefile`, and a new root-only tool is not in
  `_PRODUCT_TOOLS`, so the target would be copied verbatim into stamped
  repos that have no such file; adding it to `_PRODUCT_TOOLS` would imply
  mirroring a tool no payload tool imports, which ADR-0060 forbids.
- **A definition-site marker** over **an allow-list file or a roster in
  the tool** — the roster is the artefact that went stale (ADR-0039 →
  ADR-0058); the in-tree cross-references at the definitions are the part
  that stayed correct.
- **A definition-site marker** over **deriving the carve-out list from
  the ADRs themselves** (parsing "What deliberately did NOT move"
  sections) — it reads the right documents and is the wrong mechanism:
  it makes prose load-bearing for a checker, and the prose is exactly
  what went stale.
- **Group-wide coverage** over **a one-sided marker excusing the pair** —
  a one-sided marker lets a third owner be absorbed into an existing
  carve-out without anyone touching the existing owner's file, which is
  the ADR-0039 failure re-implemented in the fix for it.
- **Both directions checked** over **findings-only** — a carve-out list
  nothing re-checks is the condition this run exists to fix, so dead
  markers are findings too.
- **Citation resolution only, not status liveness** — checking whether a
  cited ADR is superseded needs the status grammar, whose owner is
  `gates.ADR_STATUS`; importing a detector module from a tool is the
  tool-to-tool coupling ADR-0058 just removed, and the fold that would
  make it clean (`ADR_STATUS` into `knowledge_plane`) is its own
  decision, not a ride-along. Recorded here, deliberately deferred.
- **`same-value` + `same-keys`** over **also comparing whole function
  bodies** — built and measured: identical normalized function bodies
  yield **zero** groups at HEAD and zero at `fbfa3c3`. It is dead weight,
  not a safety net.
- **`same-value` + `same-keys`** over **a seam-call fingerprint** (group
  functions by which seam helpers they call) — built and measured at
  `fbfa3c3`: it produces 5 groups, of which the two largest are six
  `main()` functions that all call `repo_root` and `report`, and four
  that all call `repo_root`, `report`, and `write_outputs`. It fires
  hardest on the seam working exactly as designed, and it still misses
  `_drift` (the two functions' call sets are not equal). Flagging correct
  adoption is the fastest way to get a tool ignored.
- **A structural floor** (no bare numeric/boolean/`None`) over **a
  minimum-length threshold** — measured, the structural rule drops both
  junk groups and keeps every real one with no number to tune; a
  character count is a knob nobody will ever have a principled reason to
  change.
- **`tests/**` excluded from the universe** over **included** — measured,
  10 findings versus 23; a test asserting an exact string is that
  string's pin, not a second owner. Deferred, not closed.
- **Trigger in Orient (§2)** over **the Health sweep (§3)** — a
  one-owner finding must never classify main as red; that is the same bar
  that disqualified the detector home.
- **No baseline or suppressions file** over **recording day-one findings
  so the tool starts clean** — a baseline is a roster with a worse name,
  and it would silence the eight true findings this design exists to
  surface.

## What this design deliberately does not do

- It does not fix `plane_drift.issue_lifecycle`. It is the fixture
  (`defect.md`, out of scope; seeded at `docs/backlog.md:46`).
- It does not fold any of the eight other true findings it prints. They
  are enumerated above so the classification is on the record, and they
  are the pre-pass's first useful output, not this run's cleanup list.
- It does not catch a *re-implementation* — the `reconcile_drift` /
  `_drift` shape. Two candidate rules were built and lost on measured
  evidence; closing it needs semantic comparison, which is the
  over-cleverness `defect.md` names as a way this dies.
- It does not touch `DETECTORS`, detector `J`, `CHECKERS`, or any
  workflow. Letter `K` stays unclaimed.

## ADRs

**One ADR is offered — proposed text only. No file is written into
`docs/adr/`; this run is prepare-and-stop, and writing a decision record
is the operator's act.**

> **Resolved 2026-08-23 — the operator agreed to the text below and
> authorized writing it during Implement, status `provisional`.** That is
> the one file this run adds under `docs/adr/`, and it carries the two
> obligations every ADR here carries: the index row in
> `docs/adr/README.md` must match the file's status byte-for-byte, and
> the status line must satisfy `gates.ADR_STATUS`. It makes seven open
> provisionals, which the operator accepted knowingly.

The tool's *existence* does not meet the bar (easy to reverse, not
surprising, barely a trade-off) and is recorded above as one-line
decisions. The **carve-out mechanism** meets all three: it is hard to
reverse once markers are spread through the tree, it is genuinely
surprising to find a machine-read comment above a regex, and it is the
result of a trade-off the repo has already lost once.

Proposed as `docs/adr/0061-a-carve-out-lives-at-the-definition-site.md`:

```markdown
# A carve-out lives at the definition site and must pay rent

- Status: provisional
- Date: 2026-08-23

The repo's bar is one fact, one owner, and until now the only thing
enforcing it was a human reading the tree during a manual deepening
review — a finder with a measured hit rate of 4 of 7
(docs/fixes/one-fact-one-owner/defect.md). A mechanical pre-pass closes
that gap, but a checker for this class has a false-positive problem the
other detectors do not: this repo has recorded, *deliberate* duplicates,
and a tool that cries wolf on decisions already made gets disabled.

So the pre-pass needs a way to say "this pair is deliberate, and here is
the ADR". The hard part is not where to put that list; it is what stops
the list from going stale — because this repo has already watched one go
stale. ADR-0039 fixed the checkbox-regex roster at three owners, in
prose, in an ADR, three files away from every regex it named. Nineteen
days later `knowledge_plane.DONE_ROW` arrived as a fourth, byte-identical
to `gates.MERGED_ROW`; nothing re-read the roster, and ADR-0058 exists to
record that. The part of that roster that stayed correct is the part that
lived in the tree at the definitions — the cross-references at
`knowledge_plane.py:69-77` and `protocol.py:57-60`, both still accurate.

## Decision

**A deliberate second owner is annotated where it is defined**, in the
comment block immediately above the definition:

    # one-owner: <module>.<name> (ADR-####) — <reason>

**The reason is required.** A bare marker waives nothing — the same rule
`gates.NO_WO_DECLARATION` already applies to the other place a change may
excuse itself.

**The carve-out is re-derived against the tree on every run, and checked
in both directions.**

- *Under-coverage.* Silence is a property of the whole group, never of
  one marker: a group is silent only when every member carries a marker
  **and** every member is named by some other member's marker. A new
  owner therefore cannot admit itself — admitting it means editing an
  existing owner's file, where a reviewer is already looking. This is the
  precise failure ADR-0039 suffered, made impossible.
- *Over-coverage.* Every marker must match a duplicate the pass actually
  finds. A marker whose counterpart was deleted, renamed, or folded
  matches nothing and is reported as stale, by file and line. The list
  cannot rot quietly, because dead entries are findings.

**The citation must resolve** to a file in `docs/adr/`. Whether that ADR
is still live is deliberately not checked: the status grammar's owner is
`gates.ADR_STATUS`, and importing a detector module from a tool is the
coupling ADR-0058 removed. Folding `ADR_STATUS` into `knowledge_plane` is
its own decision, not a ride-along.

## Consequences

- The carve-out list has no file of its own. There is no allow-list, no
  suppressions file, and no baseline — each is a roster under another
  name, and the roster is the thing that went stale.
- Adding a deliberate second owner costs two edits, in two files, by
  construction. That is the point, not an oversight.
- Deleting a definition deletes its excuse, and moving it moves it. The
  carve-out cannot outlive the code it describes.
- The first annotation this decision writes is `budget_guard.git_runner`
  / `dashboard.git_runner`, the `runner('git')` pair ADR-0037 sanctions
  explicitly. The canonical pair — `protocol._CHECKBOX` versus
  `knowledge_plane.ROW` — needs no annotation, because the identity rule
  is exact and their patterns and flags genuinely differ.
- Status is provisional: this records a mechanism on first use, and the
  operator has confirmed nothing.
```

## Traceability

`defect.md` records no PRD (maintenance runs skip it), so the trace runs
against its Success criteria:

| `defect.md` success criterion | Where it lands |
|---|---|
| Check exists, documented command, label-prefixed problem strings | `one_owner.py` + `main` + CLAUDE.md entry |
| Finds `plane_drift.issue_lifecycle` unaided | `same-keys` identity; measured, line nine at HEAD |
| Silent on recorded deliberate duplicates | exact identity for `_CHECKBOX`/`ROW`; the marker for the rest |
| Zero false positives at HEAD, or carved out with an ADR | 1 fixture + 1 ADR-0037 carve-out + 8 true findings, all enumerated |
| A test that would have caught each of the three historical instances | **2 of 3 met; the third pinned as a known miss — surfaced, not assumed** |
| Full battery green | the tool is outside `make check`; nothing in CI changes |
| `update-manifest` if a detector or mirrored tool | not required — root-only tool, no payload importer (ADR-0060) |
| Test-ordering visible in history | Implement's to honour; the pure core exists so it can be |

No `ux:` frontmatter echo appears above, and its absence is deliberate
rather than an omission: the protocol's echo relays a `ux-reason` from
`prd.md`, maintenance runs skip PRD, and this run's brief records
"User-facing surface: none". The first `assumptions:` entry says so, which
is the only place the protocol lets it be said.

> **Resolved 2026-08-23 — the operator answered Decompose's gap 1: a marker
> in a mirrored file is fine, and the 0061 record says why.** The
> *Components → `one_owner.py`* bullet reading "joins no
> `factory_init.MIRRORS` entry, and touches no checksum" is true of the
> tool, and was read as covering the tool's first annotation too. It does
> not. The design's day-one customer is the `runner('git')` group, and
> `budget_guard.py` is a `MIRRORS` entry (`factory_init.py:142`) whose
> payload twin is byte-identical (`diff -q`, HEAD `7650052`). So `B4`
> changes a mirrored root file: `python3 factory_init.py update-manifest`
> runs in that same commit, and the regenerated twin and manifest are
> committed with it. **Amended: this run touches no checksum until its
> first annotation, which touches exactly one.**
>
> The detector-home objection does not transfer, and the 0061 record must
> say so. That objection was that a `gates.py` detector would turn a
> stamped repo's own `make check` red on product source that never agreed
> to this repo's seam convention. A `# one-owner:` marker is an inert
> comment: no stamped-repo tooling reads it — `gates._scannable_files` is
> `docs/**/*.md` plus `CONTEXT.md`, verified at HEAD, so detectors A, C and
> D never open a `.py` file — and the pass itself is root-only and ships
> nowhere. The marker costs one checksum regeneration and nothing else.
> This reasoning belongs in the 0061 record as a rule, not as a one-off,
> so the next annotation does not re-open the question.
>
> Two fully root-only groups were measured as alternatives and rejected:
> `Path(__file__).resolve().parent` (`charter_replay.py:49`,
> `trigger_eval.py:42`) and `expected,id,kind,query` (`eval_schema.py:182`,
> `trigger_eval.py:303`). Both are undecided *true findings*, so annotating
> either would decide a duplicate this run puts out of scope — trading a
> scope violation for a manifest regeneration.
